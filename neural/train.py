"""Entrena y evalúa MemeCode Neural con un dataset JSONL local."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random

from neural.model import MemeCodeGPT, ModelConfig
from neural.tokenizer import BOS, EOS, encode


def load_samples(path: Path) -> list[list[int]]:
    """Carga ejemplos independientes para evitar fugas entre train y validación."""
    samples: list[list[int]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en línea {line_number}: {exc}") from exc
            if not isinstance(item, dict) or not isinstance(item.get("prompt"), str) or not isinstance(item.get("response"), str):
                raise ValueError(f"La línea {line_number} necesita prompt y response de texto.")
            prompt, response = item["prompt"].strip(), item["response"].strip()
            if not prompt or not response:
                raise ValueError(f"Prompt y response no pueden estar vacíos (línea {line_number}).")
            sample = f"Usuario: {prompt}\nMemeCode: {response}\n"
            samples.append([BOS, *encode(sample), EOS])
    if len(samples) < 2:
        raise ValueError("Se necesitan al menos dos ejemplos para separar entrenamiento y validación.")
    return samples


def load_dataset(path: Path) -> list[int]:
    """Compatibilidad: devuelve todos los ejemplos concatenados."""
    return [token for sample in load_samples(path) for token in sample]


def split_samples(samples: list[list[int]], eval_fraction: float, seed: int):
    """Divide por ejemplos completos, nunca por fragmentos del mismo ejemplo."""
    if not 0.05 <= eval_fraction <= 0.5:
        raise ValueError("eval_fraction debe estar entre 0.05 y 0.5.")
    shuffled = list(samples)
    random.Random(seed).shuffle(shuffled)
    eval_count = max(1, int(round(len(shuffled) * eval_fraction)))
    eval_count = min(eval_count, len(shuffled) - 1)
    validation = shuffled[:eval_count]
    training = shuffled[eval_count:]
    return training, validation


def pack_samples(samples: list[list[int]]) -> torch.Tensor:
    return torch.tensor([token for sample in samples for token in sample], dtype=torch.long)


def sample_batch(data: torch.Tensor, batch_size: int, block_size: int, device: torch.device):
    if len(data) <= block_size:
        raise ValueError("No hay suficientes tokens para crear un lote; añade ejemplos o reduce block-size.")
    starts = torch.randint(0, len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in starts]).to(device)
    y = torch.stack([data[i + 1:i + block_size + 1] for i in starts]).to(device)
    return x, y


def estimate_loss(model, train_data, validation_data, batch_size, block_size, device, batches=8):
    """Calcula pérdidas medias sin actualizar los pesos."""
    import torch

    model.eval()
    results = {}
    with torch.no_grad():
        for name, data in (("train", train_data), ("validation", validation_data)):
            losses = []
            for _ in range(batches):
                x, y = sample_batch(data, batch_size, block_size, device)
                _, loss = model(x, y)
                losses.append(loss.item())
            results[name] = sum(losses) / len(losses)
    model.train()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrenar el modelo local MemeCode Neural")
    parser.add_argument("--data", default="neural/dataset/examples.jsonl")
    parser.add_argument("--output", default="neural/checkpoints/memecode-neural.pt")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--eval-fraction", type=float, default=0.15)
    parser.add_argument("--eval-interval", type=int, default=50)
    parser.add_argument("--eval-batches", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.steps < 1 or args.batch_size < 1 or args.block_size < 8:
        parser.error("steps y batch-size deben ser positivos; block-size debe ser >= 8")
    if args.eval_interval < 1 or args.eval_batches < 1:
        parser.error("eval-interval y eval-batches deben ser positivos")
    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "No se puede entrenar MemeCode Neural: PyTorch no está instalado. "
            "Las herramientas locales siguen funcionando sin esta dependencia opcional."
        ) from exc
    try:
        samples = load_samples(Path(args.data))
        train_samples, validation_samples = split_samples(samples, args.eval_fraction, args.seed)
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    train_data = pack_samples(train_samples)
    validation_data = pack_samples(validation_samples)
    if len(train_data) <= args.block_size or len(validation_data) <= args.block_size:
        raise SystemExit(
            "Train o validación no tienen suficientes tokens para block-size. "
            "Añade más ejemplos o reduce --block-size/--eval-fraction."
        )

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = ModelConfig(block_size=args.block_size)
    model = MemeCodeGPT(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    print(
        f"Dispositivo={device}; ejemplos train={len(train_samples)}; "
        f"validación={len(validation_samples)}; parámetros={sum(p.numel() for p in model.parameters()):,}"
    )

    for step in range(1, args.steps + 1):
        model.train()
        x, y = sample_batch(train_data, args.batch_size, args.block_size, device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % args.eval_interval == 0 or step == args.steps:
            metrics = estimate_loss(
                model, train_data, validation_data, args.batch_size,
                args.block_size, device, args.eval_batches
            )
            print(
                f"Paso {step}/{args.steps} | train_loss={metrics['train']:.4f} "
                f"| validation_loss={metrics['validation']:.4f}"
            )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "config": model.config_dict(),
        "state_dict": model.state_dict(),
        "step": args.steps,
        "train_examples": len(train_samples),
        "validation_examples": len(validation_samples),
        "seed": args.seed,
        "validation_loss": metrics["validation"],
    }, output)
    print(f"Modelo guardado en: {output}")
    print("La pérdida es una señal de aprendizaje, no una prueba de respuestas correctas.")
    print("Revisa resultados con ejemplos nuevos antes de usar el modelo en proyectos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Entrena MemeCode Neural desde un dataset JSONL, sin servicios externos."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import torch

from neural.model import MemeCodeGPT, ModelConfig
from neural.tokenizer import BOS, EOS, encode


def load_dataset(path: Path) -> list[int]:
    tokens: list[int] = []
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
            sample = f"Usuario: {item['prompt'].strip()}\nMemeCode: {item['response'].strip()}\n"
            tokens.extend([BOS, *encode(sample), EOS])
    if len(tokens) < 3:
        raise ValueError("El dataset está vacío o no contiene ejemplos suficientes.")
    return tokens


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrenar el modelo local MemeCode Neural")
    parser.add_argument("--data", default="neural/dataset/examples.jsonl")
    parser.add_argument("--output", default="neural/checkpoints/memecode-neural.pt")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.steps < 1 or args.batch_size < 1 or args.block_size < 8:
        parser.error("steps y batch-size deben ser positivos; block-size debe ser >= 8")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    data = torch.tensor(load_dataset(Path(args.data)), dtype=torch.long)
    if len(data) <= args.block_size:
        raise SystemExit(f"Dataset demasiado pequeño: {len(data)} tokens. Añade más ejemplos o reduce --block-size.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = ModelConfig(block_size=args.block_size)
    model = MemeCodeGPT(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    print(f"Entrenando en {device}; tokens={len(data)}; parámetros={sum(p.numel() for p in model.parameters()):,}")
    model.train()
    for step in range(1, args.steps + 1):
        starts = torch.randint(0, len(data) - args.block_size - 1, (args.batch_size,))
        x = torch.stack([data[i:i + args.block_size] for i in starts]).to(device)
        y = torch.stack([data[i + 1:i + args.block_size + 1] for i in starts]).to(device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 50 == 0 or step == args.steps:
            print(f"Paso {step}/{args.steps} | pérdida: {loss.item():.4f}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"config": model.config_dict(), "state_dict": model.state_dict(), "step": args.steps}, output)
    print(f"Modelo guardado en: {output}")
    print("Aviso: un dataset pequeño produce texto experimental; amplía y revisa los ejemplos antes de usarlo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

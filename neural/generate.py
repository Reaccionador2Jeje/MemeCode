"""Prueba una respuesta del checkpoint local de MemeCode Neural."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generar texto con MemeCode Neural")
    parser.add_argument("prompt", nargs="?", default="Hola, ¿qué puedes hacer?")
    parser.add_argument("--model", default="neural/checkpoints/memecode-neural.pt")
    parser.add_argument("--tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40, help="Limita la selección a los K tokens más probables; 0 desactiva el filtro")
    args = parser.parse_args()
    if args.tokens < 1 or args.temperature <= 0 or args.top_k < 0:
        parser.error("tokens debe ser positivo, temperature > 0 y top-k >= 0")

    path = Path(args.model)
    if not path.is_file():
        raise SystemExit(f"No existe el checkpoint: {path}. Entrena primero con python -m neural.train")

    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "No se puede generar texto: PyTorch no está instalado. "
            "Las herramientas ligeras de Neural siguen disponibles sin PyTorch."
        ) from exc

    from neural.model import MemeCodeGPT, ModelConfig
    from neural.tokenizer import BOS, EOS, encode, decode

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    model = MemeCodeGPT(ModelConfig(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    start = torch.tensor(
        [[BOS, *encode(f"Usuario: {args.prompt}\\nMemeCode:")]],
        dtype=torch.long,
        device=device,
    )
    with torch.no_grad():
        result = model.generate(
            start,
            max_new_tokens=min(args.tokens, 512),
            temperature=args.temperature,
            top_k=args.top_k or None,
            eos_token_id=EOS,
        )[0].tolist()
    generated = result[len(start[0]):]
    if EOS in generated:
        generated = generated[:generated.index(EOS)]
    print(decode(generated).strip() or "(El modelo no generó texto.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

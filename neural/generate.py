"""Prueba una respuesta del checkpoint local de MemeCode Neural."""
from __future__ import annotations

import argparse
from pathlib import Path
import torch

from neural.model import MemeCodeGPT, ModelConfig
from neural.tokenizer import BOS, EOS, encode, decode


def main() -> int:
    parser = argparse.ArgumentParser(description="Generar texto con MemeCode Neural")
    parser.add_argument("prompt", nargs="?", default="Hola, ¿qué puedes hacer?")
    parser.add_argument("--model", default="neural/checkpoints/memecode-neural.pt")
    parser.add_argument("--tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    args = parser.parse_args()
    path = Path(args.model)
    if not path.is_file():
        raise SystemExit(f"No existe el checkpoint: {path}. Entrena primero con python -m neural.train")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    model = MemeCodeGPT(ModelConfig(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    start = torch.tensor([[BOS, *encode(f"Usuario: {args.prompt}\\nMemeCode:")]], dtype=torch.long, device=device)
    result = model.generate(start, max_new_tokens=max(1, min(args.tokens, 512)), temperature=args.temperature)[0].tolist()
    generated = result[len(start[0]):]
    if EOS in generated:
        generated = generated[:generated.index(EOS)]
    print(decode(generated).strip() or "(El modelo no generó texto.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

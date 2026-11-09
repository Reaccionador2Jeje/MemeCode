"""Agente local de codificación para MemeCode Neural.

Las salidas del modelo se consideran texto no confiable: nunca se ejecutan.
Las herramientas se invocan mediante comandos explícitos del usuario.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

MAX_FILE_BYTES = 256_000
SECRET_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}


class NeuralAgentError(Exception):
    """Error controlado del agente local."""


def workspace_path(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise NeuralAgentError("Usa una ruta relativa dentro del proyecto.")
    candidate = (root / relative).resolve()
    base = root.resolve()
    if candidate != base and base not in candidate.parents:
        raise NeuralAgentError("La ruta intenta salir del workspace.")
    if any(part in SECRET_NAMES or part.endswith((".pem", ".key")) for part in Path(relative).parts):
        raise NeuralAgentError("Acceso bloqueado a archivos que podrían contener secretos.")
    return candidate


def list_project_files(root: Path, limit: int = 100) -> list[str]:
    ignored = {".git", ".venv", "__pycache__", "node_modules", ".memecode"}
    results = []
    for path in sorted(root.rglob("*")):
        if any(part in ignored for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            results.append(path.relative_to(root).as_posix())
            if len(results) >= limit:
                break
    return results


def read_project_file(root: Path, relative: str) -> str:
    path = workspace_path(root, relative)
    if not path.is_file():
        raise NeuralAgentError("El archivo no existe.")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise NeuralAgentError("Archivo demasiado grande para leerlo desde el agente.")
    return path.read_text(encoding="utf-8")


def create_project_file(root: Path, relative: str, content: str, *, approve: bool = False) -> str:
    path = workspace_path(root, relative)
    if path.exists():
        raise NeuralAgentError("El archivo ya existe; no se sobrescribirá.")
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise NeuralAgentError("El contenido supera el límite de 256 KB.")
    if not approve:
        raise NeuralAgentError("Creación cancelada: requiere confirmación explícita.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Archivo creado: {path.relative_to(root.resolve()).as_posix()}"


def run_project_tests(root: Path, *, approve: bool = False) -> str:
    if not approve:
        raise NeuralAgentError("Ejecución cancelada: requiere confirmación explícita.")
    # Lista fija, sin shell ni argumentos suministrados por el modelo/usuario.
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    try:
        result = subprocess.run(
            command, cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", timeout=60, check=False, shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NeuralAgentError(f"No se pudieron ejecutar las pruebas: {exc}") from exc
    return result.stdout[-12_000:] or f"Pruebas terminadas. Código: {result.returncode}"


class NeuralTextModel:
    """Carga el checkpoint opcional; la generación nunca activa herramientas."""
    def __init__(self, checkpoint: Path):
        self.model = None
        self.device = None
        if not checkpoint.is_file():
            return
        try:
            import torch
            from neural.model import MemeCodeGPT, ModelConfig
            from neural.tokenizer import BOS, encode, decode
            self.torch = torch
            self.BOS, self.encode, self.decode = BOS, encode, decode
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            data = torch.load(checkpoint, map_location=self.device, weights_only=True)
            self.model = MemeCodeGPT(ModelConfig(**data["config"])).to(self.device)
            self.model.load_state_dict(data["state_dict"])
            self.model.eval()
        except Exception as exc:
            raise NeuralAgentError(f"No se pudo cargar el checkpoint: {exc}") from exc

    def answer(self, prompt: str, max_tokens: int = 160) -> str:
        if self.model is None:
            return ("Todavía no hay un checkpoint entrenado. Puedo usar las herramientas "
                    "locales /ls, /read, /new y /test. Entrena primero con python -m neural.train.")
        start = self.torch.tensor(
            [[self.BOS, *self.encode(f"Usuario: {prompt}\nMemeCode:")]],
            dtype=self.torch.long, device=self.device,
        )
        with self.torch.no_grad():
            output = self.model.generate(start, max_new_tokens=max(1, min(max_tokens, 256)))[0].tolist()
        generated = output[len(start[0]):]
        return self.decode(generated).strip() or "(Neural no generó texto.)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente local de codificación MemeCode Neural")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--checkpoint", default="neural/checkpoints/memecode-neural.pt")
    parser.add_argument("--task", help="Pregunta para el modelo local")
    parser.add_argument("--list", action="store_true", help="Listar archivos")
    parser.add_argument("--read", metavar="RUTA", help="Leer un archivo")
    parser.add_argument("--new", nargs=2, metavar=("RUTA", "CONTENIDO"), help="Crear un archivo nuevo")
    parser.add_argument("--test", action="store_true", help="Ejecutar unittest discover con confirmación")
    parser.add_argument("--yes", action="store_true", help="Confirmar creación o ejecución de pruebas")
    args = parser.parse_args()
    try:
        root = Path(args.workspace).resolve()
        if not root.is_dir():
            raise NeuralAgentError("El workspace debe ser una carpeta existente.")
        if args.list:
            print("\n".join(list_project_files(root)) or "(Proyecto vacío)")
        elif args.read:
            print(read_project_file(root, args.read))
        elif args.new:
            print(create_project_file(root, args.new[0], args.new[1], approve=args.yes))
        elif args.test:
            print(run_project_tests(root, approve=args.yes))
        elif args.task:
            model = NeuralTextModel(Path(args.checkpoint))
            print(model.answer(args.task))
        else:
            parser.print_help()
        return 0
    except (NeuralAgentError, OSError, UnicodeError) as exc:
        print(f"MemeCode Neural Agent: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Diagnóstico de funciones disponibles en MemeCode Neural, sin dependencias."""
from __future__ import annotations

import importlib.util


def main() -> int:
    torch_available = importlib.util.find_spec("torch") is not None
    print("MemeCode Neural — diagnóstico")
    print("Herramientas locales: disponibles (archivos, planes y pruebas)")
    print(f"PyTorch: {'disponible' if torch_available else 'no instalado (opcional)'}")
    if torch_available:
        print("Modelo: se puede intentar entrenar o generar texto si existe un checkpoint.")
    else:
        print("Modelo: entrenamiento y generación desactivados en este entorno.")
        print("No necesitas PyTorch para usar las herramientas locales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

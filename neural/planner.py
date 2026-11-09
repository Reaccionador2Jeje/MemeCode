"""Validador y aplicador de planes JSON de MemeCode Neural.

Los planes son datos no confiables. Solo se aceptan operaciones de archivos
explícitas y rutas contenidas en el workspace. No se ejecuta código del plan.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_PLAN_OPERATIONS = 8
MAX_FILE_BYTES = 256_000
SECRET_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}
IGNORED_PATHS = {".git", ".memecode", ".venv", "__pycache__", "node_modules"}


class PlanError(ValueError):
    """El plan no cumple el formato o las reglas de seguridad."""


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise PlanError("Cada ruta debe ser relativa al workspace.")
    if any(part in IGNORED_PATHS for part in Path(relative).parts):
        raise PlanError("La ruta apunta a una carpeta protegida.")
    if any(part in SECRET_NAMES or part.endswith((".pem", ".key")) for part in Path(relative).parts):
        raise PlanError("La ruta apunta a un posible archivo secreto.")
    base = root.resolve()
    candidate = (base / relative).resolve()
    if candidate != base and base not in candidate.parents:
        raise PlanError("La ruta intenta salir del workspace.")
    return candidate


def parse_plan(raw: str) -> dict[str, Any]:
    try:
        plan = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PlanError("El plan no es JSON válido. No se aplicó ningún cambio.") from exc
    if not isinstance(plan, dict) or set(plan) - {"version", "summary", "operations"}:
        raise PlanError("El plan contiene campos no permitidos.")
    if plan.get("version") != 1:
        raise PlanError("Versión de plan no compatible; se requiere version: 1.")
    if not isinstance(plan.get("summary"), str) or not plan["summary"].strip():
        raise PlanError("El plan necesita un resumen.")
    operations = plan.get("operations")
    if not isinstance(operations, list) or not 1 <= len(operations) <= MAX_PLAN_OPERATIONS:
        raise PlanError(f"El plan debe incluir entre 1 y {MAX_PLAN_OPERATIONS} operaciones.")
    seen: set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) - {"action", "path", "content"}:
            raise PlanError("Operación con campos desconocidos.")
        action = operation.get("action")
        if action not in {"create_file", "replace_file"}:
            raise PlanError("Acción no permitida. Solo create_file y replace_file.")
        path = operation.get("path")
        if not isinstance(path, str) or path in seen:
            raise PlanError("Ruta inválida o repetida dentro del plan.")
        seen.add(path)
        content = operation.get("content")
        if not isinstance(content, str):
            raise PlanError("El contenido de cada archivo debe ser texto.")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise PlanError("Un archivo supera el límite de 256 KB.")
    return plan


def preview_plan(root: Path, plan: dict[str, Any]) -> list[str]:
    preview = []
    for operation in plan["operations"]:
        path = safe_path(root, operation["path"])
        exists = path.exists()
        action = operation["action"]
        if action == "create_file" and exists:
            raise PlanError(f"No se sobrescribirá el archivo existente: {operation['path']}")
        if action == "replace_file" and not exists:
            raise PlanError(f"No se puede reemplazar un archivo inexistente: {operation['path']}")
        if exists and not path.is_file():
            raise PlanError(f"La ruta no es un archivo: {operation['path']}")
        preview.append(f"{action}: {operation['path']} ({'existe' if exists else 'nuevo'})")
    return preview


def apply_plan(root: Path, plan: dict[str, Any], *, approve: bool = False) -> list[str]:
    preview = preview_plan(root, plan)
    if not approve:
        raise PlanError("Aplicación cancelada: revisa el plan y confirma con --yes.")
    base = root.resolve()
    backup_root = (base / ".memecode" / "backups").resolve()
    if base not in backup_root.parents:
        raise PlanError("La carpeta de copias de seguridad no es segura.")
    changes: list[tuple[Path, bytes | None]] = []
    backup_files: list[tuple[Path, bytes]] = []
    try:
        # Revalidar todo antes de escribir, luego guardar copias de los archivos reemplazados.
        for operation in plan["operations"]:
            path = safe_path(base, operation["path"])
            previous = path.read_bytes() if path.exists() else None
            changes.append((path, previous))
            if previous is not None:
                backup_path = (backup_root / operation["path"]).resolve()
                if base not in backup_path.parents:
                    raise PlanError("La ruta de respaldo no es segura.")
                if backup_path.exists():
                    raise PlanError(f"Ya existe una copia de seguridad: {operation['path']}")
                backup_files.append((backup_path, previous))
        for backup_path, previous in backup_files:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_bytes(previous)
        for operation, (path, _) in zip(plan["operations"], changes):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(operation["content"], encoding="utf-8")
    except Exception:
        # Restaurar lo que ya se alcanzó a modificar.
        for path, previous in reversed(changes):
            try:
                if previous is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(previous)
            except OSError:
                pass
        raise
    return [f"Aplicado: {line}" for line in preview]

#!/usr/bin/env python3
"""MemeCode host bridge: workspace-scoped files and approval-gated commands."""
from __future__ import annotations
import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence

MAX_READ_BYTES = 256_000
MAX_OUTPUT_CHARS = 20_000
DEFAULT_TIMEOUT = 30
BLOCKED_EXECUTABLES = {
    "sudo", "su", "doas", "rm", "rmdir", "mkfs", "dd", "shutdown",
    "reboot", "poweroff", "passwd", "useradd", "userdel", "mount",
    "umount", "iptables", "nft",
}
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa",
                "id_ed25519", "credentials.json", "secrets.json"}

class WorkspaceError(Exception):
    """An operation attempted to leave the approved workspace."""

def workspace_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise WorkspaceError(f"Workspace is not a directory: {root}")
    return root

def safe_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise WorkspaceError("Absolute paths and parent traversal are not allowed.")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise WorkspaceError("Path escapes the workspace.") from exc
    return resolved

def is_secret(path: Path) -> bool:
    return path.name.lower() in SECRET_NAMES or path.name.lower().startswith(".env.")

def list_files(root: Path, relative: str) -> list[str]:
    directory = safe_path(root, relative)
    if not directory.is_dir():
        raise WorkspaceError("Requested path is not a directory.")
    result = []
    for item in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
        if is_secret(item):
            continue
        try:
            item.resolve().relative_to(root)
        except ValueError:
            continue
        result.append(("[dir] " if item.is_dir() else "[file] ") + item.name)
    return result

def read_file(root: Path, relative: str) -> str:
    path = safe_path(root, relative)
    if is_secret(path):
        raise WorkspaceError("Reading secret/configuration files is blocked.")
    if not path.is_file():
        raise WorkspaceError("File does not exist.")
    data = path.read_bytes()
    if len(data) > MAX_READ_BYTES:
        raise WorkspaceError(f"File exceeds the {MAX_READ_BYTES}-byte read limit.")
    return data.decode("utf-8")

def write_file(root: Path, relative: str, content: str) -> None:
    path = safe_path(root, relative)
    if is_secret(path):
        raise WorkspaceError("Writing secret/configuration files is blocked.")
    if len(content.encode("utf-8")) > MAX_READ_BYTES:
        raise WorkspaceError("File exceeds the write size limit.")
    if path.exists() and path.is_symlink():
        raise WorkspaceError("Writing through symlinks is blocked.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def filtered_environment() -> dict[str, str]:
    """Keep common runtime variables but drop credential-like environment keys."""
    allowed = {"PATH", "HOME", "PREFIX", "TMPDIR", "LANG", "LC_ALL", "TERM",
               "ANDROID_ROOT", "ANDROID_DATA", "SHELL"}
    blocked_words = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH")
    return {
        key: value for key, value in os.environ.items()
        if key in allowed and not any(word in key.upper() for word in blocked_words)
    }

def run_command(root: Path, argv: Sequence[str], timeout: int) -> int:
    if not argv:
        raise WorkspaceError("Provide a command after --.")
    executable = Path(argv[0]).name.lower()
    if executable in BLOCKED_EXECUTABLES:
        raise WorkspaceError(f"Command '{executable}' is blocked by default.")
    if any("\x00" in part for part in argv):
        raise WorkspaceError("NUL bytes are not allowed in command arguments.")
    print("Command to execute:\n$ " + shlex.join(argv))
    print(f"Working directory: {root}")
    if input("Approve this command? [y/N] ").strip().lower() not in {"y", "yes"}:
        print("Cancelled.")
        return 2
    try:
        result = subprocess.run(
            list(argv), cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", timeout=max(1, min(timeout, 120)),
            check=False, shell=False, env={**filtered_environment(), "PWD": str(root)}
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        print(str(output)[-MAX_OUTPUT_CHARS:])
        print(f"Command timed out after {timeout} seconds.")
        return 124
    print(result.stdout[-MAX_OUTPUT_CHARS:])
    print(f"Exit code: {result.returncode}")
    return result.returncode

def main() -> int:
    parser = argparse.ArgumentParser(description="MemeCode safe workspace bridge")
    parser.add_argument("--workspace", default=".", help="Approved project directory")
    sub = parser.add_subparsers(dest="action", required=True)
    listing = sub.add_parser("list", help="List workspace entries")
    listing.add_argument("path", nargs="?", default=".")
    reader = sub.add_parser("read", help="Read a text file")
    reader.add_argument("path")
    writer = sub.add_parser("write", help="Write a text file")
    writer.add_argument("path")
    writer.add_argument("--content", required=True)
    runner = sub.add_parser("run", help="Run an approved command")
    runner.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    runner.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        root = workspace_root(args.workspace)
        if args.action == "list":
            print(json.dumps(list_files(root, args.path), ensure_ascii=False, indent=2))
            return 0
        if args.action == "read":
            print(read_file(root, args.path))
            return 0
        if args.action == "write":
            write_file(root, args.path, args.content)
            print(f"Written: {args.path}")
            return 0
        if args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            return run_command(root, command, args.timeout)
    except (WorkspaceError, OSError, UnicodeError) as exc:
        print(f"MemeCode error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

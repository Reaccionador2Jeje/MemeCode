#!/data/data/com.termux/files/usr/bin/bash
# MemeCode one-command installer for Termux and Linux.
set -eu

REPO="https://github.com/Reaccionador2Jeje/MemeCode.git"
MEMINGO_REPO="https://github.com/Reaccionador2Jeje/Memingo.git"
MEMINGO_BRANCH="feat/arch-aur-packaging"
APP_DIR="${MEMECODE_HOME:-$HOME/.local/share/memecode}"
BIN_DIR="${PREFIX:+$PREFIX/bin}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
ACTION="${1:-install}"

say() { printf '\n[MemeCode] %s\n' "$*"; }
fail() { say "ERROR: $*"; exit 1; }

case "$ACTION" in
  install|update) ;;
  uninstall)
    if [ -d "$APP_DIR" ]; then
      printf '¿Desinstalar MemeCode de %s? [y/N] ' "$APP_DIR"
      read -r answer
      case "$answer" in y|Y|yes|YES) rm -rf "$APP_DIR" ;; *) say "Cancelado."; exit 0 ;; esac
    fi
    rm -f "$BIN_DIR/memecode"
    say "MemeCode desinstalado. Tus proyectos y claves externas no se modificaron."
    exit 0
    ;;
  *) fail "Uso: install.sh [install|update|uninstall]" ;;
esac

command -v git >/dev/null 2>&1 || fail "Falta Git. En Termux: pkg install git"
PYTHON="$(command -v python3 || command -v python || true)"
[ -n "$PYTHON" ] || fail "Falta Python 3. En Termux: pkg install python"
command -v curl >/dev/null 2>&1 || fail "Falta curl. En Termux: pkg install curl"

mkdir -p "$(dirname "$APP_DIR")" "$BIN_DIR"
if [ -d "$APP_DIR/.git" ]; then
  say "Actualizando repositorio MemeCode..."
  git -C "$APP_DIR" pull --ff-only origin main || fail "No se pudo actualizar. Revisa tus cambios locales con git -C '$APP_DIR' status."
elif [ -e "$APP_DIR" ]; then
  fail "$APP_DIR existe pero no es un repositorio Git. Muévelo o define MEMECODE_HOME."
else
  say "Descargando MemeCode..."
  git clone --depth 1 "$REPO" "$APP_DIR"
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM
say "Descargando el runtime Memingo..."
git clone --depth 1 --branch "$MEMINGO_BRANCH" "$MEMINGO_REPO" "$TMP_DIR/Memingo" || fail "No se pudo descargar Memingo."
say "Preparando entorno Python aislado..."
"$PYTHON" -m venv "$APP_DIR/.venv" || fail "No se pudo crear el entorno virtual. Comprueba que Python incluya venv."
"$APP_DIR/.venv/bin/python" -m pip install "$TMP_DIR/Memingo" || fail "No se pudo instalar Memingo."
"$APP_DIR/.venv/bin/python" -m py_compile "$APP_DIR/runtime/agent.py" "$APP_DIR/runtime/host_bridge.py" || fail "Falló la comprobación de Python."
"$APP_DIR/.venv/bin/python" -m memingo --help >/dev/null 2>&1 || "$APP_DIR/.venv/bin/memingo" --help >/dev/null 2>&1 || fail "Memingo no quedó disponible."

cat > "$BIN_DIR/memecode" <<'LAUNCHER'
#!/bin/sh
set -eu
APP_DIR="${MEMECODE_HOME:-$HOME/.local/share/memecode}"
PY="$APP_DIR/.venv/bin/python"
AGENT="$APP_DIR/runtime/agent.py"
if [ ! -x "$PY" ] || [ ! -f "$AGENT" ]; then
  echo "MemeCode no está instalado. Ejecuta el instalador oficial." >&2
  exit 1
fi
case "${1:-}" in
  doctor)
    echo "MemeCode: instalación encontrada"
    "$PY" --version
    "$APP_DIR/.venv/bin/memingo" --help >/dev/null 2>&1 && echo "Memingo: OK" || echo "Memingo: revisar"
    "$PY" -m py_compile "$AGENT" "$APP_DIR/runtime/host_bridge.py" && echo "Python: OK"
    if [ -n "${MEMECODE_API_KEY:-}" ]; then echo "API: clave presente en esta sesión"; else echo "API: falta MEMECODE_API_KEY (no compartas tu clave)"; fi
    ;;
  update)
    exec sh "$APP_DIR/install.sh" update
    ;;
  uninstall)
    exec sh "$APP_DIR/install.sh" uninstall
    ;;
  help|-h|--help)
    echo "Uso: memecode [doctor|update|uninstall|--chat|tarea...]"
    echo "Sin argumentos: abre el chat en la carpeta actual."
    echo "Ejemplo: memecode --workspace . 'Revisa este proyecto'"
    ;;
  "")
    exec "$PY" "$AGENT" --workspace . --chat
    ;;
  *)
    exec "$PY" "$AGENT" "$@"
    ;;
esac
LAUNCHER
chmod +x "$BIN_DIR/memecode"
cp "$APP_DIR/install.sh" "$APP_DIR/install.sh.tmp" 2>/dev/null || true
say "¡Instalación completada!"
say "Ejecuta: memecode"
case ":$PATH:" in *":$BIN_DIR:"*) ;; *) say "Añade $BIN_DIR a PATH para ejecutar memecode desde cualquier carpeta." ;; esac
say "Comprueba la instalación con: memecode doctor"

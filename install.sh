#!/data/data/com.termux/files/usr/bin/bash
# MemeCode one-command installer for Termux and Linux.
set -eu

REPO="https://github.com/Reaccionador2Jeje/MemeCode.git"
MEMINGO_REPO="https://github.com/Reaccionador2Jeje/Memingo.git"
MEMINGO_BRANCH="feat/arch-aur-packaging"
APP_DIR="${MEMECODE_HOME:-$HOME/.local/share/memecode}"
if [ -n "${TERMUX_VERSION:-}" ] && [ -n "${PREFIX:-}" ] && [ -d "$PREFIX/bin" ]; then
  BIN_DIR="$PREFIX/bin"
else
  BIN_DIR="$HOME/.local/bin"
fi
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
    rm -f "$BIN_DIR/memecode" "$BIN_DIR/memecode-neural"
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
"$APP_DIR/.venv/bin/python" -m pip install --upgrade "$TMP_DIR/Memingo" "textual>=0.80,<2" || fail "No se pudieron instalar Memingo y la TUI."
"$APP_DIR/.venv/bin/python" -m py_compile "$APP_DIR/runtime/agent.py" "$APP_DIR/runtime/host_bridge.py" "$APP_DIR/runtime/tui.py" "$APP_DIR/neural/agent.py" "$APP_DIR/neural/planner.py" || fail "Falló la comprobación de Python."
"$APP_DIR/.venv/bin/python" -m memingo --help >/dev/null 2>&1 || "$APP_DIR/.venv/bin/memingo" --help >/dev/null 2>&1 || fail "Memingo no quedó disponible."

say "La configuración del proveedor es opcional. Puedes configurarla después desde la TUI con /setup o mediante: memecode setup"

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
    "$PY" -m py_compile "$AGENT" "$APP_DIR/runtime/host_bridge.py" "$APP_DIR/runtime/tui.py" "$APP_DIR/neural/agent.py" "$APP_DIR/neural/planner.py" && echo "Python + TUI + Neural: OK"
    if [ -n "${MEMECODE_API_KEY:-}" ]; then echo "API: clave presente en esta sesión"; else echo "API: falta MEMECODE_API_KEY (no compartas tu clave)"; fi
    ;;
  setup)
    exec "$PY" "$AGENT" --setup
    ;;
  neural)
    shift
    export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"
    exec "$PY" -m neural.agent --workspace "$PWD" "$@"
    ;;
  update)
    exec sh "$APP_DIR/install.sh" update
    ;;
  uninstall)
    exec sh "$APP_DIR/install.sh" uninstall
    ;;
  help|-h|--help)
    echo "Uso: memecode [setup|doctor|neural|update|uninstall|--chat|tarea...]"
    echo "Sin argumentos: abre la TUI en la carpeta actual."
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

cat > "$BIN_DIR/memecode-neural" <<'NEURAL_LAUNCHER'
#!/bin/sh
set -eu
APP_DIR="${MEMECODE_HOME:-$HOME/.local/share/memecode}"
PY="$APP_DIR/.venv/bin/python"
if [ ! -x "$PY" ] || [ ! -f "$APP_DIR/neural/agent.py" ]; then
  echo "MemeCode Neural no está instalado. Ejecuta el instalador oficial." >&2
  exit 1
fi
export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m neural.agent --workspace "$PWD" "$@"
NEURAL_LAUNCHER
chmod +x "$BIN_DIR/memecode-neural"
curl -fsSL "https://raw.githubusercontent.com/Reaccionador2Jeje/MemeCode/main/install.sh" -o "$APP_DIR/install.sh"
say "¡Instalación completada!"
say "Ejecuta: memecode"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    if [ "$BIN_DIR" = "$HOME/.local/bin" ]; then
      for profile in "$HOME/.profile" "$HOME/.bashrc"; do
        touch "$profile"
        grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$profile" || printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$profile"
      done
      PATH="$BIN_DIR:$PATH"
      export PATH
      say "Se añadió $BIN_DIR al PATH de las próximas sesiones."
    else
      say "Añade $BIN_DIR a PATH para ejecutar memecode desde cualquier carpeta."
    fi
    ;;
esac
say "Comprueba la instalación con: memecode doctor"

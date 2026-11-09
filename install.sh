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
"$APP_DIR/.venv/bin/python" -m pip install --upgrade "$TMP_DIR/Memingo" || fail "No se pudo instalar Memingo."
"$APP_DIR/.venv/bin/python" -m py_compile "$APP_DIR/runtime/agent.py" "$APP_DIR/runtime/host_bridge.py" || fail "Falló la comprobación de Python."
"$APP_DIR/.venv/bin/python" -m memingo --help >/dev/null 2>&1 || "$APP_DIR/.venv/bin/memingo" --help >/dev/null 2>&1 || fail "Memingo no quedó disponible."

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/memecode"
CONFIG_FILE="$CONFIG_DIR/.env"
CURRENT_MODEL="gpt-4o-mini"
if [ -f "$CONFIG_FILE" ]; then
  CURRENT_MODEL="$("$APP_DIR/.venv/bin/python" -c 'import re,sys; s=open(sys.argv[1],encoding="utf-8").read(); m=re.search(r"^MEMECODE_MODEL=[\"\\x27]?(.*?)[\"\\x27]?$",s,re.M); print(m.group(1) if m else "gpt-4o-mini")' "$CONFIG_FILE" 2>/dev/null || printf 'gpt-4o-mini')"
  [ -n "$CURRENT_MODEL" ] || CURRENT_MODEL="gpt-4o-mini"
fi
say "Configuración del modelo"
# El instalador suele ejecutarse con curl | sh: stdin es el pipe del script.
# Lee las respuestas desde la terminal real para que el prompt no termine en EOF.
[ -r /dev/tty ] || fail "No se detectó una terminal interactiva. Ejecuta el instalador desde una terminal."
printf 'Modelo de IA [actual: %s]: ' "$CURRENT_MODEL" > /dev/tty
IFS= read -r SELECTED_MODEL < /dev/tty
SELECTED_MODEL="${SELECTED_MODEL:-$CURRENT_MODEL}"
case "$SELECTED_MODEL" in *[!a-zA-Z0-9._:/+-]*|'') fail "Nombre de modelo inválido. No uses espacios." ;; esac
say "Abre la página oficial para crear tu API key:"
printf '%s\n' "https://platform.openai.com/api-keys"
if command -v termux-open-url >/dev/null 2>&1; then
  termux-open-url "https://platform.openai.com/api-keys" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "https://platform.openai.com/api-keys" >/dev/null 2>&1 || true
fi
say "Crea y copia tu API key. Después pégala aquí; la entrada estará oculta."
"$APP_DIR/.venv/bin/python" - "$CONFIG_FILE" "$SELECTED_MODEL" <<'PY'
import getpass, json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
values = {"MEMECODE_API_KEY": "", "MEMECODE_MODEL": "gpt-4o-mini", "MEMECODE_BASE_URL": "https://api.openai.com/v1"}
if path.is_file():
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            if key in values:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                values[key] = value
values["MEMECODE_MODEL"] = sys.argv[2]
key = getpass.getpass("Pega MEMECODE_API_KEY (entrada oculta): ").strip()
if key:
    values["MEMECODE_API_KEY"] = key
else:
    print("No se introdujo una key; podrás configurarla después con: memecode setup")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("# MemeCode private provider configuration. Do not share or commit.\n" + "".join(f"{k}={json.dumps(v)}\n" for k, v in values.items()), encoding="utf-8")
os.chmod(path, 0o600)
print("Configuración guardada en:", path)
PY

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
case ":$PATH:" in *":$BIN_DIR:"*) ;; *) say "Añade $BIN_DIR a PATH para ejecutar memecode desde cualquier carpeta." ;; esac
say "Comprueba la instalación con: memecode doctor"

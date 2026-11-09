# MemeCode

**An open-source coding-agent project built around Memingo.**

MemeCode is an early open-source coding agent. Its identity, workflow, capabilities, and safety policy are defined in Memingo (`.mgo`); a small Python adapter connects that core to an OpenAI-compatible model API and local workspace tools.

## Project status

**Status:** Early development — MVP foundation

- [x] Memingo policy core and Python host bridge
- [x] Workspace-confined file operations and approval-gated edits
- [x] Approval-gated command execution
- [x] OpenAI-compatible tool-calling agent loop
- [x] Bounded review/repair, interactive chat, and opt-in task history
- [x] Read-only Git and public GitHub inspection
- [x] Approval-gated local branch creation and commits (no push)
- [x] One-command installers for Termux, Linux, macOS, and Windows

## Install

### Android / Termux

```sh
pkg update
pkg install git python curl
curl -fsSL https://raw.githubusercontent.com/Reaccionador2Jeje/MemeCode/main/install.sh | sh
```

### Linux

Install Git, Python 3 with venv support, and curl, then run:

```sh
curl -fsSL https://raw.githubusercontent.com/Reaccionador2Jeje/MemeCode/main/install.sh | sh
```

### macOS

Install Git, Python 3, and curl. Homebrew users can run:

```sh
brew install git python
```

Then run:

```sh
curl -fsSL https://raw.githubusercontent.com/Reaccionador2Jeje/MemeCode/main/install.sh | sh
```

The macOS/Linux installer places the command in `~/.local/bin`. If the installer says that directory is not on PATH, add it to your shell profile (zsh is the default on current macOS):

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Windows 10 / 11 (PowerShell)

Install Git for Windows and Python 3 first. During Python setup, enable **Add Python to PATH**. Open PowerShell and run:

```powershell
$installer = Join-Path $env:TEMP "memecode-install.ps1"
Invoke-WebRequest "https://raw.githubusercontent.com/Reaccionador2Jeje/MemeCode/main/install.ps1" -OutFile $installer
powershell -NoProfile -ExecutionPolicy Bypass -File $installer
```

The installer creates a private Python environment and adds MemeCode's command folder to your user PATH. Open a new terminal after installation if `memecode` is not found immediately.

All installers download MemeCode and Memingo, create an isolated Python environment, and install Memingo automatically. You do not need to clone or install Memingo separately.

## Run

From the folder you want MemeCode to work in:

```sh
cd /path/to/your/project
memecode
```

On Windows, use `cd C:\path\to\your\project` in PowerShell.

Useful commands on all platforms:

```text
memecode
memecode doctor
memecode update
memecode uninstall
memecode "Inspect this project and explain its structure"
```

Set a compatible provider key in your current terminal session.

macOS / Linux / Termux:
```sh
export MEMECODE_API_KEY='your-api-key'
export MEMECODE_MODEL='gpt-4o-mini'
```

Windows PowerShell:
```powershell
$env:MEMECODE_API_KEY = "your-api-key"
$env:MEMECODE_MODEL = "gpt-4o-mini"
```

API use may cost money depending on the provider. Keep keys private and review provider pricing before use.

## Architecture

- `src/main.mgo` and `src/agent_core.mgo`: Memingo entry point and policy.
- `runtime/host_bridge.py`: workspace-scoped file and command bridge.
- `runtime/agent.py`: model adapter, tool loop, approvals, Git/GitHub tools, review cycle, chat, and history.
- `install.sh`: Termux, Linux, and macOS installer.
- `install.ps1`: Windows PowerShell installer.
- `docs/TERMUX.md`: Android installation guide.

## Safety

File edits display a diff and require approval. Commands require approval. Git commits and branch creation require approval and remain local; MemeCode does not push. The command bridge is **not an OS sandbox**: approved programs still run with your user permissions. Only use it in projects you trust.

## License

Apache License 2.0. See [LICENSE](LICENSE).

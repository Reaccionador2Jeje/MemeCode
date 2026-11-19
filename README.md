# MemeCode

**An open-source coding-agent project built around Memingo.**

MemeCode 2.0 begins a staged migration to a `.mgo`-first core. The new `src/memecode_core.mgo` provides dependency-free, read-only workspace commands without Python imports, PyTorch, or an AI provider. The existing Python agent remains available during migration because the current Memingo v0.2 interpreter itself is Python-based; a fully native runtime is a separate future project.

## Project status

**Status:** Early development — MVP foundation

- [x] Memingo policy core and Python host bridge (legacy path)
- [x] Memingo 2.0 read-only core preview (`src/memecode_core.mgo`)
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
memecode neural --help
memecode-neural --list
memecode update
memecode uninstall
memecode "Inspect this project and explain its structure"
```

## Optional API setup

MemeCode opens its terminal UI without requiring a model or API key. The provider configuration is optional during installation and first launch. In the TUI, use `/setup` to configure a provider, or run this command from a regular terminal:

```sh
memecode setup
```

The TUI also works before a provider is configured; you can browse its interface and set up the provider later. Use `/test` inside the TUI to verify the API key, model ID, endpoint, and a real text response before asking the agent to edit a project.

MemeCode detects three API protocols from the base URL:
- **OpenAI-compatible Chat Completions** (OpenAI, OpenRouter, Groq, Together, DeepSeek and compatible gateways): use the provider's API root, usually ending in `/v1`.
- **Anthropic Messages API**: use `https://api.anthropic.com/v1`.
- **Google Gemini generateContent API**: use `https://generativelanguage.googleapis.com/v1beta`.

Use the exact model ID shown by the provider dashboard. MemeCode retries compatible request formats when a model rejects optional temperature or tool-calling parameters. If a model only supports text generation, it falls back to text-only mode and clearly warns that no project files or commands were executed. See [docs/PROVIDERS.md](docs/PROVIDERS.md) for setup examples and troubleshooting.

The configuration uses these exact variable names:

```dotenv
MEMECODE_API_KEY="your-real-api-key"
MEMECODE_MODEL="gpt-4o-mini"
MEMECODE_BASE_URL="https://api.openai.com/v1"
```

The private file is stored outside your project: `%APPDATA%\\MemeCode\\.env` on Windows, or `$XDG_CONFIG_HOME/memecode/.env` (default: `~/.config/memecode/.env`) on Termux, Linux, and macOS. On Unix-like systems its permissions are restricted to the current user. Environment variables with the same names override the file.

Installers do not ask for a model or API key. The model and key are requested only when you explicitly open `/setup` in the TUI or run `memecode setup`. The root `.env.example` is only a template. Never put a real key in a repository, share it, or commit `.env`. API use may cost money depending on the provider; check its pricing and model availability.

## Experimental local model: MemeCode Neural

The repository now includes an independent, experimental character/byte-level Transformer written in Python with PyTorch. It trains locally from JSONL prompt/response examples and does not call a model API.

Install the optional training dependency in an isolated environment:

```sh
python -m pip install -r requirements-neural.txt
```

Train the starter model:

```sh
python -m neural.train --steps 500
```

Generate a sample:

```sh
python -m neural.generate "¿Qué es Memingo?"
```

Add reviewed examples to `neural/dataset/examples.jsonl`, one JSON object per line with `prompt` and `response` string fields. Checkpoints are written under `neural/checkpoints/` and should remain local.

**Important status:** this is a research prototype with a tiny starter dataset. Its answers will be weak until it is trained on a much larger, carefully reviewed corpus. PyTorch is an optional dependency and may not be readily installable on Android/Termux. The regular `memecode` command continues to use its provider adapter. Neural is available separately through `memecode neural` or `memecode-neural`; it does not call a hosted provider. The Neural launcher is installed automatically, but PyTorch and a trained checkpoint are optional and are not bundled. Without a checkpoint, workspace commands such as listing and reading files still work; natural-language plan drafting requires a trained checkpoint. No API key is required for Neural.

### Run the local Neural agent

After installing MemeCode, open a project directory and run:

```sh
memecode neural --help
memecode neural --list
memecode neural --read README.md
```

You can also use its dedicated command:

```sh
memecode-neural --list
memecode-neural --draft "Create a small Python calculator"
```

To apply a reviewed plan saved as `plan.json`, first preview it and then explicitly confirm:

```sh
memecode-neural --apply-plan plan.json
memecode-neural --apply-plan plan.json --yes
```

The installer registers both launchers on Termux, Linux, macOS, and Windows. Neural works in the current directory as its workspace. Plan generation needs an available trained checkpoint; file listing/reading and plan validation do not require a model checkpoint.

## MemeCode 2.0 — Memingo core preview

Run the new read-only `.mgo` core from the project root:

```sh
MEMECODE_ACTION=status memingo run src/memecode_core.mgo
MEMECODE_ACTION=list memingo run src/memecode_core.mgo
MEMECODE_ACTION=read MEMECODE_PATH=README.md memingo run src/memecode_core.mgo
```

See [docs/MIGRATION_MEMINGO.md](docs/MIGRATION_MEMINGO.md) for scope and migration stages.

## Architecture

- `src/memecode_core.mgo`: new read-only MemeCode 2.0 core written in Memingo.
- `src/main.mgo` and `src/agent_core.mgo`: previous Memingo entry point and policy.
- `runtime/host_bridge.py`: workspace-scoped file and command bridge.
- `runtime/agent.py`: multi-protocol model adapters, compatibility fallbacks, tool loop, approvals, Git/GitHub tools, review cycle, chat, and history.
- `docs/PROVIDERS.md`: supported provider protocols, setup examples, and diagnostics.
- `install.sh`: Termux, Linux, and macOS installer.
- `runtime/tui.py`: Textual terminal interface, including interactive approval dialogs.
- `requirements.txt`: TUI dependency.
- `install.ps1`: Windows PowerShell installer.
- `docs/TERMUX.md`: Android installation guide.

## Safety

File edits display a diff and require approval. Commands require approval. Git commits and branch creation require approval and remain local; MemeCode does not push. The command bridge is **not an OS sandbox**: approved programs still run with your user permissions. Only use it in projects you trust.

## License

Apache License 2.0. See [LICENSE](LICENSE).


## MemeCode 2.0.1 — Memingo plan preview

The `.mgo` plan validator at `src/memecode_planner.mgo` accepts a JSON plan through `MEMECODE_PLAN_JSON`, validates paths and operation limits, and prints a preview. This stage is read-only: it does not create or replace files. See [docs/MEMINGO_PLANNER.md](docs/MEMINGO_PLANNER.md).

## Walletie compatibility

MemeCode's local coding-agent features remain independent of Walletie. Do not place wallet service credentials in the agent, local project files, or client configuration.

Walletie V1 currently accepts AtDev Cloud HS256 tokens only; other identity systems need the documented SSO bridge first. See the [Walletie integration matrix](https://github.com/Reaccionador2Jeje/Walletie/blob/main/docs/INTEGRATION_MATRIX.md).

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
- [x] One-command installer for Termux and Linux

## One-command install

### Termux (Android)

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

The installer downloads MemeCode and Memingo, creates an isolated Python virtual environment, and adds the `memecode` command. No separate Memingo installation is needed.

## Run

From the folder you want MemeCode to work in:

```sh
cd /path/to/your/project
memecode
```

Useful commands:

```sh
memecode doctor
memecode update
memecode uninstall
memecode "Inspect this project and explain its structure"
```

Set a compatible provider key in your current terminal session:

```sh
export MEMECODE_API_KEY='your-api-key'
export MEMECODE_MODEL='gpt-4o-mini'
```

API use may cost money depending on the provider. Keep keys private and review provider pricing before use.

## Architecture

- `src/main.mgo` and `src/agent_core.mgo`: Memingo entry point and policy.
- `runtime/host_bridge.py`: workspace-scoped file and command bridge.
- `runtime/agent.py`: model adapter, tool loop, approvals, Git/GitHub tools, review cycle, chat, and history.
- `install.sh`: one-command installer and update/uninstall entry point.
- `docs/TERMUX.md`: Android installation guide.

## Safety

File edits display a diff and require approval. Commands require approval. Git commits and branch creation require approval and remain local; MemeCode does not push. The command bridge is **not an OS sandbox**: approved programs still run with your user permissions. Only use it in projects you trust.

## License

Apache License 2.0. See [LICENSE](LICENSE).

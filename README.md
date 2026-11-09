# MemeCode

**An open-source coding-agent project built around Memingo.**

MemeCode is an early open-source coding agent. Its identity, workflow, capabilities, and safety policy are defined in Memingo (`.mgo`); a small Python adapter connects that core to an OpenAI-compatible model API and the local workspace tools.

## Project status

**Status:** Early development — MVP foundation

- [x] Public repository and initial structure
- [x] Memingo project entry point and policy core
- [x] Python host bridge for scoped file and command operations
- [x] Workspace path validation
- [x] Explicit confirmation before running shell commands
- [x] OpenAI-compatible chat-completions provider adapter
- [x] Agent planning and tool-call loop\n- [x] Runtime loads its system policy from Memingo
- [x] Bounded review and repair cycle (1–3 passes)
- [x] Read-only local Git inspection
- [x] Android/Termux installation guide

## Architecture

- `src/main.mgo`: Memingo entry point and project configuration.
- `prompts/system.mgo`: Memingo-side agent principles and safety policy.
- `runtime/host_bridge.py`: minimal OS bridge. It confines file operations to the selected workspace and requires confirmation before executing commands.
- `runtime/agent.py`: model adapter, approval-gated file editing and command tools, plus read-only Git inspection and bounded review/repair mode.
- `docs/TERMUX.md`: phone-first setup instructions for Android/Termux.

The agent's policy and workflow are Memingo-native; model networking and operating-system integration remain in Python. This is an early development tool, not a production-ready sandbox.

## Requirements

- Python 3.10+
- Memingo installed (for running the `.mgo` entry point)

## Quick start

Clone the repository:

```bash
git clone https://github.com/Reaccionador2Jeje/MemeCode.git
cd MemeCode
```

Run the Memingo entry point:

```bash
memingo run src/main.mgo
```

Configure an OpenAI-compatible provider (keep the API key private):

```bash
export MEMECODE_API_KEY='your-api-key'
export MEMECODE_MODEL='gpt-4o-mini'
# Optional: use another compatible provider
# export MEMECODE_BASE_URL='https://provider.example/v1'
python3 runtime/agent.py 'Inspect this project and explain its structure' --workspace .
# Optional bounded review/repair (asks before each edit/command):
python3 runtime/agent.py 'Review the project and run its tests' --workspace . --review --max-repair-rounds 2
```

The agent can list and read project files, propose edits with a diff and approval, and run approved commands. It requires a compatible model API key; API usage may have costs depending on the provider.

Inspect the workspace through the bridge:

```bash
python3 runtime/host_bridge.py --workspace . list .
python3 runtime/host_bridge.py --workspace . read README.md
```

Run a command only after reviewing and approving it:

```bash
python3 runtime/host_bridge.py --workspace . run -- python3 --version
```

The bridge asks for confirmation and passes commands as argument arrays without invoking a shell. It blocks selected executables, but this is not a filesystem sandbox: an approved program may still access files outside the workspace.

## Safety model

- File paths are resolved and checked against the workspace root, including symlinks.
- Commands run with the workspace as their working directory and a reduced environment that omits credential-like variables.\n- Command execution is **not an OS sandbox**: an approved program still runs with your user permissions. Review every command and only run MemeCode in projects you trust.
- Commands are passed as argument arrays; shell interpolation is not enabled.
- Every command requires an interactive approval.
- Destructive/system-administration commands are blocked by default.
- Command execution has a timeout and bounded output.
- Do not put API keys, passwords, or other secrets in project files.

This is a development tool. Review commands before approving them and do not run it on projects you do not trust.

## Roadmap

1. Connect an OpenAI-compatible model provider using environment variables.
2. Add a tool-calling agent loop with plan, edit, test, and review steps.
3. Add diffs and per-file approval before changes.
4. [x] Add read-only Git status/diff/log inspection.
5. Add approval-gated Git mutations and GitHub integration.
6. Improve the phone-friendly Termux workflow and add a local chat interface.

## License

Apache License 2.0. See [LICENSE](LICENSE).

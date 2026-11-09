# MemeCode

**An open-source coding-agent project built around Memingo.**

MemeCode is designed to help inspect a project, propose edits, run checks, and repair errors. This first commit establishes the safe workspace runtime and the Memingo-side project entry point. The model/provider integration and autonomous repair loop are planned next; they are not claimed to be complete yet.

## Project status

<badge>Early development — MVP foundation</badge>

- [x] Public repository and initial structure
- [x] Memingo project entry point
- [x] Python host bridge for scoped file and command operations
- [x] Workspace path validation
- [x] Explicit confirmation before running shell commands
- [ ] LLM provider integration
- [ ] Agent planning and tool-call loop
- [ ] Automated review and repair cycle
- [ ] Git/GitHub integration
- [ ] Android/Termux installation guide

## Architecture

- `src/main.mgo`: Memingo entry point and project configuration.
- `prompts/system.mgo`: Memingo-side agent principles and safety policy.
- `runtime/host_bridge.py`: minimal OS bridge. It confines file operations to the selected workspace and requires confirmation before executing commands.

The bridge is intentionally small: Memingo remains the project's primary language. The current version is a foundation, not yet a fully autonomous AI agent.

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

Inspect the workspace through the bridge:

```bash
python3 runtime/host_bridge.py --workspace . list .
python3 runtime/host_bridge.py --workspace . read README.md
```

Run a command only after reviewing and approving it:

```bash
python3 runtime/host_bridge.py --workspace . run -- python3 --version
```

The bridge asks for confirmation. It does not invoke a shell, and it rejects commands that attempt to escape the workspace or use a blocked executable.

## Safety model

- File paths are resolved and checked against the workspace root, including symlinks.
- Commands run with the workspace as their working directory.
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
4. Add Git status/diff/commit helpers.
5. Add a phone-friendly Termux workflow.

## License

MIT. See [LICENSE](LICENSE).

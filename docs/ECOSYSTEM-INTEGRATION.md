# MemeCode — Ecosystem Integration

Status: planning document; it does not change agent execution behavior.

## Integration boundaries
- Keep workspace file access confined to the selected project.
- Preserve approval gates for edits, command execution, branch creation and commits.
- Keep public GitHub inspection read-only unless the user explicitly approves a write.
- Treat model/provider output as untrusted input.
- Keep provider credentials outside project files and logs.

## Memingo migration
Pin the Memingo version used by the native core. Maintain conformance tests against the legacy host path until behavior is equivalent. Do not remove the legacy runtime based only on a successful compile.

## Next tasks
1. Add tests for workspace path traversal rejection.
2. Add tests proving approval is required for mutations and command execution.
3. Add provider-independent tests for tool-call validation.
4. Document history retention and opt-in behavior.
5. Track native-core parity as a checklist, not a percentage guess.
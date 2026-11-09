# Coding agent instructions

These instructions apply to GitHub Copilot, OpenCode, and other coding agents working in this repository.

## Project priorities

- Treat MemeCode Neural as an experimental, local-first language-model research project.
- The Neural engine must work without a hosted AI API. Do not route Neural inference through the provider-backed MemeCode agent.
- Improve actual model capability: data quality, tokenization, training stability, evaluation, inference, and only then agent/tool integration.
- Do not claim the model is intelligent, production-ready, or comparable to commercial coding models without measured evidence.
- Keep the Memingo runtime and the Neural research engine separate unless a task explicitly requests integration.

## Before changing code

1. Read `neural/README.md`, the relevant implementation, and its tests.
2. Check the current Git diff and preserve unrelated user changes.
3. Identify the smallest coherent implementation step.
4. Explain any architectural trade-off briefly in the change summary.

## Neural engineering rules

- Preserve CPU-only operation. CUDA may be an optional acceleration path, never a requirement.
- Avoid requiring AVX2 or newer CPU instruction sets. The project should remain usable on older x86-64 CPUs where supported by the installed PyTorch build.
- For constrained CPU experiments, document or use:
  `ATEN_CPU_CAPABILITY=default OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`
  when the local environment requires it. Do not bake machine-specific environment overrides into library imports.
- Keep model, tokenizer, checkpoint, and dataset versions explicit and mutually compatible.
- Save checkpoints with enough metadata to reproduce and resume training: model configuration, tokenizer identity, optimizer/training step when applicable, seed, and dataset/evaluation metadata.
- Never commit trained checkpoints, virtual environments, caches, private datasets, credentials, or generated artifacts.
- Do not silently discard a checkpoint when loading fails. Report a useful, actionable error.
- Prefer deterministic data splits and seeded experiments. Report train and validation metrics separately.
- Evaluate on held-out prompts and report limitations. Loss alone is not proof of useful answers.
- Prevent generation loops with well-tested sampling controls, but do not disguise poor model learning as model quality.
- Keep the default model small enough for CPU smoke tests. Make larger configurations opt-in and document their memory/compute cost.
- Do not increase model size or training duration blindly. Measure parameter count, runtime, memory use, and validation behavior.

## Dataset rules

- Training examples must be reviewed, accurate, varied, and relevant to the intended coding assistant.
- Keep JSONL valid and one example per line.
- Do not add private information, secrets, passwords, API keys, copyrighted corpora without permission, or unreviewed bulk-generated filler.
- Separate train and validation data by complete example/document, not random token fragments.
- Add tests for malformed records, empty fields, duplicate leakage, and tokenizer round trips where relevant.

## Safety and tool boundaries

- Treat all model-generated text, code, JSON, and plans as untrusted input.
- Never execute model output as shell commands or tool calls.
- Keep file access confined to the selected workspace and require explicit approval for modifications or command execution.
- Never add arbitrary shell, network, or Git push capability to the Neural model just because a model requests it.
- Do not expose secrets in logs, prompts, tests, or generated files.

## Quality gates

Run focused tests first, then the relevant full test suite. Do not run long training jobs as a substitute for unit tests.
For changes to training or generation, include a small deterministic CPU smoke test.
For changes to checkpoint formats, test both successful loading and clear rejection of incompatible or malformed checkpoints.
For tokenizer changes, test UTF-8 round trips, special tokens, empty text, and unknown/malformed data handling.

## Git workflow

- Make focused commits with descriptive messages.
- Never force-push or rewrite shared history.
- Never commit local checkpoints or secrets.
- Summarize files changed, tests run, and any limitations.

# MemeCode Neural improvement roadmap

MemeCode Neural is an experimental local language model. The immediate goal is to make the existing prototype train and generate reliably, then measure whether it can perform narrow coding tasks. A large coding model cannot be created merely by increasing the layer count or training for more steps.

## Guiding constraints

- Local inference; no hosted model API required.
- CPU-only training and inference remain supported.
- Small smoke tests must run on modest hardware.
- Larger experiments are optional and must state their compute and memory requirements.
- Model quality must be measured on held-out examples, not inferred from a checkpoint existing or a loss decreasing.

## Stage 1 — Stabilize the current baseline

- Keep the existing byte-level model as a reproducible baseline.
- Verify tokenizer special-token behavior and UTF-8 handling.
- Make generation robust against repeated-token loops without hiding weak model learning.
- Record parameter count, train/validation loss, generation settings, and checkpoint metadata.
- Keep checkpoints local and out of Git.

## Stage 2 — Versioned BPE experiment

- Implement BPE as a separate, versioned tokenizer and model path.
- Validate merge-table integrity and tokenizer/model vocabulary compatibility.
- Add deterministic tokenizer training and round-trip tests.
- Save tokenizer identity and configuration in each checkpoint.
- Reject incompatible checkpoints with clear errors; never silently fall back to a different tokenizer.

## Stage 3 — Reproducible training

- Support deterministic seeds, explicit train/validation splits, gradient clipping, and configurable evaluation.
- Add checkpoint resume, including optimizer state and global step.
- Save the best validation checkpoint separately from the latest checkpoint.
- Track training curves and avoid evaluating on training examples.
- Keep default experiments small; benchmark larger settings before recommending them.

## Stage 4 — Better data and task evaluation

- Build a reviewed dataset focused on a narrow initial scope: Python basics, Memingo syntax, code explanation, and small code transformations.
- Keep examples concise, diverse, and accurate.
- Create a held-out evaluation set that is not used for training or tokenizer fitting.
- Score exact-match tasks where possible and use a documented human-review rubric for open-ended tasks.
- Track repetition, malformed output, task success, and validation loss separately.

## Stage 5 — Efficient inference

- Add bounded context handling and predictable generation limits.
- Expose temperature, top-k/top-p where implemented, repetition controls, and stop sequences with tests.
- Benchmark CPU latency and memory use.
- Keep optional acceleration paths separate from the portable CPU path.

## Stage 6 — Coding-agent integration

- Keep model generation separate from tool execution.
- Treat generated plans and code as untrusted.
- Require user approval for file modifications and command execution.
- Use deterministic project tools for file listing, reading, diffing, and tests.
- Do not grant the model arbitrary shell, network, credential, or Git push access.

## Definition of progress

A stage is complete only when its implementation, tests, documentation, and measured results are committed. A successful import, checkpoint load, or non-empty generation is a smoke-test result, not evidence of coding ability.

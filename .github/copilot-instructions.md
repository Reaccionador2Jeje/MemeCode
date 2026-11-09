# GitHub Copilot instructions

Read the repository-root `AGENTS.md` before making changes. It is the shared engineering contract for Copilot, OpenCode, and other coding agents.

For MemeCode Neural, prioritize real model improvement in this order:

1. Reliable, versioned tokenizer and dataset pipeline.
2. Reproducible training with checkpoint resume and correct validation.
3. Generation quality and loop prevention, measured separately from training loss.
4. Held-out coding-task evaluation and regression tests.
5. Efficient CPU inference and optional acceleration.
6. Carefully reviewed integration with the coding-agent workflow.

Keep Neural local-first and independent of hosted provider APIs. Do not claim that a tiny model trained on a tiny dataset can replace Copilot or other large coding models. Use Copilot to engineer and review MemeCode; do not confuse Copilot's own intelligence with the capability of MemeCode Neural.

Preserve CPU-only compatibility, avoid AVX2 assumptions, protect user data and secrets, and never execute model-generated commands. Keep changes small, testable, and documented. Do not commit checkpoints, virtual environments, caches, or secrets.

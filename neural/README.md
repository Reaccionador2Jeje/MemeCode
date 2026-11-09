# MemeCode Neural

MemeCode Neural is an experimental, locally trained language-model prototype. It does not call hosted AI APIs.

## Requirements

- Python 3.10 or newer
- PyTorch (see `requirements-neural.txt`)
- A computer with enough RAM for the selected model and batch size

PyTorch availability varies by operating system and device. Android/Termux is not currently a supported installation target; use a compatible desktop or notebook environment for the first experiments.

## Quick start

From the repository root:

```bash
python -m pip install -r requirements-neural.txt
python -m neural.train --steps 500
python -m neural.generate "¿Qué es Memingo?"
```

The first training run creates `neural/checkpoints/memecode-neural.pt`. The checkpoint is a local generated artifact and should not be committed to Git.

## Add training examples

Append one JSON object per line to `neural/dataset/examples.jsonl`:

```json
{"prompt":"¿Qué es una función?","response":"Una función es un bloque reutilizable de código."}
```

Keep examples accurate, varied, and reviewed. Do not add private data, API keys, passwords, or personal information.

## Important limitations

- This is a tiny experimental Transformer, not a production assistant.
- The starter dataset is only for smoke tests and learning; it is far too small for reliable coding assistance.
- Training from scratch requires substantial data, compute, evaluation, and iteration.
- The model generates text only. It does not safely execute shell commands or modify projects.
- A lower training loss does not prove that answers are correct. Evaluate with held-out examples and human review.

## Development checks

Run the neural tests with:

```bash
python -m unittest tests.test_neural
```

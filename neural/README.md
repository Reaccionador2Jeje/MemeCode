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

Training separates complete examples into training and validation sets, then reports both losses periodically. The default validation fraction is 15%.

Try a shorter experiment on a small device:

```bash
python -m neural.train --steps 30 --batch-size 2 --block-size 64 --eval-batches 2
```

The first training run creates `neural/checkpoints/memecode-neural.pt`. The checkpoint is a local generated artifact and should not be committed to Git.

## Add training examples

Append one JSON object per line to `neural/dataset/examples.jsonl`:

```json
{"prompt":"¿Qué es una función?","response":"Una función es un bloque reutilizable de código."}
```

Keep examples accurate, varied, and reviewed. Do not add private data, API keys, passwords, or personal information. At least two valid examples are required; both training and validation partitions must contain enough tokens for the selected block size.

## Understand the metrics

- `train_loss`: average next-token prediction loss on training examples.
- `validation_loss`: average next-token prediction loss on examples held out from training.
- If training loss falls while validation loss rises, the model may be memorizing instead of generalizing.
- Loss is not a score for factual correctness. Always test generated answers with new prompts and human review.

The split is deterministic for a fixed dataset and `--seed`. The validation set is separated by whole examples to avoid placing fragments of the same example in both partitions.

## Development checks

Run the neural tests with:

```bash
python -m unittest tests.test_neural
```

## Important limitations

- This is a tiny experimental Transformer, not a production assistant.
- The starter dataset is only for learning and smoke tests; it is far too small for reliable coding assistance.
- Training from scratch requires substantial data, compute, and evaluation.
- The model generates text only. It does not safely execute shell commands or modify projects.

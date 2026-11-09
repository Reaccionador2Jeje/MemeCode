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


## Local coding agent (experimental)

MemeCode Neural includes a local command-driven coding agent. It does not contact an AI provider.

From the repository root:

```bash
# List project files
python -m neural.agent --workspace . --list

# Read a project file
python -m neural.agent --workspace . --read README.md

# Ask the locally trained model (requires a checkpoint)
python -m neural.agent --workspace . --task "Explica este proyecto"

# Create a new file; explicit confirmation flag is required
python -m neural.agent --workspace . --new notes.txt "Notas del proyecto" --yes

# Run the fixed unittest discovery command; explicit confirmation is required
python -m neural.agent --workspace . --test --yes
```

### Safety and current capabilities

- The model's generated text is never interpreted as a command or tool call.
- File creation is limited to new files inside the workspace; overwriting is refused.
- File reads reject common secret-file names and files larger than 256 KB.
- Path traversal outside the workspace is rejected.
- Test execution uses a fixed Python unittest command, no shell, and requires `--yes`.
- No hay herramienta de shell arbitraria, red ni push automático a Git.
- Neural puede redactar planes JSON y aplicarlos solo después de revisarlos y confirmarlos.
- Without a trained checkpoint, the local tools still work, but natural-language model answers are unavailable.
- This is an early, command-driven agent, not yet an autonomous coding assistant. The tiny starter model is not expected to reliably understand or write programs.

## Neural 0.3: planificar y aplicar cambios

El agente puede pedir al checkpoint local que redacte un plan JSON:

```bash
python -m neural.agent --draft "Crea un módulo de saludos en Python"
```

La salida del modelo es solo una propuesta. Guárdala como `plan.json` dentro del workspace, revísala y valida su vista previa:

```bash
python -m neural.agent --apply-plan plan.json
```

Solo después de revisar las rutas y el contenido, aplica el plan:

```bash
python -m neural.agent --apply-plan plan.json --yes
```

Formato admitido:

```json
{
  "version": 1,
  "summary": "Añadir un módulo de ejemplo",
  "operations": [
    {
      "action": "create_file",
      "path": "src/saludos.py",
      "content": "def hola():\\n    return 'Hola'"
    }
  ]
}
```

Se admiten como máximo ocho operaciones por plan. Las acciones son `create_file` y `replace_file`; no se admite shell, red, borrado ni comandos indicados por el modelo. Al reemplazar un archivo, se guarda una copia en `.memecode/backups/`. Los planes no se aplican sin `--yes`.

**Limitación:** el Transformer de inicio es muy pequeño y puede generar JSON inválido o código incorrecto. Sin checkpoint, `--draft` no puede generar planes. Esta versión proporciona el flujo de planificación, validación y aplicación, no una autonomía comparable a un agente comercial. Ejecutar pruebas sigue siendo una acción separada y requiere confirmación.

"""Pruebas básicas del tokenizador, Transformer y división del dataset."""
import unittest
from pathlib import Path
import tempfile

try:
    import torch
    from neural.model import MemeCodeGPT, ModelConfig
    from neural.tokenizer import BOS, EOS, encode, decode
    from neural.train import load_samples, split_samples
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@unittest.skipUnless(TORCH_AVAILABLE, "PyTorch no está instalado")
class NeuralTests(unittest.TestCase):
    def test_tokenizer_round_trip_utf8(self):
        text = "¡Hola, MemeCode! ñ 🧠"
        self.assertEqual(decode(encode(text)), text)

    def test_special_tokens(self):
        tokens = encode("hola", add_bos=True, add_eos=True)
        self.assertEqual(tokens[0], BOS)
        self.assertEqual(tokens[-1], EOS)

    def test_model_forward_shape_and_loss(self):
        config = ModelConfig(block_size=16, embedding_size=32, heads=4, layers=1, dropout=0.0)
        model = MemeCodeGPT(config)
        inputs = torch.randint(0, config.vocab_size, (2, 12))
        targets = torch.randint(0, config.vocab_size, (2, 12))
        logits, loss = model(inputs, targets)
        self.assertEqual(tuple(logits.shape), (2, 12, config.vocab_size))
        self.assertIsNotNone(loss)
        self.assertTrue(torch.isfinite(loss).item())

    def test_model_rejects_long_sequence(self):
        config = ModelConfig(block_size=8, embedding_size=32, heads=4, layers=1)
        model = MemeCodeGPT(config)
        with self.assertRaises(ValueError):
            model(torch.zeros((1, 9), dtype=torch.long))

    def test_split_keeps_examples_independent_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "samples.jsonl"
            path.write_text(
                '{"prompt":"uno","response":"respuesta uno"}\n'
                '{"prompt":"dos","response":"respuesta dos"}\n'
                '{"prompt":"tres","response":"respuesta tres"}\n'
                '{"prompt":"cuatro","response":"respuesta cuatro"}\n',
                encoding="utf-8",
            )
            samples = load_samples(path)
            train_a, val_a = split_samples(samples, 0.25, 7)
            train_b, val_b = split_samples(samples, 0.25, 7)
            self.assertEqual(train_a, train_b)
            self.assertEqual(val_a, val_b)
            self.assertEqual(len(train_a) + len(val_a), len(samples))
            self.assertFalse(set(map(tuple, train_a)) & set(map(tuple, val_a)))

    def test_split_rejects_invalid_fraction(self):
        with self.assertRaises(ValueError):
            split_samples([[1, 2], [3, 4]], 0.01, 1)


if __name__ == "__main__":
    unittest.main()

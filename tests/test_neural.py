"""Pruebas básicas del tokenizador y el Transformer de MemeCode Neural."""
import unittest

try:
    import torch
    from neural.model import MemeCodeGPT, ModelConfig
    from neural.tokenizer import BOS, EOS, encode, decode
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


if __name__ == "__main__":
    unittest.main()

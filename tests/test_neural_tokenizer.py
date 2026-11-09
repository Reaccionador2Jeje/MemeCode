import unittest

from neural.tokenizer import BOS, EOS, PAD, VOCAB_SIZE, encode, decode


class NeuralTokenizerTests(unittest.TestCase):
    def test_utf8_round_trip(self):
        text = "MemeCode Neural: programación en español 🚀"
        self.assertEqual(decode(encode(text)), text)

    def test_special_tokens(self):
        tokens = encode("hola", add_bos=True, add_eos=True)
        self.assertEqual(tokens[0], BOS)
        self.assertEqual(tokens[-1], EOS)
        self.assertEqual(VOCAB_SIZE, 259)
        self.assertGreaterEqual(PAD, 256)

    def test_rejects_non_text(self):
        with self.assertRaises(TypeError):
            encode(123)


if __name__ == "__main__":
    unittest.main()

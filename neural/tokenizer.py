"""Tokenizer UTF-8 por bytes; no necesita vocabulario ni dependencias externas."""

BOS = 256
EOS = 257
PAD = 258
VOCAB_SIZE = 259


def encode(text: str, *, add_bos: bool = False, add_eos: bool = False) -> list[int]:
    """Convierte texto UTF-8 en IDs de byte."""
    if not isinstance(text, str):
        raise TypeError("text debe ser str")
    tokens = list(text.encode("utf-8"))
    if add_bos:
        tokens.insert(0, BOS)
    if add_eos:
        tokens.append(EOS)
    return tokens


def decode(tokens: list[int]) -> str:
    """Reconstruye texto UTF-8 ignorando tokens especiales."""
    raw = bytes(token for token in tokens if 0 <= token <= 255)
    return raw.decode("utf-8", errors="replace")

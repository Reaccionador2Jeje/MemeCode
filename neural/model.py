"""Pequeño Transformer causal para experimentos locales de MemeCode Neural."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import torch
from torch import nn


@dataclass
class ModelConfig:
    vocab_size: int = 259
    block_size: int = 128
    embedding_size: int = 96
    heads: int = 4
    layers: int = 2
    dropout: float = 0.1


class TransformerBlock(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.embedding_size)
        self.attention = nn.MultiheadAttention(
            config.embedding_size, config.heads, dropout=config.dropout, batch_first=True
        )
        self.norm2 = nn.LayerNorm(config.embedding_size)
        self.feed_forward = nn.Sequential(
            nn.Linear(config.embedding_size, config.embedding_size * 4),
            nn.GELU(),
            nn.Linear(config.embedding_size * 4, config.embedding_size),
            nn.Dropout(config.dropout),
        )
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        length = x.size(1)
        # True significa que la posición futura queda bloqueada.
        mask = torch.triu(torch.ones(length, length, device=x.device, dtype=torch.bool), diagonal=1)
        normalized = self.norm1(x)
        attended, _ = self.attention(normalized, normalized, normalized, attn_mask=mask, need_weights=False)
        x = x + self.dropout(attended)
        return x + self.feed_forward(self.norm2(x))


class MemeCodeGPT(nn.Module):
    def __init__(self, config: ModelConfig | None = None):
        super().__init__()
        self.config = config or ModelConfig()
        c = self.config
        self.token_embedding = nn.Embedding(c.vocab_size, c.embedding_size)
        self.position_embedding = nn.Embedding(c.block_size, c.embedding_size)
        self.blocks = nn.Sequential(*(TransformerBlock(c) for _ in range(c.layers)))
        self.final_norm = nn.LayerNorm(c.embedding_size)
        self.output = nn.Linear(c.embedding_size, c.vocab_size, bias=False)
        self.output.weight = self.token_embedding.weight
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, tokens: torch.Tensor, targets: torch.Tensor | None = None):
        batch, length = tokens.shape
        if length > self.config.block_size:
            raise ValueError("La secuencia supera block_size")
        positions = torch.arange(length, device=tokens.device)
        x = self.token_embedding(tokens) + self.position_embedding(positions)[None, :, :]
        x = self.final_norm(self.blocks(x))
        logits = self.output(x)
        loss = None
        if targets is not None:
            loss = nn.functional.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, tokens: torch.Tensor, max_new_tokens: int = 120, temperature: float = 0.8):
        self.eval()
        for _ in range(max_new_tokens):
            context = tokens[:, -self.config.block_size:]
            logits, _ = self(context)
            logits = logits[:, -1, :] / max(temperature, 0.05)
            probabilities = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probabilities, num_samples=1)
            tokens = torch.cat((tokens, next_token), dim=1)
        return tokens

    def config_dict(self) -> dict:
        return asdict(self.config)

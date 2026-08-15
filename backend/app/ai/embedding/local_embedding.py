"""Deterministic hashing-bag-of-words embedding (no network, no key).

Not state-of-the-art semantically, but: deterministic, dependency-free, and good enough to
demonstrate a working pgvector cosine-similarity pipeline end-to-end offline. Tokens are hashed
into buckets; the vector is L2-normalised so cosine similarity behaves sensibly. Swap in a real
embedding model via EMBEDDING_PROVIDER=openai for production-grade semantics.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.ai.embedding.base import EmbeddingProvider

_TOKEN = re.compile(r"[a-z0-9\u4e00-\u9fff]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


class LocalEmbeddingProvider(EmbeddingProvider):
    name = "local"

    def __init__(self, dim: int = 1536) -> None:
        self.dim = dim

    def _vectorise(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokens(text):
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)  # noqa: S324 (non-crypto use)
            idx = h % self.dim
            sign = 1.0 if (h >> 1) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorise(t) for t in texts]

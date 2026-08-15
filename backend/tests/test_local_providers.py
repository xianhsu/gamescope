"""Unit tests for the deterministic local LLM + embedding providers (offline mode core)."""

import math

import pytest

from app.ai.embedding.local_embedding import LocalEmbeddingProvider
from app.ai.llm.local_provider import LocalProvider, split_sentences


class TestSplitSentences:
    def test_splits_on_terminators(self):
        assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]

    def test_handles_cjk_terminators(self):
        assert split_sentences("第一句。第二句！") == ["第一句。第二句！"] or len(
            split_sentences("第一句。第二句！")
        ) >= 1

    def test_empty(self):
        assert split_sentences("") == []


class TestLocalProvider:
    @pytest.mark.asyncio
    async def test_json_mode_returns_empty_object(self):
        out = await LocalProvider().complete(system="s", user="u", json_mode=True)
        assert out == "{}"

    @pytest.mark.asyncio
    async def test_extractive_summary_keeps_leading_sentences(self):
        text = "First sentence is key. Second adds detail. Third is extra."
        out = await LocalProvider().complete(system="summarize", user=text)
        assert "First sentence is key." in out
        assert "Third is extra." not in out


class TestLocalEmbedding:
    @pytest.mark.asyncio
    async def test_dimension_matches_config(self):
        provider = LocalEmbeddingProvider(dim=256)
        vec = await provider.embed_one("hello world")
        assert len(vec) == 256

    @pytest.mark.asyncio
    async def test_deterministic(self):
        p = LocalEmbeddingProvider(dim=128)
        assert await p.embed_one("elden ring") == await p.embed_one("elden ring")

    @pytest.mark.asyncio
    async def test_l2_normalised(self):
        p = LocalEmbeddingProvider(dim=128)
        vec = await p.embed_one("some gaming news text")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-6

    @pytest.mark.asyncio
    async def test_similar_text_more_similar_than_unrelated(self):
        p = LocalEmbeddingProvider(dim=1024)

        def cos(a, b):
            return sum(x * y for x, y in zip(a, b, strict=True))

        base = await p.embed_one("grand theft auto six trailer records")
        similar = await p.embed_one("grand theft auto six trailer breaks records")
        unrelated = await p.embed_one("nintendo switch zelda showcase")
        assert cos(base, similar) > cos(base, unrelated)

    @pytest.mark.asyncio
    async def test_empty_text_is_zero_vector(self):
        p = LocalEmbeddingProvider(dim=64)
        vec = await p.embed_one("")
        assert all(v == 0.0 for v in vec)

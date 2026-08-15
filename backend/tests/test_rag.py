"""Unit tests for RAG context building + grounded (local, deterministic) answering."""

from datetime import UTC, datetime

import pytest

from app.ai.llm.local_provider import LocalProvider
from app.ai.rag import ContextItem, build_context_text, extractive_answer, generate_answer


def _item(index, title, text, *, official=False, rumor=False):
    return ContextItem(
        index=index,
        title=title,
        source="ign",
        url=f"https://ign.com/{index}",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        is_official=official,
        is_rumor=rumor,
        text=text,
    )


class TestBuildContextText:
    def test_numbers_and_tags_sources(self):
        items = [_item(1, "GTA 6 trailer", "Rockstar released a trailer.", official=True)]
        text = build_context_text(items)
        assert "[1]" in text
        assert "official" in text
        assert "2026-01-01" in text

    def test_respects_char_budget(self):
        items = [_item(i, f"Title {i}", "x" * 1000) for i in range(1, 10)]
        text = build_context_text(items, max_chars=500)
        assert len(text) <= 600  # budget + a small block overrun tolerance


class TestExtractiveAnswer:
    def test_empty_items_returns_insufficient_en(self):
        out = extractive_answer("anything", [], "en")
        assert "isn't enough information" in out

    def test_empty_items_returns_insufficient_zh(self):
        out = extractive_answer("随便", [], "zh")
        assert "没有足够信息" in out

    def test_answer_is_grounded_with_citations(self):
        items = [
            _item(1, "GTA 6 trailer", "The GTA 6 trailer broke records in 24 hours."),
            _item(2, "Zelda teaser", "Nintendo teased a new Zelda."),
        ]
        out = extractive_answer("what happened with the gta 6 trailer?", items, "en")
        assert "[1]" in out  # cites the relevant source
        assert "records" in out.lower()

    def test_official_and_rumor_are_labelled(self):
        items = [
            _item(1, "Official post", "Studio confirmed the date.", official=True),
            _item(2, "Leak", "An insider claims details leaked.", rumor=True),
        ]
        out = extractive_answer("date and leaks", items, "en")
        assert "(official)" in out
        assert "(rumor)" in out


class TestGenerateAnswer:
    @pytest.mark.asyncio
    async def test_local_provider_uses_extractive_path(self):
        items = [_item(1, "GTA 6", "The GTA 6 trailer broke records.")]
        out = await generate_answer(LocalProvider(), "gta 6 trailer", items, "en")
        assert "[1]" in out

    @pytest.mark.asyncio
    async def test_no_items_is_insufficient(self):
        out = await generate_answer(LocalProvider(), "q", [], "en")
        assert "isn't enough information" in out

"""Unit tests for the dedup stage (URL exact + title-similarity, DB + within-run)."""

from app.ingestion.stages.dedup import dedup
from app.ingestion.types import PipelineContext, PipelineItem


def _item(title: str, normalized_url: str) -> PipelineItem:
    return PipelineItem(raw=None, title=title, normalized_url=normalized_url)


def _ctx(recent_titles=None) -> PipelineContext:
    return PipelineContext(
        db=None,
        source=None,
        llm=None,
        embedder=None,
        games=[],
        recent_titles=recent_titles or [],
    )


class TestDedup:
    def test_unique_item_passes(self):
        item = dedup(_item("GTA 6 trailer", "https://ign.com/gta6"), _ctx())
        assert item.dropped is False

    def test_duplicate_url_within_run_dropped(self):
        ctx = _ctx()
        first = dedup(_item("A", "https://ign.com/x"), ctx)
        second = dedup(_item("A again, different title", "https://ign.com/x"), ctx)
        assert first.dropped is False
        assert second.dropped is True
        assert second.drop_reason == "duplicate_url_in_run"

    def test_duplicate_url_in_db_dropped(self):
        ctx = _ctx(recent_titles=[(1, "Old title", "https://ign.com/known")])
        item = dedup(_item("Fresh title", "https://ign.com/known"), ctx)
        assert item.dropped is True
        assert item.drop_reason == "duplicate_url_db"

    def test_near_duplicate_title_dropped(self):
        ctx = _ctx(recent_titles=[(1, "GTA 6 trailer breaks records", "https://a.com/1")])
        item = dedup(_item("GTA 6 trailer breaks record", "https://b.com/2"), ctx)
        assert item.dropped is True
        assert item.drop_reason == "duplicate_title"

    def test_distinct_title_and_url_survives(self):
        ctx = _ctx(recent_titles=[(1, "Zelda showcase recap", "https://a.com/1")])
        item = dedup(_item("Battlefield reveal event", "https://b.com/2"), ctx)
        assert item.dropped is False

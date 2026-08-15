"""Unit tests for RetrievalFilters.from_parsed (time-range → since datetime)."""

from datetime import UTC, datetime

from app.retrieval.base import RetrievalFilters


class TestRetrievalFilters:
    def test_no_time_range_means_no_since(self):
        f = RetrievalFilters.from_parsed(game_id=None, platform=None, time_range=None)
        assert f.since is None

    def test_7d_sets_since_about_a_week_ago(self):
        f = RetrievalFilters.from_parsed(game_id=None, platform=None, time_range="7d")
        assert f.since is not None
        delta = datetime.now(UTC) - f.since
        assert 6.5 <= delta.total_seconds() / 86400 <= 7.5

    def test_passes_through_game_and_platform(self):
        f = RetrievalFilters.from_parsed(game_id=42, platform="PC", time_range="1d")
        assert f.game_id == 42
        assert f.platform == "PC"

    def test_unknown_time_range_ignored(self):
        f = RetrievalFilters.from_parsed(game_id=None, platform=None, time_range="banana")
        assert f.since is None

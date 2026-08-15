"""Unit tests for the deterministic query-understanding rules (no LLM needed)."""

import pytest

from app.ai.query_understanding import (
    detect_language,
    match_game,
    match_platform,
    match_time_range,
    parse_query,
)

ALIASES = {
    "Grand Theft Auto VI": ["GTA 6", "GTA VI", "GTA6"],
    "The Legend of Zelda": ["Zelda"],
}


class TestLanguage:
    def test_english(self):
        assert detect_language("latest gta 6 news") == "en"

    def test_chinese(self):
        assert detect_language("最新的 GTA6 消息") == "zh"


class TestGameMatch:
    def test_matches_alias(self):
        assert match_game("any news on gta 6?", ALIASES) == "Grand Theft Auto VI"

    def test_matches_canonical(self):
        assert match_game("the legend of zelda teaser", ALIASES) == "The Legend of Zelda"

    def test_longest_alias_wins(self):
        # "zelda" and canonical both present; canonical (longer) should win.
        assert match_game("the legend of zelda", ALIASES) == "The Legend of Zelda"

    def test_no_match(self):
        assert match_game("random unrelated query", ALIASES) is None

    def test_word_boundary_prevents_substring_false_positive(self):
        # "gta6" alias should not match inside an unrelated token.
        assert match_game("upgrade6pack", ALIASES) is None


class TestPlatformMatch:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("news for ps5 owners", "PlayStation"),
            ("xbox game pass additions", "Xbox"),
            ("nintendo switch lineup", "Nintendo"),
            ("best steam deals", "PC"),
            ("android release date", "Mobile"),
        ],
    )
    def test_platforms(self, query, expected):
        assert match_platform(query) == expected

    def test_no_platform(self):
        assert match_platform("general gaming news") is None


class TestTimeRange:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("what happened today", "1d"),
            ("news this week", "7d"),
            ("anything in the past month", "30d"),
            ("recently announced", "14d"),
        ],
    )
    def test_time_ranges(self, query, expected):
        assert match_time_range(query) == expected

    def test_none_when_absent(self):
        assert match_time_range("tell me about elden ring") is None


class TestParseQuery:
    def test_full_parse_sets_freshness(self):
        parsed = parse_query("latest GTA 6 news on PS5 this week", ALIASES)
        assert parsed.game == "Grand Theft Auto VI"
        assert parsed.platform == "PlayStation"
        assert parsed.time_range == "7d"
        assert parsed.requires_freshness is True
        assert parsed.language == "en"

    def test_minimal_query(self):
        parsed = parse_query("elden ring", ALIASES)
        assert parsed.requires_freshness is False
        assert parsed.platform is None

    def test_chinese_freshness(self):
        parsed = parse_query("最新的赛博朋克消息", ALIASES)
        assert parsed.language == "zh"
        assert parsed.requires_freshness is True

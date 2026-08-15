"""Unit tests for the pure text helpers (URL normalization, slug, excerpt, hash, similarity)."""

from app.ingestion.text import (
    content_hash,
    make_excerpt,
    normalize_url,
    slugify,
    title_similarity,
)


class TestNormalizeUrl:
    def test_lowercases_scheme_and_host_and_strips_www(self):
        assert normalize_url("HTTPS://WWW.IGN.com/Articles/Foo") == "https://ign.com/Articles/Foo"

    def test_drops_tracking_params_but_keeps_real_ones(self):
        out = normalize_url("https://ign.com/a?utm_source=twitter&id=7&fbclid=xyz")
        assert "utm_source" not in out
        assert "fbclid" not in out
        assert "id=7" in out

    def test_removes_fragment_and_trailing_slash(self):
        assert normalize_url("https://ign.com/a/#section") == "https://ign.com/a"

    def test_two_urls_differing_only_by_tracking_normalize_equal(self):
        a = normalize_url("https://ign.com/gta6?utm_campaign=a")
        b = normalize_url("https://www.ign.com/gta6/?utm_campaign=b&fbclid=1")
        assert a == b

    def test_empty_is_safe(self):
        assert normalize_url("") == ""


class TestSlugify:
    def test_basic(self):
        assert slugify("Grand Theft Auto VI!") == "grand-theft-auto-vi"

    def test_collapses_symbols_and_trims(self):
        assert slugify("  --Hello, World--  ") == "hello-world"

    def test_empty_falls_back(self):
        assert slugify("") == "article"

    def test_respects_max_len(self):
        assert len(slugify("a" * 200, max_len=10)) <= 10


class TestMakeExcerpt:
    def test_short_text_unchanged(self):
        assert make_excerpt("hello world", 500) == "hello world"

    def test_long_text_truncated_on_word_boundary_with_ellipsis(self):
        text = "word " * 300
        out = make_excerpt(text, 50)
        assert len(out) <= 51  # 50 + ellipsis char
        assert out.endswith("…")

    def test_collapses_whitespace(self):
        assert make_excerpt("a\n\n   b\tc", 500) == "a b c"


class TestContentHash:
    def test_deterministic(self):
        assert content_hash("Title", "Body") == content_hash("Title", "Body")

    def test_case_and_whitespace_insensitive(self):
        assert content_hash("Title  ", "BODY") == content_hash("title", "body")

    def test_different_content_differs(self):
        assert content_hash("Title", "Body A") != content_hash("Title", "Body B")

    def test_is_sha256_hex(self):
        h = content_hash("x")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestTitleSimilarity:
    def test_identical_is_one(self):
        assert title_similarity("GTA 6 trailer", "GTA 6 trailer") == 1.0

    def test_near_duplicate_is_high(self):
        score = title_similarity(
            "GTA 6 trailer breaks records", "GTA 6 trailer breaks record"
        )
        assert score >= 0.9

    def test_unrelated_is_low(self):
        assert title_similarity("Zelda showcase", "Battlefield reveal") < 0.5

    def test_empty_is_zero(self):
        assert title_similarity("", "anything") == 0.0

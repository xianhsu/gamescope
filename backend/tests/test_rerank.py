"""Unit tests for the transparent heuristic reranker.

Uses lightweight stubs (only `.is_official` and `.published_at` are read) so the test stays
a pure unit test with no ORM/session coupling.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.retrieval.hybrid import FusedDoc
from app.retrieval.rerank import rerank


@dataclass
class ArticleStub:
    is_official: bool = False
    published_at: datetime | None = None


def _fused(article_id, score, sources):
    return FusedDoc(article_id=article_id, score=score, sources=sources)


class TestRerank:
    def test_official_gets_boost_over_equal_base_score(self):
        now = datetime.now(UTC)
        articles = {
            1: ArticleStub(is_official=True, published_at=now),
            2: ArticleStub(is_official=False, published_at=now),
        }
        fused = [_fused(1, 0.10, ["fts"]), _fused(2, 0.10, ["fts"])]
        out = rerank(fused, articles, limit=10)
        assert out[0].article_id == 1

    def test_recent_beats_old_when_base_equal(self):
        now = datetime.now(UTC)
        articles = {
            1: ArticleStub(published_at=now),
            2: ArticleStub(published_at=now - timedelta(days=60)),
        }
        fused = [_fused(2, 0.10, ["fts"]), _fused(1, 0.10, ["fts"])]
        out = rerank(fused, articles, limit=10)
        assert out[0].article_id == 1

    def test_multi_retriever_agreement_boosts(self):
        now = datetime.now(UTC)
        articles = {1: ArticleStub(published_at=now), 2: ArticleStub(published_at=now)}
        fused = [_fused(1, 0.10, ["fts"]), _fused(2, 0.10, ["fts", "vector"])]
        out = rerank(fused, articles, limit=10)
        assert out[0].article_id == 2

    def test_limit_applies(self):
        articles = {i: ArticleStub() for i in range(5)}
        fused = [_fused(i, 0.1, ["fts"]) for i in range(5)]
        assert len(rerank(fused, articles, limit=3)) == 3

    def test_missing_article_does_not_crash(self):
        fused = [_fused(999, 0.1, ["fts"])]
        out = rerank(fused, {}, limit=10)
        assert out[0].article_id == 999

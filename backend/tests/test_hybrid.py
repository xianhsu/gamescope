"""Unit tests for Reciprocal Rank Fusion — the heart of hybrid retrieval."""

from app.retrieval.base import RetrievedDoc
from app.retrieval.hybrid import reciprocal_rank_fusion


def _fts(ids):
    return [RetrievedDoc(article_id=i, score=0.0, retriever="fts") for i in ids]


def _vec(ids):
    return [RetrievedDoc(article_id=i, score=0.0, retriever="vector") for i in ids]


class TestRRF:
    def test_doc_in_both_lists_outranks_single_list_docs(self):
        # Article 1 appears top of both; article 2 only in FTS, article 3 only in vector.
        fused = reciprocal_rank_fusion([_fts([1, 2]), _vec([1, 3])], k=60)
        top = fused[0]
        assert top.article_id == 1
        assert set(top.sources) == {"fts", "vector"}

    def test_score_uses_rank_not_raw_score(self):
        # Even with zero raw scores, ranking still produces a meaningful ordering.
        fused = reciprocal_rank_fusion([_fts([10, 20, 30])], k=60)
        assert [d.article_id for d in fused] == [10, 20, 30]
        assert fused[0].score > fused[1].score > fused[2].score

    def test_k_dampens_contribution(self):
        small_k = reciprocal_rank_fusion([_fts([1])], k=1)[0].score
        large_k = reciprocal_rank_fusion([_fts([1])], k=1000)[0].score
        assert small_k > large_k  # larger k → smaller per-rank contribution

    def test_limit_truncates(self):
        fused = reciprocal_rank_fusion([_fts([1, 2, 3, 4, 5])], k=60, limit=2)
        assert len(fused) == 2

    def test_sources_deduplicated(self):
        # Same doc from the same retriever twice shouldn't duplicate the source label.
        docs = [RetrievedDoc(article_id=1, score=0, retriever="fts")]
        fused = reciprocal_rank_fusion([docs, docs], k=60)
        assert fused[0].sources.count("fts") == 1

    def test_external_live_docs_fused_by_url(self):
        live = [
            RetrievedDoc(article_id=0, score=0, retriever="live", external={"url": "http://x/1"}),
        ]
        fused = reciprocal_rank_fusion([_fts([1]), live], k=60)
        assert len(fused) == 2
        assert any(d.article_id == 0 and d.external for d in fused)

    def test_empty_input(self):
        assert reciprocal_rank_fusion([], k=60) == []

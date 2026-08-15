"""Hybrid fusion via Reciprocal Rank Fusion (RRF).

RRF is parameter-light and explainable: score(d) = Σ_r 1/(k + rank_r(d)), summed over the
retrievers that returned d. It is robust to differing score scales (FTS ts_rank vs cosine
similarity) because it uses ranks, not raw scores — which is exactly why it beats naive score
addition here. `k` (default 60) dampens the influence of very low ranks.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.base import RetrievedDoc


@dataclass
class FusedDoc:
    article_id: int
    score: float
    sources: list[str]
    external: dict | None = None


def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievedDoc]], *, k: int = 60, limit: int | None = None
) -> list[FusedDoc]:
    """Fuse multiple ranked lists. Each list must already be sorted best-first."""
    agg: dict[int, FusedDoc] = {}
    external_agg: dict[str, FusedDoc] = {}

    for docs in ranked_lists:
        for rank, doc in enumerate(docs):  # rank 0 = best
            contribution = 1.0 / (k + rank + 1)
            if doc.article_id and doc.article_id > 0:
                existing = agg.get(doc.article_id)
                if existing is None:
                    agg[doc.article_id] = FusedDoc(
                        article_id=doc.article_id, score=contribution, sources=[doc.retriever]
                    )
                else:
                    existing.score += contribution
                    if doc.retriever not in existing.sources:
                        existing.sources.append(doc.retriever)
            elif doc.external:  # live results keyed by URL
                key = doc.external.get("url", "")
                existing = external_agg.get(key)
                if existing is None:
                    external_agg[key] = FusedDoc(
                        article_id=0,
                        score=contribution,
                        sources=[doc.retriever],
                        external=doc.external,
                    )
                else:
                    existing.score += contribution

    fused = sorted([*agg.values(), *external_agg.values()], key=lambda d: d.score, reverse=True)
    return fused[:limit] if limit else fused

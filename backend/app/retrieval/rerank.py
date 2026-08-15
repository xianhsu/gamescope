"""Lightweight, dependency-free reranker (optional final pass).

Default rerank is a transparent heuristic on top of the fused RRF score:
  final = rrf_score * (1 + w_official*is_official + w_recency*recency + w_multi*multi_retriever)

A learned cross-encoder / LLM reranker could replace this behind the same function signature;
we keep the default explainable and free of extra model dependencies (documented trade-off).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.article import Article
from app.retrieval.hybrid import FusedDoc


def rerank(
    fused: list[FusedDoc],
    articles_by_id: dict[int, Article],
    *,
    limit: int,
    w_official: float = 0.15,
    w_recency: float = 0.25,
    w_multi: float = 0.10,
) -> list[FusedDoc]:
    now = datetime.now(UTC)
    for doc in fused:
        boost = 1.0
        art = articles_by_id.get(doc.article_id)
        if art is not None:
            if art.is_official:
                boost += w_official
            if art.published_at:
                age_days = max((now - art.published_at).total_seconds() / 86400.0, 0.0)
                boost += w_recency * (1.0 / (1.0 + age_days / 7.0))  # decays over ~weeks
        if len(doc.sources) > 1:  # agreed on by both FTS and vector
            boost += w_multi
        doc.score *= boost
    return sorted(fused, key=lambda d: d.score, reverse=True)[:limit]

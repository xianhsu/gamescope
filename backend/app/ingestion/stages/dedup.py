"""DEDUP: normalized-URL exact match (DB + within-run) + recent-title similarity.

Cheapest high-ROI signals first (per the architecture review). Embedding-similarity dedup is a
documented future refinement (requires embeddings to already exist).
"""

from __future__ import annotations

from app.ingestion.text import title_similarity
from app.ingestion.types import PipelineContext, PipelineItem

TITLE_SIM_THRESHOLD = 0.90


def dedup(item: PipelineItem, ctx: PipelineContext) -> PipelineItem:
    # 1) exact normalized-URL, within the current run
    if item.normalized_url in ctx.seen_urls:
        item.dropped = True
        item.drop_reason = "duplicate_url_in_run"
        return item
    ctx.seen_urls.add(item.normalized_url)

    # 2) exact normalized-URL, already in DB
    for _id, _title, nurl in ctx.recent_titles:
        if nurl and nurl == item.normalized_url:
            item.dropped = True
            item.drop_reason = "duplicate_url_db"
            return item

    # 3) near-duplicate title vs recent DB rows (same story from another source)
    for _id, title, _nurl in ctx.recent_titles:
        if title_similarity(item.title, title) >= TITLE_SIM_THRESHOLD:
            item.dropped = True
            item.drop_reason = "duplicate_title"
            return item

    return item

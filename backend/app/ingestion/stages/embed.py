"""EMBED: vector for hybrid retrieval. Failure must NOT block ingestion (backfill later)."""

from __future__ import annotations

from app.core.logging import get_logger
from app.ingestion.types import PipelineContext, PipelineItem

logger = get_logger(__name__)


async def embed(item: PipelineItem, ctx: PipelineContext) -> PipelineItem:
    text = f"{item.title}\n{item.summary or item.excerpt or ''}".strip()
    try:
        item.embedding = await ctx.embedder.embed_one(text)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "embed_failed", extra={"extra": {"url": item.original_url, "error": str(exc)}}
        )
        item.embedding = None  # store without embedding; a later run can backfill
    return item

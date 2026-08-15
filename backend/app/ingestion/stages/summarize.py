"""SUMMARIZE: GameScope AI summary. AI failure must NOT block ingestion."""

from __future__ import annotations

from app.core.logging import get_logger
from app.ingestion.types import PipelineContext, PipelineItem

logger = get_logger(__name__)

_SYSTEM = (
    "You are a concise gaming-news editor. Summarise the item in 1–2 neutral sentences. "
    "No hype, no invented facts, no first person."
)


async def summarize(item: PipelineItem, ctx: PipelineContext) -> PipelineItem:
    source_text = item.excerpt or item.title
    try:
        summary = await ctx.llm.complete(
            system=_SYSTEM,
            user=f"Title: {item.title}\n\nContent: {source_text}",
            temperature=0.2,
            max_tokens=160,
        )
        item.summary = (summary or "").strip() or item.excerpt or None
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        logger.warning(
            "summarize_failed", extra={"extra": {"url": item.original_url, "error": str(exc)}}
        )
        item.summary = item.excerpt or None  # fall back to excerpt; article still stores
    return item

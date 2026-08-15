"""PARSE: RawItem -> PipelineItem (extract common fields)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.errors import ArticleParseError
from app.ingestion.sources.base import RawItem
from app.ingestion.types import PipelineItem


def parse(raw: RawItem) -> PipelineItem:
    if not raw.title or not raw.url:
        raise ArticleParseError("Item missing title or url.")
    return PipelineItem(
        raw=raw,
        title=raw.title.strip(),
        original_url=raw.url.strip(),
        published_at=raw.published_at,
        image_url=raw.image_url,
        fetched_at=datetime.now(UTC),
    )

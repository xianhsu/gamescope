"""CLEAN: HTML-stripped, license-safe excerpt + content hash (idempotency key)."""

from __future__ import annotations

import re

from app.ingestion.text import content_hash, make_excerpt, strip_html
from app.ingestion.types import PipelineItem

_CJK = re.compile(r"[\u4e00-\u9fff]")


def clean(item: PipelineItem) -> PipelineItem:
    raw = item.raw
    body_html = raw.content_html or raw.summary_html or ""
    plain = strip_html(body_html)
    # We deliberately store only a short excerpt, never the full third-party article.
    item.excerpt = make_excerpt(plain, 500)
    if _CJK.search(item.excerpt):
        item.language = "zh"
    item.content_hash = content_hash(item.title, item.excerpt)
    return item

"""NORMALIZE: canonical URL + language guess."""

from __future__ import annotations

import re

from app.ingestion.text import normalize_url
from app.ingestion.types import PipelineItem

_CJK = re.compile(r"[\u4e00-\u9fff]")


def normalize(item: PipelineItem) -> PipelineItem:
    item.normalized_url = normalize_url(item.original_url)
    item.language = "zh" if _CJK.search(item.title) else "en"
    return item

"""CLASSIFY: category, official/rumor flags, platforms, importance — deterministic rules.

Uses source reliability + keyword signals. This is exactly the kind of task the brief says to
keep in code (fast, testable, explainable); the LLM is not needed here.
"""

from __future__ import annotations

import re

from app.ingestion.types import PipelineContext, PipelineItem
from app.models.constants import Category, ReliabilityLevel

_PLATFORM_SIGNALS: list[tuple[str, re.Pattern]] = [
    ("PlayStation", re.compile(r"\b(ps5|ps4|playstation)\b", re.I)),
    ("Xbox", re.compile(r"\b(xbox|game pass|series x|series s)\b", re.I)),
    ("Nintendo", re.compile(r"\b(nintendo|switch)\b", re.I)),
    ("PC", re.compile(r"\b(pc|steam|epic games store|windows)\b", re.I)),
    ("Mobile", re.compile(r"\b(ios|android|mobile)\b", re.I)),
]

_RUMOR = re.compile(r"\b(rumou?r|leak|leaked|reportedly|allegedly|insider)\b|传闻|爆料|疑似", re.I)
_REVIEW = re.compile(r"\breview\b|评测", re.I)
_DEAL = re.compile(r"\b(deal|discount|sale|free|% off)\b|优惠|打折|限免", re.I)
_UPDATE = re.compile(r"\b(update|patch|hotfix|version)\b|更新|补丁", re.I)

_HIGH_SIGNAL = re.compile(
    r"\b(announced|announce|reveal|revealed|release date|launch|trailer|gameplay|"
    r"delay|delayed|shutdown)\b|公布|发布|发售|预告|跳票",
    re.I,
)


def _detect_platforms(text: str) -> list[str]:
    return [name for name, pat in _PLATFORM_SIGNALS if pat.search(text)]


def classify(item: PipelineItem, ctx: PipelineContext) -> PipelineItem:
    text = f"{item.title} {item.excerpt}"
    reliability = ctx.source.reliability_level

    item.is_official = reliability == ReliabilityLevel.OFFICIAL
    item.platforms = _detect_platforms(text)

    if _RUMOR.search(text):
        item.is_rumor = True
        item.category = Category.RUMOR
    elif item.is_official:
        item.category = Category.OFFICIAL
    elif _REVIEW.search(text):
        item.category = Category.REVIEW
    elif _DEAL.search(text):
        item.category = Category.DEAL
    elif _UPDATE.search(text):
        item.category = Category.UPDATE
    else:
        item.category = Category.MEDIA

    # importance in [0,1]: reliability base + signal boost.
    base = {
        ReliabilityLevel.OFFICIAL: 0.6,
        ReliabilityLevel.HIGH: 0.45,
        ReliabilityLevel.MEDIUM: 0.3,
        ReliabilityLevel.LOW: 0.15,
    }.get(reliability, 0.3)
    if _HIGH_SIGNAL.search(text):
        base += 0.25
    if item.is_rumor:
        base -= 0.1
    item.importance_score = round(max(0.0, min(base, 1.0)), 3)
    return item

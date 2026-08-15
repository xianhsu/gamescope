"""Shared dataclasses for the pipeline (kept separate to avoid circular imports)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.ai.embedding.base import EmbeddingProvider
from app.ai.llm.base import LLMProvider
from app.ingestion.sources.base import RawItem
from app.models.game import Game
from app.models.source import Source


@dataclass
class PipelineItem:
    raw: RawItem
    title: str = ""
    original_url: str = ""
    normalized_url: str = ""
    content_hash: str = ""
    excerpt: str = ""
    summary: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    image_url: str | None = None
    language: str = "en"
    category: str = "other"
    is_official: bool = False
    is_rumor: bool = False
    platforms: list[str] = field(default_factory=list)
    importance_score: float = 0.0
    game_matches: list[tuple[int, float]] = field(default_factory=list)  # (game_id, confidence)
    embedding: list[float] | None = None
    dropped: bool = False
    drop_reason: str = ""


@dataclass
class PipelineContext:
    db: object  # AsyncSession
    source: Source
    llm: LLMProvider
    embedder: EmbeddingProvider
    games: list[Game]
    recent_titles: list[tuple[int, str, str]]  # (id, title, normalized_url)
    seen_urls: set[str] = field(default_factory=set)  # within-run dedup

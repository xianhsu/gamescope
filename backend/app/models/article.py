from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin
from app.models.constants import Category

if TYPE_CHECKING:
    from app.models.article_game import ArticleGame
    from app.models.source import Source


class Article(Base, TimestampMixin):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(600), nullable=False)
    slug: Mapped[str] = mapped_column(String(650), unique=True, index=True, nullable=False)

    # GameScope-generated summary (see copyright policy: we do NOT store full articles).
    summary: Mapped[str | None] = mapped_column(Text)
    content_excerpt: Mapped[str | None] = mapped_column(Text)

    original_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    # Canonicalised URL used as the primary dedup key.
    normalized_url: Mapped[str] = mapped_column(String(1000), index=True, nullable=False)
    # Hash of normalized content; gates re-summarize / re-embed (idempotency).
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), index=True, nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    category: Mapped[str] = mapped_column(
        String(16), default=Category.OTHER, index=True, nullable=False
    )
    platforms: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list, nullable=False)

    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_rumor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # True for seed/fixture rows so the UI can honestly badge non-real data.
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    image_url: Mapped[str | None] = mapped_column(String(1000))

    # AI embedding (nullable until the embed stage runs). Dim from settings.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dim))
    # Full-text search vector; maintained by a trigger created in the migration.
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)

    source: Mapped[Source] = relationship(back_populates="articles")
    game_links: Mapped[list[ArticleGame]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )

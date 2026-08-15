from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.constants import ReliabilityLevel, SourceType

if TYPE_CHECKING:
    from app.models.article import Article


class Source(Base, TimestampMixin):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(16), default=SourceType.RSS, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500))
    feed_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reliability_level: Mapped[str] = mapped_column(
        String(16), default=ReliabilityLevel.MEDIUM, nullable=False
    )

    articles: Mapped[list[Article]] = relationship(back_populates="source")

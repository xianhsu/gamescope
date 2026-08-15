from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.article_game import ArticleGame


class Game(Base, TimestampMixin):
    __tablename__ = "game"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, index=True, nullable=False)
    developer: Mapped[str | None] = mapped_column(String(200))
    publisher: Mapped[str | None] = mapped_column(String(200))
    release_date: Mapped[date | None] = mapped_column(Date)
    # Aliases power deterministic entity matching, e.g. ["GTA VI", "GTA 6"].
    aliases: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    article_links: Mapped[list[ArticleGame]] = relationship(back_populates="game")

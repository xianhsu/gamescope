from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.game import Game


class ArticleGame(Base):
    """Many-to-many link between articles and games, with a match confidence."""

    __tablename__ = "article_game"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("article.id", ondelete="CASCADE"), primary_key=True
    )
    game_id: Mapped[int] = mapped_column(
        ForeignKey("game.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    article: Mapped[Article] = relationship(back_populates="game_links")
    game: Mapped[Game] = relationship(back_populates="article_links")

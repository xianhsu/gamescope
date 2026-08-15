from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_game import ArticleGame
from app.models.game import Game


class GameRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, *, offset: int = 0, limit: int = 100) -> tuple[list[Game], int]:
        stmt = select(Game).order_by(Game.name).offset(offset).limit(limit)
        rows = list((await self.db.execute(stmt)).scalars().all())
        total = int((await self.db.execute(select(func.count(Game.id)))).scalar_one())
        return rows, total

    async def get_by_slug(self, slug: str) -> Game | None:
        return (await self.db.execute(select(Game).where(Game.slug == slug))).scalar_one_or_none()

    async def get_all(self) -> list[Game]:
        return list((await self.db.execute(select(Game))).scalars().all())

    async def trending(self, *, limit: int = 8, days: int = 30) -> list[tuple[Game, int]]:
        """Games ranked by recent article volume + importance."""
        from datetime import UTC, datetime, timedelta

        since = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(Game, func.count(Article.id).label("cnt"))
            .join(ArticleGame, ArticleGame.game_id == Game.id)
            .join(Article, Article.id == ArticleGame.article_id)
            .where(Article.published_at >= since)
            .group_by(Game.id)
            .order_by(func.count(Article.id).desc(), func.max(Article.importance_score).desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def article_count(self, game_id: int) -> int:
        stmt = select(func.count(ArticleGame.article_id)).where(ArticleGame.game_id == game_id)
        return int((await self.db.execute(stmt)).scalar_one())

    async def count(self) -> int:
        return int((await self.db.execute(select(func.count(Game.id)))).scalar_one())

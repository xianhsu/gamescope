"""Article data access. No business logic — just queries."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.article_game import ArticleGame
from app.models.game import Game


class ArticleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base_query(self) -> Select:
        return select(Article).options(
            selectinload(Article.source),
            selectinload(Article.game_links).selectinload(ArticleGame.game),
        )

    def _apply_filters(
        self,
        stmt: Select,
        *,
        platform: str | None = None,
        category: str | None = None,
        source_slug: str | None = None,
        game_slug: str | None = None,
        q: str | None = None,
    ) -> Select:
        if platform:
            stmt = stmt.where(Article.platforms.any(platform))
        if category:
            stmt = stmt.where(Article.category == category)
        if source_slug:
            from app.models.source import Source

            stmt = stmt.join(Source, Article.source_id == Source.id).where(
                Source.slug == source_slug
            )
        if game_slug:
            stmt = stmt.where(Article.game_links.any(ArticleGame.game.has(Game.slug == game_slug)))
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(
                or_(func.lower(Article.title).like(like), func.lower(Article.summary).like(like))
            )
        return stmt

    async def list(
        self,
        *,
        offset: int,
        limit: int,
        sort: str = "latest",
        **filters: str | None,
    ) -> tuple[list[Article], int]:
        stmt = self._apply_filters(self._base_query(), **filters)
        count_stmt = self._apply_filters(select(func.count(Article.id.distinct())), **filters)

        if sort == "importance":
            stmt = stmt.order_by(
                Article.importance_score.desc(), Article.published_at.desc().nullslast()
            )
        else:  # latest
            stmt = stmt.order_by(Article.published_at.desc().nullslast(), Article.id.desc())

        stmt = stmt.offset(offset).limit(limit)
        rows = (await self.db.execute(stmt)).unique().scalars().all()
        total = (await self.db.execute(count_stmt)).scalar_one()
        return list(rows), int(total)

    async def get_by_slug(self, slug: str) -> Article | None:
        stmt = self._base_query().where(Article.slug == slug)
        return (await self.db.execute(stmt)).unique().scalar_one_or_none()

    async def get_by_ids(self, ids: list[int]) -> list[Article]:
        if not ids:
            return []
        stmt = self._base_query().where(Article.id.in_(ids))
        rows = (await self.db.execute(stmt)).unique().scalars().all()
        by_id = {a.id: a for a in rows}
        return [by_id[i] for i in ids if i in by_id]  # preserve caller ordering

    async def related(self, article: Article, limit: int = 5) -> list[Article]:
        """Related = shares a game, else same category; newest first, excluding self."""
        game_ids = [link.game_id for link in article.game_links]
        stmt = self._base_query().where(Article.id != article.id)
        if game_ids:
            stmt = stmt.where(Article.game_links.any(ArticleGame.game_id.in_(game_ids)))
        else:
            stmt = stmt.where(Article.category == article.category)
        stmt = stmt.order_by(Article.published_at.desc().nullslast()).limit(limit)
        return list((await self.db.execute(stmt)).unique().scalars().all())

    # --- Ingestion / dedup helpers ---

    async def get_by_normalized_url(self, normalized_url: str) -> Article | None:
        stmt = select(Article).where(Article.normalized_url == normalized_url)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def recent_titles(self, limit: int) -> list[tuple[int, str, str]]:
        stmt = (
            select(Article.id, Article.title, Article.normalized_url)
            .order_by(Article.fetched_at.desc())
            .limit(limit)
        )
        return [tuple(r) for r in (await self.db.execute(stmt)).all()]

    async def count(self) -> int:
        return int((await self.db.execute(select(func.count(Article.id)))).scalar_one())

    async def count_where(self, condition) -> int:
        return int(
            (await self.db.execute(select(func.count(Article.id)).where(condition))).scalar_one()
        )

    async def latest_published_at(self) -> datetime | None:
        return (await self.db.execute(select(func.max(Article.fetched_at)))).scalar_one_or_none()

    async def newest_published_among(self, ids: list[int]) -> datetime | None:
        if not ids:
            return None
        stmt = select(func.max(Article.published_at)).where(Article.id.in_(ids))
        return (await self.db.execute(stmt)).scalar_one_or_none()

"""PostgreSQL full-text retriever using the maintained `search_vector` + ts_rank."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.article_game import ArticleGame
from app.retrieval.base import RetrievalFilters, RetrievedDoc


class FullTextRetriever:
    name = "fts"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def retrieve(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RetrievedDoc]:
        if not query.strip():
            return []
        # 'simple' config is language-agnostic and safe for mixed en/zh queries.
        tsquery = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank(Article.search_vector, tsquery)
        stmt = select(Article.id, rank.label("score")).where(
            Article.search_vector.op("@@")(tsquery)
        )
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(rank.desc()).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        return [
            RetrievedDoc(article_id=r[0], score=float(r[1] or 0.0), retriever=self.name)
            for r in rows
        ]

    @staticmethod
    def _apply_filters(stmt, filters: RetrievalFilters):
        if filters.since:
            stmt = stmt.where(Article.published_at >= filters.since)
        if filters.platform:
            stmt = stmt.where(Article.platforms.any(filters.platform))
        if filters.game_id:
            stmt = stmt.where(Article.game_links.any(ArticleGame.game_id == filters.game_id))
        return stmt

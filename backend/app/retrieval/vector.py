"""pgvector cosine-similarity retriever."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding.base import EmbeddingProvider
from app.models.article import Article
from app.models.article_game import ArticleGame
from app.retrieval.base import RetrievalFilters, RetrievedDoc


class VectorRetriever:
    name = "vector"

    def __init__(self, db: AsyncSession, embedder: EmbeddingProvider) -> None:
        self.db = db
        self.embedder = embedder

    async def retrieve(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RetrievedDoc]:
        if not query.strip():
            return []
        query_vec = await self.embedder.embed_one(query)
        distance = Article.embedding.cosine_distance(query_vec)
        stmt = select(Article.id, distance.label("distance")).where(Article.embedding.is_not(None))
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(distance.asc()).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        # cosine similarity = 1 - cosine distance
        return [
            RetrievedDoc(article_id=r[0], score=1.0 - float(r[1]), retriever=self.name)
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

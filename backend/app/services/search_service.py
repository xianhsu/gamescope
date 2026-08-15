from __future__ import annotations

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.constants import SearchKind
from app.models.search_log import SearchLog
from app.repositories.article_repo import ArticleRepository
from app.retrieval.base import RetrievalFilters
from app.retrieval.fulltext import FullTextRetriever
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.mappers import to_list_item

logger = get_logger(__name__)


class SearchService:
    """Traditional search: Postgres FTS over title/summary (+ game/category via metadata),
    with an ILIKE fallback so results are returned even before FTS vectors are populated."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ArticleRepository(db)
        self.fts = FullTextRetriever(db)

    async def search(self, query: str, *, limit: int = 20) -> SearchResponse:
        started = time.perf_counter()
        query = (query or "").strip()
        if not query:
            return SearchResponse(query=query, total=0, items=[])

        docs = await self.fts.retrieve(query, RetrievalFilters(), limit)
        score_by_id = {d.article_id: d.score for d in docs}
        articles = await self.repo.get_by_ids(list(score_by_id.keys()))

        if not articles:  # FTS empty (e.g. vectors not yet built) — ILIKE fallback
            rows, _ = await self.repo.list(offset=0, limit=limit, q=query)
            articles = rows
            score_by_id = {a.id: 0.0 for a in rows}

        items = [
            SearchResultItem(
                **to_list_item(a).model_dump(), score=round(score_by_id.get(a.id, 0.0), 4)
            )
            for a in articles
        ]

        await self._log(query, len(items), int((time.perf_counter() - started) * 1000))
        return SearchResponse(query=query, total=len(items), items=items)

    async def _log(self, query: str, count: int, latency_ms: int) -> None:
        try:
            self.db.add(
                SearchLog(
                    query=query[:500],
                    kind=SearchKind.KEYWORD,
                    result_count=count,
                    latency_ms=latency_ms,
                )
            )
            await self.db.commit()
        except Exception as exc:  # noqa: BLE001 — analytics must never break search
            logger.warning("search_log_failed", extra={"extra": {"error": str(exc)}})
            await self.db.rollback()

"""AI Search (RAG) orchestration — the project's centerpiece.

Flow (never `question -> LLM -> answer`):
  query understanding -> metadata filter -> FTS + vector retrieval -> (freshness) live
  -> RRF fusion -> hydrate -> rerank -> context builder -> grounded generation -> answer + citations
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import query_understanding as qu
from app.ai.embedding.factory import get_embedding_provider
from app.ai.llm.factory import get_llm_provider
from app.ai.rag import ContextItem, generate_answer
from app.core.config import settings
from app.core.logging import get_logger
from app.models.constants import SearchKind
from app.models.search_log import SearchLog
from app.repositories.article_repo import ArticleRepository
from app.repositories.game_repo import GameRepository
from app.retrieval.base import RetrievalFilters
from app.retrieval.fulltext import FullTextRetriever
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.live import get_live_retriever
from app.retrieval.rerank import rerank
from app.retrieval.vector import VectorRetriever
from app.schemas.ai import (
    AISearchResponse,
    Citation,
    QueryMetadata,
    RelatedArticle,
    RetrievalStats,
)

logger = get_logger(__name__)


class AISearchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.article_repo = ArticleRepository(db)
        self.game_repo = GameRepository(db)
        self.llm = get_llm_provider()
        self.embedder = get_embedding_provider()
        self.fts = FullTextRetriever(db)
        self.vector = VectorRetriever(db, self.embedder)
        self.live = get_live_retriever()

    async def search(self, query: str, language: str | None = None) -> AISearchResponse:
        started = time.perf_counter()

        games = await self.game_repo.get_all()
        aliases = {g.name: list(g.aliases or []) for g in games}
        game_id_by_name = {g.name: g.id for g in games}

        parsed = await qu.understand(query, aliases, self.llm)
        if language:
            parsed.language = language

        game_id = game_id_by_name.get(parsed.game) if parsed.game else None
        filters = RetrievalFilters.from_parsed(
            game_id=game_id, platform=parsed.platform, time_range=parsed.time_range
        )

        fts_docs = await self.fts.retrieve(query, filters, settings.retrieval_fts_limit)
        vec_docs = await self.vector.retrieve(query, filters, settings.retrieval_vector_limit)

        used_live = False
        live_docs: list = []
        if await self._should_use_live(parsed, fts_docs, vec_docs):
            live_docs = await self.live.retrieve(query, filters, 5)
            used_live = len(live_docs) > 0

        fused = reciprocal_rank_fusion(
            [fts_docs, vec_docs, live_docs], k=settings.rrf_k, limit=settings.retrieval_fused_limit
        )

        internal_ids = [d.article_id for d in fused if d.article_id]
        articles = await self.article_repo.get_by_ids(internal_ids)
        by_id = {a.id: a for a in articles}

        reranked = rerank(fused, by_id, limit=settings.retrieval_context_limit)

        items = self._build_context_items(reranked, by_id)
        answer = await generate_answer(self.llm, query, items, parsed.language)

        citations = [
            Citation(
                index=it.index,
                title=it.title,
                source=it.source,
                url=it.url,
                published_at=it.published_at,
                is_official=it.is_official,
                is_rumor=it.is_rumor,
            )
            for it in items
        ]
        related = [
            RelatedArticle(slug=by_id[d.article_id].slug, title=by_id[d.article_id].title)
            for d in reranked
            if d.article_id in by_id
        ][:5]

        meta = QueryMetadata(
            game=parsed.game,
            platform=parsed.platform,
            topic=parsed.topic,
            time_range=parsed.time_range,
            intent=parsed.intent,
            language=parsed.language,
            requires_freshness=parsed.requires_freshness,
            used_live=used_live,
            retrieval=RetrievalStats(
                fts=len(fts_docs),
                vector=len(vec_docs),
                live=len(live_docs),
                fused=len(fused),
                reranked=len(reranked),
            ),
        )

        await self._log(
            query, len(citations), used_live, int((time.perf_counter() - started) * 1000)
        )
        return AISearchResponse(
            answer=answer,
            sources=citations,
            related_articles=related,
            query_metadata=meta,
            generated_at=datetime.now(UTC),
        )

    async def _should_use_live(self, parsed, fts_docs, vec_docs) -> bool:
        """Config-driven freshness gate (thresholds live in settings, not hard-coded).

        - Live disabled entirely -> never.
        - Time-sensitive query (latest/recent/today/最新/最近/…) -> ALWAYS enrich with the
          live web, since the whole point of live retrieval is current information.
        - Otherwise (a non-freshness query) only fall back to live when local coverage is
          thin or stale, to save search-provider quota.
        """
        if not settings.live_retrieval_enabled:
            return False
        if parsed.requires_freshness:
            return True
        local_ids = {d.article_id for d in (*fts_docs, *vec_docs) if d.article_id}
        if len(local_ids) < settings.freshness_min_local_results:
            return True
        # If the freshest local hit is older than the configured window, prefer live.
        newest = await self.article_repo.newest_published_among(list(local_ids))
        if newest is None:
            return True
        cutoff = datetime.now(UTC) - timedelta(hours=settings.freshness_max_age_hours)
        return newest < cutoff

    @staticmethod
    def _build_context_items(reranked, by_id) -> list[ContextItem]:
        items: list[ContextItem] = []
        idx = 1
        for d in reranked:
            if d.article_id and d.article_id in by_id:
                a = by_id[d.article_id]
                items.append(
                    ContextItem(
                        index=idx,
                        title=a.title,
                        source=a.source.name,
                        url=a.original_url,
                        published_at=a.published_at,
                        is_official=a.is_official,
                        is_rumor=a.is_rumor,
                        text=a.summary or a.content_excerpt or a.title,
                    )
                )
                idx += 1
            elif d.external:
                e = d.external
                items.append(
                    ContextItem(
                        index=idx,
                        title=e.get("title", ""),
                        source=e.get("source", "Web"),
                        url=e.get("url", ""),
                        published_at=None,
                        is_official=False,
                        is_rumor=False,
                        text=e.get("snippet", ""),
                    )
                )
                idx += 1
        return items

    async def _log(self, query: str, count: int, used_live: bool, latency_ms: int) -> None:
        try:
            self.db.add(
                SearchLog(
                    query=query[:500],
                    kind=SearchKind.AI,
                    result_count=count,
                    used_live=used_live,
                    latency_ms=latency_ms,
                )
            )
            await self.db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("ai_search_log_failed", extra={"extra": {"error": str(exc)}})
            await self.db.rollback()

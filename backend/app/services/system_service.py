from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.ai.embedding.factory import active_embedding_name
from app.ai.llm.factory import active_llm_name
from app.core.config import settings
from app.core.logging import get_logger
from app.models.article import Article
from app.models.search_log import SearchLog
from app.repositories.article_repo import ArticleRepository
from app.repositories.game_repo import GameRepository
from app.repositories.job_repo import JobRepository
from app.repositories.source_repo import SourceRepository
from app.schemas.system import ComponentStatus, HealthResponse, JobOut, SystemStats

logger = get_logger(__name__)


class SystemService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.articles = ArticleRepository(db)
        self.sources = SourceRepository(db)
        self.games = GameRepository(db)
        self.jobs = JobRepository(db)

    async def health(self) -> HealthResponse:
        components: list[ComponentStatus] = []
        db_ok = True
        try:
            await self.db.execute(text("SELECT 1"))
            components.append(ComponentStatus(name="database", status="ok"))
        except Exception as exc:  # noqa: BLE001
            db_ok = False
            components.append(
                ComponentStatus(name="database", status="down", detail=str(exc)[:120])
            )

        components.append(ComponentStatus(name="search", status="ok" if db_ok else "down"))
        components.append(
            ComponentStatus(name="ai", status="ok", detail=f"llm={active_llm_name()}")
        )

        overall = "ok" if db_ok else "degraded"
        return HealthResponse(
            status=overall,
            version=__version__,
            environment=settings.environment,
            components=components,
        )

    async def stats(self) -> SystemStats:
        """All numbers are computed live from the DB — never fabricated."""
        summarized = await self.articles.count_where(Article.summary.is_not(None))
        embedded = await self.articles.count_where(Article.embedding.is_not(None))
        searches = int((await self.db.execute(select(func.count(SearchLog.id)))).scalar_one())
        return SystemStats(
            articles_total=await self.articles.count(),
            articles_summarized=summarized,
            embeddings_generated=embedded,
            sources_total=await self.sources.count(),
            sources_active=await self.sources.count(active_only=True),
            games_total=await self.games.count(),
            searches_total=searches,
            last_ingest_at=await self.articles.latest_published_at(),
            llm_provider=active_llm_name(),
            embedding_provider=active_embedding_name(),
        )

    async def recent_jobs(self, limit: int = 20) -> list[JobOut]:
        rows = await self.jobs.recent(limit=limit)
        out: list[JobOut] = []
        for job, source_name in rows:
            item = JobOut.model_validate(job)
            item.source_name = source_name
            out.append(item)
        return out

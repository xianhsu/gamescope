"""Pipeline orchestrator for a single source.

Runs FETCH → PARSE → NORMALIZE → CLEAN → DEDUP → CLASSIFY → ENTITIES → SUMMARIZE → EMBED → STORE.
Per-item fault isolation: a failure on one article is logged, counted, and skipped; the run
continues and is marked `partial`. AI (summarize/embed) failures never block basic ingestion.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import SourceFetchError
from app.core.logging import get_logger
from app.ingestion.sources.registry import build_source
from app.ingestion.stages import (
    classify as classify_stage,
)
from app.ingestion.stages import (
    clean as clean_stage,
)
from app.ingestion.stages import (
    dedup as dedup_stage,
)
from app.ingestion.stages import (
    embed as embed_stage,
)
from app.ingestion.stages import (
    entities as entities_stage,
)
from app.ingestion.stages import (
    normalize as normalize_stage,
)
from app.ingestion.stages import (
    parse as parse_stage,
)
from app.ingestion.stages import (
    store as store_stage,
)
from app.ingestion.stages import (
    summarize as summarize_stage,
)
from app.ingestion.types import PipelineContext
from app.models.constants import JobStatus
from app.models.game import Game
from app.models.processing_job import ProcessingJob
from app.models.source import Source
from app.repositories.article_repo import ArticleRepository

logger = get_logger(__name__)


async def run_source(
    db: AsyncSession,
    source: Source,
    *,
    llm,
    embedder,
    games: list[Game],
    max_items: int | None = None,
) -> ProcessingJob:
    max_items = max_items or settings.ingest_max_items_per_source
    job = ProcessingJob(source_id=source.id, status=JobStatus.RUNNING, started_at=datetime.now(UTC))
    db.add(job)
    await db.commit()
    await db.refresh(job)

    recent = await ArticleRepository(db).recent_titles(settings.ingest_dedup_lookback)
    ctx = PipelineContext(
        db=db, source=source, llm=llm, embedder=embedder, games=games, recent_titles=list(recent)
    )

    provider = build_source(
        slug=source.slug,
        name=source.name,
        feed_url=source.feed_url or "",
        base_url=source.base_url or "",
        type=source.type,
        reliability_level=source.reliability_level,
    )

    found = stored = failed = 0
    try:
        raw_items = await provider.fetch(max_items)
        found = len(raw_items)
    except SourceFetchError as exc:
        job.status = JobStatus.FAILED
        job.error = str(exc)[:500]
        job.finished_at = datetime.now(UTC)
        await db.commit()
        return job

    for raw in raw_items:
        try:
            item = parse_stage.parse(raw)
            item = normalize_stage.normalize(item)
            item = clean_stage.clean(item)
            item = dedup_stage.dedup(item, ctx)
            if item.dropped:
                continue
            item = classify_stage.classify(item, ctx)
            item = entities_stage.extract_entities(item, ctx)
            item = await summarize_stage.summarize(item, ctx)
            item = await embed_stage.embed(item, ctx)
            await store_stage.store(item, ctx)
            await db.commit()  # commit per item → true fault isolation
            stored += 1
        except Exception as exc:  # noqa: BLE001 — one bad item must not kill the run
            failed += 1
            await db.rollback()
            logger.warning(
                "article_pipeline_failed",
                extra={"extra": {"url": getattr(raw, "url", ""), "error": str(exc)}},
            )

    job.articles_found = found
    job.articles_stored = stored
    job.articles_failed = failed
    job.status = JobStatus.SUCCESS if failed == 0 else JobStatus.PARTIAL
    job.finished_at = datetime.now(UTC)
    await db.commit()
    logger.info(
        "source_ingested",
        extra={
            "extra": {"source": source.slug, "found": found, "stored": stored, "failed": failed}
        },
    )
    return job

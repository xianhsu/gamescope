from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_job import ProcessingJob
from app.models.source import Source


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def recent(self, limit: int = 20) -> list[tuple[ProcessingJob, str | None]]:
        stmt = (
            select(ProcessingJob, Source.name)
            .outerjoin(Source, Source.id == ProcessingJob.source_id)
            .order_by(ProcessingJob.started_at.desc())
            .limit(limit)
        )
        return [(row[0], row[1]) for row in (await self.db.execute(stmt)).all()]

    async def add(self, job: ProcessingJob) -> ProcessingJob:
        self.db.add(job)
        await self.db.flush()
        return job

    async def count(self) -> int:
        return int((await self.db.execute(select(func.count(ProcessingJob.id)))).scalar_one())

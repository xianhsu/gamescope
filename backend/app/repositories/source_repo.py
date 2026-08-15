from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source


class SourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, *, active_only: bool = False) -> list[Source]:
        stmt = select(Source)
        if active_only:
            stmt = stmt.where(Source.is_active.is_(True))
        return list((await self.db.execute(stmt.order_by(Source.name))).scalars().all())

    async def get_by_slug(self, slug: str) -> Source | None:
        return (
            await self.db.execute(select(Source).where(Source.slug == slug))
        ).scalar_one_or_none()

    async def count(self, *, active_only: bool = False) -> int:
        stmt = select(func.count(Source.id))
        if active_only:
            stmt = stmt.where(Source.is_active.is_(True))
        return int((await self.db.execute(stmt)).scalar_one())

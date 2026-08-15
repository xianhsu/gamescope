from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.system import JobOut, SystemStats
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/stats", response_model=SystemStats, summary="Real pipeline statistics")
async def system_stats(db: DbSession) -> SystemStats:
    return await SystemService(db).stats()


@router.get("/jobs", response_model=list[JobOut], summary="Recent processing jobs")
async def system_jobs(db: DbSession, limit: int = Query(20, ge=1, le=100)) -> list[JobOut]:
    return await SystemService(db).recent_jobs(limit=limit)

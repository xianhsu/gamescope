from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.system import HealthResponse
from app.services.system_service import SystemService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness + dependency readiness")
async def health(db: DbSession) -> HealthResponse:
    return await SystemService(db).health()

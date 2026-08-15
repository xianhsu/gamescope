from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse, summary="Traditional keyword search")
async def search(
    db: DbSession,
    q: str = Query(..., min_length=1, description="Search over title/summary/game/category"),
    limit: int = Query(20, ge=1, le=50),
) -> SearchResponse:
    return await SearchService(db).search(q, limit=limit)

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.ai import AISearchRequest, AISearchResponse
from app.services.ai_search_service import AISearchService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/search", response_model=AISearchResponse, summary="Grounded RAG answer + citations")
async def ai_search(db: DbSession, payload: AISearchRequest) -> AISearchResponse:
    return await AISearchService(db).search(payload.query, payload.language)

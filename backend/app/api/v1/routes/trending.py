from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.game import GameWithCount
from app.services.game_service import GameService

router = APIRouter(tags=["trending"])


@router.get("/trending", response_model=list[GameWithCount], summary="Trending / featured games")
async def trending(db: DbSession, limit: int = Query(8, ge=1, le=20)) -> list[GameWithCount]:
    return await GameService(db).trending(limit=limit)

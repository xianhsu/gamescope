from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession, Pagination
from app.core.pagination import Page
from app.schemas.article import ArticleListItem
from app.schemas.game import GameOut, GameWithCount
from app.services.game_service import GameService
from app.services.news_service import NewsService

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=list[GameOut], summary="List games")
async def list_games(db: DbSession) -> list[GameOut]:
    return await GameService(db).list_games()


@router.get("/{slug}", response_model=GameWithCount, summary="Game detail")
async def get_game(db: DbSession, slug: str) -> GameWithCount:
    return await GameService(db).get_game(slug)


@router.get("/{slug}/news", response_model=Page[ArticleListItem], summary="News for a game")
async def game_news(db: DbSession, slug: str, params: Pagination) -> Page[ArticleListItem]:
    return await NewsService(db).list_news(params, game_slug=slug)

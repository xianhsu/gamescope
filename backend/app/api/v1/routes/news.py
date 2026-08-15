from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession, Pagination
from app.core.pagination import Page
from app.schemas.article import ArticleDetail, ArticleListItem
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=Page[ArticleListItem], summary="List news (paginated, filterable)")
async def list_news(
    db: DbSession,
    params: Pagination,
    platform: str | None = Query(None, description="PC | PlayStation | Xbox | Nintendo | Mobile"),
    category: str | None = Query(
        None, description="official | media | rumor | update | review | deal"
    ),
    source: str | None = Query(None, description="source slug"),
    game: str | None = Query(None, description="game slug"),
    q: str | None = Query(None, description="quick text filter over title/summary"),
    sort: str = Query("latest", pattern="^(latest|importance)$"),
) -> Page[ArticleListItem]:
    return await NewsService(db).list_news(
        params,
        platform=platform,
        category=category,
        source_slug=source,
        game_slug=game,
        q=q,
        sort=sort,
    )


@router.get("/{slug}", response_model=ArticleDetail, summary="Article detail + related")
async def get_news(db: DbSession, slug: str) -> ArticleDetail:
    return await NewsService(db).get_detail(slug)

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams
from app.repositories.article_repo import ArticleRepository
from app.schemas.article import ArticleDetail, ArticleListItem
from app.services.mappers import to_detail, to_list_item


class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ArticleRepository(db)

    async def list_news(
        self,
        params: PageParams,
        *,
        platform: str | None = None,
        category: str | None = None,
        source_slug: str | None = None,
        game_slug: str | None = None,
        q: str | None = None,
        sort: str = "latest",
    ) -> Page[ArticleListItem]:
        rows, total = await self.repo.list(
            offset=params.offset,
            limit=params.limit,
            sort=sort,
            platform=platform,
            category=category,
            source_slug=source_slug,
            game_slug=game_slug,
            q=q,
        )
        return Page.create([to_list_item(a) for a in rows], total, params)

    async def get_detail(self, slug: str) -> ArticleDetail:
        article = await self.repo.get_by_slug(slug)
        if article is None:
            raise NotFoundError(f"Article '{slug}' not found.")
        related = await self.repo.related(article, limit=5)
        return to_detail(article, related)

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.article import ArticleListItem


class SearchResultItem(ArticleListItem):
    score: float = 0.0


class SearchResponse(BaseModel):
    query: str
    total: int
    items: list[SearchResultItem]

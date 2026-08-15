from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.game import GameOut
from app.schemas.source import SourceOut


class ArticleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str | None = None
    original_url: str
    image_url: str | None = None
    published_at: datetime | None = None
    language: str
    category: str
    platforms: list[str] = []
    is_official: bool
    is_rumor: bool
    is_sample: bool = False
    importance_score: float


class ArticleListItem(ArticleBase):
    source: SourceOut
    games: list[GameOut] = []


class ArticleDetail(ArticleBase):
    content_excerpt: str | None = None
    fetched_at: datetime
    source: SourceOut
    games: list[GameOut] = []
    related: list[ArticleListItem] = []

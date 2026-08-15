from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AISearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    language: str | None = Field(None, description="Answer language hint: 'en' | 'zh'")


class Citation(BaseModel):
    index: int
    title: str
    source: str
    url: str
    published_at: datetime | None = None
    is_official: bool = False
    is_rumor: bool = False


class RelatedArticle(BaseModel):
    slug: str
    title: str


class RetrievalStats(BaseModel):
    fts: int = 0
    vector: int = 0
    live: int = 0
    fused: int = 0
    reranked: int = 0


class QueryMetadata(BaseModel):
    game: str | None = None
    platform: str | None = None
    topic: str | None = None
    time_range: str | None = None
    intent: str | None = None
    language: str = "en"
    requires_freshness: bool = False
    used_live: bool = False
    retrieval: RetrievalStats = RetrievalStats()


class AISearchResponse(BaseModel):
    answer: str
    sources: list[Citation] = []
    related_articles: list[RelatedArticle] = []
    query_metadata: QueryMetadata
    generated_at: datetime

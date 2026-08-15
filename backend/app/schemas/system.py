from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComponentStatus(BaseModel):
    name: str
    status: str  # "ok" | "degraded" | "down"
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    version: str
    environment: str
    components: list[ComponentStatus]


class SystemStats(BaseModel):
    articles_total: int
    articles_summarized: int
    embeddings_generated: int
    sources_total: int
    sources_active: int
    games_total: int
    searches_total: int
    last_ingest_at: datetime | None = None
    # AI configuration surfaced honestly (which provider is actually active).
    llm_provider: str
    embedding_provider: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int | None = None
    source_name: str | None = None
    status: str
    articles_found: int
    articles_stored: int
    articles_failed: int
    started_at: datetime
    finished_at: datetime | None = None

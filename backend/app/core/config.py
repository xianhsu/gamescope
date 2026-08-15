"""Centralised application settings.

All configuration is read from the environment (12-factor). Nothing secret is hard-coded.
Thresholds that the brief asked us NOT to hard-code (freshness, retrieval limits) live here.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- Core ---
    environment: str = "development"
    log_level: str = "INFO"
    app_name: str = "GameScope API"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str | None = None
    postgres_user: str = "gamescope"
    postgres_password: str = "gamescope"
    postgres_db: str = "gamescope"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- LLM provider ---
    llm_provider: str = "local"  # local | openai
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""

    # --- Embedding provider ---
    embedding_provider: str = "local"  # local | openai
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # --- Retrieval / freshness ---
    retrieval_fts_limit: int = 15
    retrieval_vector_limit: int = 15
    retrieval_fused_limit: int = 20
    retrieval_context_limit: int = 8
    rrf_k: int = 60
    live_retrieval_enabled: bool = False
    # Which live web provider to use when live retrieval is enabled: "null" | "serpapi".
    live_retrieval_provider: str = "null"
    serpapi_api_key: str = ""
    freshness_max_age_hours: int = 48
    freshness_min_local_results: int = 3

    # --- Ingestion ---
    ingest_http_timeout: float = 20.0
    ingest_max_items_per_source: int = 40
    ingest_dedup_lookback: int = 500

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Async SQLAlchemy URI. Explicit DATABASE_URL wins; otherwise assembled from parts."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

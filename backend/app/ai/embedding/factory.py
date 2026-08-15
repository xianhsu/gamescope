from __future__ import annotations

from functools import lru_cache

from app.ai.embedding.base import EmbeddingProvider
from app.ai.embedding.local_embedding import LocalEmbeddingProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider.lower() == "openai" and settings.llm_api_key:
        from app.ai.embedding.openai_embedding import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            api_key=settings.llm_api_key,
            model=settings.embedding_model,
            dim=settings.embedding_dim,
            base_url=settings.llm_base_url or None,
        )
    if settings.embedding_provider.lower() == "openai":
        logger.warning(
            "embedding_falling_back_to_local", extra={"extra": {"reason": "no LLM_API_KEY"}}
        )
    return LocalEmbeddingProvider(dim=settings.embedding_dim)


def active_embedding_name() -> str:
    return get_embedding_provider().name

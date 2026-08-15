"""Build the active LLM provider from settings.

Rule: if provider=openai AND a key is present, use OpenAIProvider; otherwise fall back to
LocalProvider. This guarantees the app always has a working provider and never crashes for
lack of a key. `active_llm_name()` reports the *actual* provider for honest /system stats.
"""

from __future__ import annotations

from functools import lru_cache

from app.ai.llm.base import LLMProvider
from app.ai.llm.local_provider import LocalProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_llm_provider() -> LLMProvider:
    if settings.llm_provider.lower() == "openai" and settings.llm_api_key:
        from app.ai.llm.openai_provider import OpenAIProvider

        logger.info(
            "llm_provider_selected",
            extra={"extra": {"provider": "openai", "model": settings.llm_model}},
        )
        return OpenAIProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url or None,
        )
    if settings.llm_provider.lower() == "openai":
        logger.warning("llm_falling_back_to_local", extra={"extra": {"reason": "no LLM_API_KEY"}})
    return LocalProvider()


def active_llm_name() -> str:
    return get_llm_provider().name

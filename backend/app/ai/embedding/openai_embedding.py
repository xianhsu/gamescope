from __future__ import annotations

from app.ai.embedding.base import EmbeddingProvider
from app.core.errors import EmbeddingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, dim: int, base_url: str | None = None) -> None:
        from openai import AsyncOpenAI

        self.model = model
        self.dim = dim
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url or None)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = await self._client.embeddings.create(model=self.model, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as exc:  # noqa: BLE001
            logger.warning("embedding_provider_error", extra={"extra": {"error": str(exc)}})
            raise EmbeddingError("Failed to generate embeddings.") from exc

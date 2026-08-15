"""OpenAI-compatible chat provider.

Works with OpenAI and any compatible gateway (DeepSeek, Qwen dashscope compat mode, etc.)
by setting LLM_BASE_URL + LLM_MODEL + LLM_API_KEY.
"""

from __future__ import annotations

from app.ai.llm.base import LLMProvider
from app.core.errors import AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        from openai import AsyncOpenAI

        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url or None)

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        kwargs: dict = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = await self._client.chat.completions.create(**kwargs)
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001 — normalize to our error model
            logger.warning("openai_provider_error", extra={"extra": {"error": str(exc)}})
            raise AIProviderError("The AI provider returned an error.") from exc

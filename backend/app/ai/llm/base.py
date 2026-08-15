"""LLM provider abstraction.

The interface is deliberately tiny: one `complete()` call. Concrete providers:
  - OpenAIProvider : any OpenAI-compatible endpoint (OpenAI / DeepSeek / Qwen via base_url)
  - LocalProvider  : deterministic, no network, no key — makes the system runnable + testable

This keeps the business logic (RAG, query understanding) independent of any vendor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        """Return the model's text completion for a system+user prompt."""
        raise NotImplementedError

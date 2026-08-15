"""Deterministic, no-network LLM provider.

Purpose: make GameScope fully runnable and testable **without any API key**.
It does extractive summarisation for the summarize stage and returns empty JSON for
query-understanding fallback (so the deterministic rule-based parser dominates).

The RAG service uses a dedicated extractive path for local mode (see ai/rag.py) so that
AI Search still returns a *grounded, cited* answer with no external dependency.
"""

from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


from app.ai.llm.base import LLMProvider  # noqa: E402


class LocalProvider(LLMProvider):
    name = "local"

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        if json_mode:
            # Let the deterministic rule-based parser own query understanding.
            return "{}"
        # Extractive summary: keep the first 1–2 informative sentences.
        sentences = split_sentences(user)
        if not sentences:
            return ""
        summary = " ".join(sentences[:2])
        return summary[:400]

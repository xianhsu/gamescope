"""Pluggable live-web retriever.

v1 ships a NullLiveRetriever (returns nothing) so the retrieval contract and freshness logic
are fully exercised without binding the business to any search vendor. A real provider (Tavily,
Bing, SerpAPI, …) can be dropped in behind this same interface with no changes to the AI Search
service. Enable via LIVE_RETRIEVAL_ENABLED + a concrete implementation.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.retrieval.base import RetrievalFilters, RetrievedDoc

logger = get_logger(__name__)


class NullLiveRetriever:
    name = "live"

    async def retrieve(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RetrievedDoc]:
        logger.info("live_retrieval_noop", extra={"extra": {"query": query}})
        return []


def get_live_retriever():
    """Factory hook. Return a concrete provider when configured; else the null retriever."""
    return NullLiveRetriever()

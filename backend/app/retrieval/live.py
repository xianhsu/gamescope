"""Pluggable live-web retriever.

v1 shipped a NullLiveRetriever (returns nothing) so the retrieval contract and freshness logic
were fully exercised without binding the business to any search vendor. A real provider
(SerpAPI, Bing, Brave, Tavily, …) drops in behind the same `retrieve()` interface — the AI
Search service, RRF fusion, and citation/RAG builders never change.

Enable via env:
  LIVE_RETRIEVAL_ENABLED=true
  LIVE_RETRIEVAL_PROVIDER=serpapi
  SERPAPI_API_KEY=<your key>      # read from env/.env — never hard-coded, never committed

Live results carry their payload in `RetrievedDoc.external` so the rest of the pipeline can
surface them as cited web sources without a database row.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.retrieval.base import RetrievalFilters, RetrievedDoc

logger = get_logger(__name__)

# Map our coarse time ranges to SerpAPI's `tbs` recency filter.
# (SerpAPI only supports h/d/w/m/y granularity.)
_TBS_BY_RANGE = {
    "1d": "qdr:d",
    "7d": "qdr:w",
    "14d": "qdr:w",
    "30d": "qdr:m",
    "90d": "qdr:m",
}

_TIMEOUT_SECONDS = 8.0


class SerpAPILiveRetriever:
    """Queries Google via SerpAPI and maps organic results into RetrievedDocs."""

    name = "live"
    endpoint = "https://serpapi.com/search.json"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def retrieve(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RetrievedDoc]:
        q = f"{query} {filters.platform}".strip() if filters.platform else query
        params = {
            "engine": "google",
            "q": q,
            "api_key": self.api_key,
            "num": max(int(limit), 5),
            "hl": "en",
        }
        tbs = _TBS_BY_RANGE.get((filters.time_range or "").lower())
        if tbs:
            params["tbs"] = tbs

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                resp = await client.get(self.endpoint, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            # Never let a search-provider failure break the whole AI Search response.
            logger.warning("serpapi_request_failed", extra={"extra": {"error": str(exc)}})
            return []
        except Exception as exc:  # noqa: BLE001
            logger.warning("serpapi_unexpected_error", extra={"extra": {"error": str(exc)}})
            return []

        results = data.get("organic_results") or []
        docs: list[RetrievedDoc] = []
        for rank, r in enumerate(results[: int(limit)]):
            url = r.get("link") or ""
            if not url:
                continue
            docs.append(
                RetrievedDoc(
                    article_id=0,  # external results have no DB id
                    score=max(0.0, 1.0 - rank * 0.05),
                    retriever=self.name,
                    external={
                        "title": r.get("title", ""),
                        "source": r.get("source") or "Web",
                        "url": url,
                        "snippet": r.get("snippet")
                        or (r.get("snippet_highlighted_words") or ""),
                    },
                )
            )
        logger.info("serpapi_retrieved", extra={"extra": {"query": q, "count": len(docs)}})
        return docs


class NullLiveRetriever:
    name = "live"

    async def retrieve(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RetrievedDoc]:
        logger.info("live_retrieval_noop", extra={"extra": {"query": query}})
        return []


def get_live_retriever():
    """Factory hook. Return a concrete provider when configured; else the null retriever.

    Selection is config-driven so no business logic changes when swapping providers:
      LIVE_RETRIEVAL_PROVIDER=serpapi + SERPAPI_API_KEY set  -> SerpAPILiveRetriever
      anything else (including a missing key)                -> NullLiveRetriever (safe no-op)
    """
    if settings.live_retrieval_provider.lower() == "serpapi" and settings.serpapi_api_key:
        return SerpAPILiveRetriever(api_key=settings.serpapi_api_key)
    return NullLiveRetriever()

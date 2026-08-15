"""Retrieval contracts.

Every retriever implements the same `retrieve()` interface and returns `RetrievedDoc`s.
This lets the AI Search service treat internal FTS, vector, and (pluggable) live-web retrieval
uniformly, and fuse them with RRF — no retriever is special-cased in the business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol

_TIME_RANGE_DAYS = {"1d": 1, "7d": 7, "14d": 14, "30d": 30, "90d": 90}


@dataclass
class RetrievalFilters:
    game_id: int | None = None
    platform: str | None = None
    since: datetime | None = None
    # Original time-range token (e.g. "7d"); live retrievers map it to provider recency filters.
    time_range: str | None = None

    @classmethod
    def from_parsed(cls, *, game_id: int | None, platform: str | None, time_range: str | None):
        since = None
        if time_range in _TIME_RANGE_DAYS:
            since = datetime.now(UTC) - timedelta(days=_TIME_RANGE_DAYS[time_range])
        return cls(game_id=game_id, platform=platform, since=since, time_range=time_range)


@dataclass
class RetrievedDoc:
    article_id: int
    score: float
    retriever: str
    # Live results have no DB id; they carry their own payload for citation.
    external: dict | None = None


@dataclass
class RetrievalResult:
    docs: list[RetrievedDoc] = field(default_factory=list)
    name: str = ""


class Retriever(Protocol):
    name: str

    async def retrieve(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RetrievedDoc]: ...

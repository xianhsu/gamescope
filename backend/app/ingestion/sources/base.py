"""NewsSource provider pattern.

Adding a new source means writing a NewsSource subclass — the pipeline never changes.
`RawItem` is the common shape every source produces regardless of underlying protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawItem:
    title: str
    url: str
    source_slug: str
    summary_html: str = ""
    content_html: str = ""
    published_at: datetime | None = None
    image_url: str | None = None
    raw: dict = field(default_factory=dict)


class NewsSource(ABC):
    slug: str
    name: str
    type: str = "rss"
    reliability_level: str = "medium"

    @abstractmethod
    async def fetch(self, limit: int) -> list[RawItem]:
        """Fetch up to `limit` recent items. Should raise SourceFetchError on network failure."""
        raise NotImplementedError

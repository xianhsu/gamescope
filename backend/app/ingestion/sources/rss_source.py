"""RSS/Atom source. Covers the majority of official + media gaming feeds."""

from __future__ import annotations

from datetime import UTC, datetime
from time import mktime

import feedparser
import httpx

from app.core.errors import SourceFetchError
from app.core.logging import get_logger
from app.ingestion.sources.base import NewsSource, RawItem

logger = get_logger(__name__)


class RSSSource(NewsSource):
    type = "rss"

    def __init__(
        self,
        slug: str,
        name: str,
        feed_url: str,
        base_url: str = "",
        reliability_level: str = "medium",
        timeout: float = 20.0,
    ) -> None:
        self.slug = slug
        self.name = name
        self.feed_url = feed_url
        self.base_url = base_url
        self.reliability_level = reliability_level
        self.timeout = timeout

    async def fetch(self, limit: int) -> list[RawItem]:
        headers = {"User-Agent": "GameScopeBot/0.1 (+https://github.com/gamescope)"}
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=headers, follow_redirects=True
            ) as client:
                resp = await client.get(self.feed_url)
                resp.raise_for_status()
                body = resp.content
        except httpx.HTTPError as exc:
            logger.warning(
                "source_fetch_failed", extra={"extra": {"source": self.slug, "error": str(exc)}}
            )
            raise SourceFetchError(f"Failed to fetch {self.slug}: {exc}") from exc

        parsed = feedparser.parse(body)
        items: list[RawItem] = []
        for entry in parsed.entries[:limit]:
            items.append(
                RawItem(
                    title=(entry.get("title") or "").strip(),
                    url=(entry.get("link") or "").strip(),
                    source_slug=self.slug,
                    summary_html=entry.get("summary", ""),
                    content_html=self._entry_content(entry),
                    published_at=self._entry_time(entry),
                    image_url=self._entry_image(entry),
                    raw={"id": entry.get("id", "")},
                )
            )
        logger.info("source_fetched", extra={"extra": {"source": self.slug, "items": len(items)}})
        return items

    @staticmethod
    def _entry_content(entry) -> str:
        if entry.get("content"):
            return entry["content"][0].get("value", "")
        return entry.get("summary", "")

    @staticmethod
    def _entry_time(entry) -> datetime | None:
        for key in ("published_parsed", "updated_parsed"):
            t = entry.get(key)
            if t:
                return datetime.fromtimestamp(mktime(t), tz=UTC)
        return None

    @staticmethod
    def _entry_image(entry) -> str | None:
        media = entry.get("media_content") or entry.get("media_thumbnail")
        if media and isinstance(media, list) and media[0].get("url"):
            return media[0]["url"]
        for link in entry.get("links", []):
            if link.get("type", "").startswith("image"):
                return link.get("href")
        return None

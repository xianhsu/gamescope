"""Source + game seed definitions and the source builder.

Sources are a curated 5–8 (per the brief): a mix of official studio/platform feeds and a few
stable media outlets, all via public RSS. Adding one is a one-line dict — no pipeline changes.
"""

from __future__ import annotations

from app.core.config import settings
from app.ingestion.sources.base import NewsSource
from app.ingestion.sources.rss_source import RSSSource
from app.models.constants import ReliabilityLevel, SourceType

# slug, name, feed_url, base_url, reliability, type
SOURCE_DEFS: list[dict] = [
    {
        "slug": "playstation-blog",
        "name": "PlayStation Blog",
        "feed_url": "https://blog.playstation.com/feed/",
        "base_url": "https://blog.playstation.com",
        "reliability": ReliabilityLevel.OFFICIAL,
        "type": SourceType.RSS,
    },
    {
        "slug": "xbox-wire",
        "name": "Xbox Wire",
        "feed_url": "https://news.xbox.com/en-us/feed/",
        "base_url": "https://news.xbox.com",
        "reliability": ReliabilityLevel.OFFICIAL,
        "type": SourceType.RSS,
    },
    {
        "slug": "nintendo-life",
        "name": "Nintendo Life",
        "feed_url": "https://www.nintendolife.com/feeds/latest",
        "base_url": "https://www.nintendolife.com",
        "reliability": ReliabilityLevel.HIGH,
        "type": SourceType.RSS,
    },
    {
        "slug": "pc-gamer",
        "name": "PC Gamer",
        "feed_url": "https://www.pcgamer.com/rss/",
        "base_url": "https://www.pcgamer.com",
        "reliability": ReliabilityLevel.HIGH,
        "type": SourceType.RSS,
    },
    {
        "slug": "ign",
        "name": "IGN",
        "feed_url": "https://feeds.ign.com/ign/all",
        "base_url": "https://www.ign.com",
        "reliability": ReliabilityLevel.HIGH,
        "type": SourceType.RSS,
    },
    {
        "slug": "eurogamer",
        "name": "Eurogamer",
        "feed_url": "https://www.eurogamer.net/feed",
        "base_url": "https://www.eurogamer.net",
        "reliability": ReliabilityLevel.HIGH,
        "type": SourceType.RSS,
    },
    {
        "slug": "rock-paper-shotgun",
        "name": "Rock Paper Shotgun",
        "feed_url": "https://www.rockpapershotgun.com/feed",
        "base_url": "https://www.rockpapershotgun.com",
        "reliability": ReliabilityLevel.HIGH,
        "type": SourceType.RSS,
    },
]

# name, slug, developer, publisher, aliases
GAME_SEED: list[dict] = [
    {
        "name": "Grand Theft Auto VI",
        "slug": "grand-theft-auto-vi",
        "developer": "Rockstar Games",
        "publisher": "Rockstar Games",
        "aliases": ["GTA VI", "GTA 6", "GTA6", "GTA Six"],
    },
    {
        "name": "Monster Hunter Wilds",
        "slug": "monster-hunter-wilds",
        "developer": "Capcom",
        "publisher": "Capcom",
        "aliases": ["Monster Hunter", "MH Wilds", "MHWilds"],
    },
    {
        "name": "Battlefield",
        "slug": "battlefield",
        "developer": "DICE",
        "publisher": "Electronic Arts",
        "aliases": ["Battlefield 6", "BF6", "Battlefield 2042"],
    },
    {
        "name": "The Legend of Zelda",
        "slug": "the-legend-of-zelda",
        "developer": "Nintendo",
        "publisher": "Nintendo",
        "aliases": ["Zelda", "Tears of the Kingdom", "TOTK"],
    },
    {
        "name": "Elden Ring",
        "slug": "elden-ring",
        "developer": "FromSoftware",
        "publisher": "Bandai Namco",
        "aliases": ["Shadow of the Erdtree", "Elden Ring Nightreign"],
    },
    {
        "name": "Call of Duty",
        "slug": "call-of-duty",
        "developer": "Activision",
        "publisher": "Activision",
        "aliases": ["COD", "Modern Warfare", "Black Ops"],
    },
    {
        "name": "Cyberpunk 2077",
        "slug": "cyberpunk-2077",
        "developer": "CD Projekt Red",
        "publisher": "CD Projekt",
        "aliases": ["Cyberpunk"],
    },
    {
        "name": "Starfield",
        "slug": "starfield",
        "developer": "Bethesda Game Studios",
        "publisher": "Bethesda Softworks",
        "aliases": [],
    },
    {
        "name": "Marvel's Spider-Man 2",
        "slug": "marvels-spider-man-2",
        "developer": "Insomniac Games",
        "publisher": "Sony Interactive Entertainment",
        "aliases": ["Spider-Man 2", "Spiderman 2"],
    },
    {
        "name": "Hollow Knight: Silksong",
        "slug": "hollow-knight-silksong",
        "developer": "Team Cherry",
        "publisher": "Team Cherry",
        "aliases": ["Silksong"],
    },
]


def build_source(
    *,
    slug: str,
    name: str,
    feed_url: str,
    base_url: str = "",
    type: str = SourceType.RSS,
    reliability_level: str = ReliabilityLevel.MEDIUM,
) -> NewsSource:
    if type == SourceType.RSS:
        return RSSSource(
            slug=slug,
            name=name,
            feed_url=feed_url,
            base_url=base_url,
            reliability_level=reliability_level,
            timeout=settings.ingest_http_timeout,
        )
    raise NotImplementedError(f"Source type '{type}' not implemented yet (Provider pattern hook).")

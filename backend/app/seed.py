"""Idempotent seeding: sources, games, and clearly-labeled sample articles.

Sample articles carry `is_sample=True` so the UI can badge them honestly. Run real ingestion
(`python -m app.ingestion.runner`) to add real articles alongside or instead of samples.

Usage:  python -m app.seed            # sources + games + sample articles
        python -m app.seed --no-samples
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding.factory import get_embedding_provider
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.ingestion.sources.registry import GAME_SEED, SOURCE_DEFS
from app.ingestion.text import content_hash, make_excerpt, normalize_url, slugify
from app.models.article import Article
from app.models.article_game import ArticleGame
from app.models.game import Game
from app.models.source import Source

logger = get_logger("seed")


async def ensure_sources(db: AsyncSession) -> dict[str, Source]:
    existing = {s.slug: s for s in (await db.execute(select(Source))).scalars().all()}
    for d in SOURCE_DEFS:
        if d["slug"] not in existing:
            src = Source(
                name=d["name"],
                slug=d["slug"],
                type=d["type"],
                base_url=d["base_url"],
                feed_url=d["feed_url"],
                is_active=True,
                reliability_level=d["reliability"],
            )
            db.add(src)
            existing[d["slug"]] = src
    await db.commit()
    return {s.slug: s for s in (await db.execute(select(Source))).scalars().all()}


async def ensure_games(db: AsyncSession) -> dict[str, Game]:
    existing = {g.slug: g for g in (await db.execute(select(Game))).scalars().all()}
    for d in GAME_SEED:
        if d["slug"] not in existing:
            db.add(
                Game(
                    name=d["name"],
                    slug=d["slug"],
                    developer=d["developer"],
                    publisher=d["publisher"],
                    aliases=d["aliases"],
                )
            )
    await db.commit()
    return {g.slug: g for g in (await db.execute(select(Game))).scalars().all()}


# Clearly-fictional-but-plausible sample stories. Marked is_sample=True.
_SAMPLES: list[dict] = [
    {
        "title": "Grand Theft Auto VI second trailer breaks viewing records in first 24 hours",
        "source": "ign",
        "game": "grand-theft-auto-vi",
        "url": "https://www.ign.com/articles/gta-6-trailer-2-records",
        "official": False,
        "rumor": False,
        "platforms": ["PlayStation", "Xbox"],
        "days": 1,
        "excerpt": (
            "Rockstar's second trailer for Grand Theft Auto VI drew record engagement, "
            "with fans dissecting Vice City locations and the two protagonists."
        ),
    },
    {
        "title": "Rockstar confirms Grand Theft Auto VI remains on track for its announced window",
        "source": "playstation-blog",
        "game": "grand-theft-auto-vi",
        "url": "https://blog.playstation.com/gta6-update",
        "official": True,
        "rumor": False,
        "platforms": ["PlayStation"],
        "days": 3,
        "excerpt": (
            "In an official post, the studio reiterated the previously announced release "
            "window for Grand Theft Auto VI and thanked players for their patience."
        ),
    },
    {
        "title": "Report: additional GTA VI gameplay details leak ahead of official reveal",
        "source": "eurogamer",
        "game": "grand-theft-auto-vi",
        "url": "https://www.eurogamer.net/gta6-leak-report",
        "official": False,
        "rumor": True,
        "platforms": ["PC"],
        "days": 2,
        "excerpt": (
            "According to an insider, further gameplay systems for GTA VI have reportedly "
            "leaked. Rockstar has not commented and the details remain unconfirmed."
        ),
    },
    {
        "title": "Monster Hunter Wilds shares new hunt trailer and confirms cross-play",
        "source": "playstation-blog",
        "game": "monster-hunter-wilds",
        "url": "https://blog.playstation.com/mh-wilds-crossplay",
        "official": True,
        "rumor": False,
        "platforms": ["PlayStation", "Xbox", "PC"],
        "days": 4,
        "excerpt": (
            "Capcom revealed a new Monster Hunter Wilds trailer and officially confirmed "
            "cross-play across PlayStation 5, Xbox Series X|S and PC."
        ),
    },
    {
        "title": "Battlefield reveal event announced with gameplay premiere",
        "source": "xbox-wire",
        "game": "battlefield",
        "url": "https://news.xbox.com/battlefield-reveal",
        "official": True,
        "rumor": False,
        "platforms": ["Xbox", "PC"],
        "days": 5,
        "excerpt": (
            "EA and DICE announced a dedicated reveal event for the next Battlefield, "
            "promising an extended look at gameplay and a return to large-scale warfare."
        ),
    },
    {
        "title": "The Legend of Zelda: next entry teased during Nintendo showcase",
        "source": "nintendo-life",
        "game": "the-legend-of-zelda",
        "url": "https://www.nintendolife.com/zelda-teaser",
        "official": False,
        "rumor": False,
        "platforms": ["Nintendo"],
        "days": 6,
        "excerpt": (
            "Nintendo teased the next chapter in The Legend of Zelda during its latest "
            "showcase, though a release date was not provided."
        ),
    },
    {
        "title": "Elden Ring expansion adds new region and difficulty options in latest update",
        "source": "pc-gamer",
        "game": "elden-ring",
        "url": "https://www.pcgamer.com/elden-ring-update",
        "official": False,
        "rumor": False,
        "platforms": ["PC", "PlayStation", "Xbox"],
        "days": 7,
        "excerpt": (
            "A new Elden Ring update rolled out today, adding an optional region and "
            "quality-of-life difficulty settings following community feedback."
        ),
    },
    {
        "title": "Call of Duty confirms this year's entry and beta dates",
        "source": "xbox-wire",
        "game": "call-of-duty",
        "url": "https://news.xbox.com/cod-beta-dates",
        "official": True,
        "rumor": False,
        "platforms": ["Xbox", "PlayStation", "PC"],
        "days": 8,
        "excerpt": (
            "Activision officially confirmed this year's Call of Duty and published open "
            "beta dates across all platforms, with early access for pre-orders."
        ),
    },
    {
        "title": "Cyberpunk 2077 sequel enters full production, studio says",
        "source": "eurogamer",
        "game": "cyberpunk-2077",
        "url": "https://www.eurogamer.net/cyberpunk-sequel",
        "official": False,
        "rumor": False,
        "platforms": ["PC"],
        "days": 10,
        "excerpt": (
            "CD Projekt confirmed the Cyberpunk sequel, internally codenamed Orion, has "
            "moved into full production following a period of pre-production."
        ),
    },
    {
        "title": "Hollow Knight: Silksong resurfaces with new store listing",
        "source": "rock-paper-shotgun",
        "game": "hollow-knight-silksong",
        "url": "https://www.rockpapershotgun.com/silksong-listing",
        "official": False,
        "rumor": True,
        "platforms": ["PC", "Nintendo"],
        "days": 9,
        "excerpt": (
            "A new store listing for Hollow Knight: Silksong appeared briefly, reigniting "
            "speculation about a release. Team Cherry has not confirmed a date."
        ),
    },
]


async def load_sample_articles(
    db: AsyncSession, sources: dict[str, Source], games: dict[str, Game]
) -> int:
    embedder = get_embedding_provider()
    existing_urls = {r for (r,) in (await db.execute(select(Article.normalized_url))).all()}
    added = 0
    for s in _SAMPLES:
        nurl = normalize_url(s["url"])
        if nurl in existing_urls:
            continue
        src = sources.get(s["source"])
        if src is None:
            continue
        excerpt = make_excerpt(s["excerpt"], 500)
        published = datetime.now(UTC) - timedelta(days=s["days"])
        chash = content_hash(s["title"], excerpt)
        category = "rumor" if s["rumor"] else ("official" if s["official"] else "media")
        embedding = await embedder.embed_one(f"{s['title']}\n{excerpt}")
        article = Article(
            title=s["title"],
            slug=f"{slugify(s['title'])}-{chash[:6]}",
            summary=excerpt,
            content_excerpt=excerpt,
            original_url=s["url"],
            normalized_url=nurl,
            content_hash=chash,
            source_id=src.id,
            published_at=published,
            fetched_at=datetime.now(UTC),
            language="en",
            category=category,
            platforms=s["platforms"],
            is_official=s["official"],
            is_rumor=s["rumor"],
            is_sample=True,
            importance_score=0.7 if s["official"] else 0.5,
            embedding=embedding,
        )
        db.add(article)
        await db.flush()
        game = games.get(s["game"])
        if game:
            db.add(ArticleGame(article_id=article.id, game_id=game.id, confidence=0.95))
        existing_urls.add(nurl)
        added += 1
    await db.commit()
    return added


async def main(load_samples: bool = True) -> None:
    configure_logging("INFO")
    async with SessionLocal() as db:
        sources = await ensure_sources(db)
        games = await ensure_games(db)
        added = await load_sample_articles(db, sources, games) if load_samples else 0
        logger.info(
            "seed_done",
            extra={
                "extra": {
                    "sources": len(sources),
                    "games": len(games),
                    "sample_articles_added": added,
                }
            },
        )
        print(
            f"Seed complete: {len(sources)} sources, {len(games)} games, "
            f"{added} sample articles added."
        )


if __name__ == "__main__":
    load_samples = "--no-samples" not in sys.argv
    asyncio.run(main(load_samples))

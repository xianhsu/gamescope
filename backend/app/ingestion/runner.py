"""CLI ingestion entrypoint.

    python -m app.ingestion.runner                 # all active sources
    python -m app.ingestion.runner --source ign    # one source by slug
    python -m app.ingestion.runner --max 20        # cap items per source

Ensures sources + games exist (idempotent) before ingesting, so it works on a fresh DB.
"""

from __future__ import annotations

import argparse
import asyncio

from app.ai.embedding.factory import get_embedding_provider
from app.ai.llm.factory import get_llm_provider
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.ingestion.pipeline import run_source
from app.repositories.game_repo import GameRepository
from app.repositories.source_repo import SourceRepository
from app.seed import ensure_games, ensure_sources

logger = get_logger("runner")


async def run(source_slug: str | None, max_items: int | None) -> None:
    llm = get_llm_provider()
    embedder = get_embedding_provider()
    async with SessionLocal() as db:
        await ensure_sources(db)
        await ensure_games(db)
        games = await GameRepository(db).get_all()
        sources = await SourceRepository(db).get_all(active_only=True)
        if source_slug:
            sources = [s for s in sources if s.slug == source_slug]
            if not sources:
                print(f"No active source with slug '{source_slug}'.")
                return

        totals = {"found": 0, "stored": 0, "failed": 0}
        for source in sources:
            job = await run_source(
                db, source, llm=llm, embedder=embedder, games=games, max_items=max_items
            )
            totals["found"] += job.articles_found
            totals["stored"] += job.articles_stored
            totals["failed"] += job.articles_failed
            print(
                f"{source.slug:24s} status={job.status:8s} "
                f"found={job.articles_found} stored={job.articles_stored} "
                f"failed={job.articles_failed}"
            )
        print(
            f"\nTOTAL found={totals['found']} stored={totals['stored']} failed={totals['failed']}"
        )


def main() -> None:
    configure_logging("INFO")
    ap = argparse.ArgumentParser(description="GameScope ingestion runner")
    ap.add_argument("--source", help="ingest only this source slug")
    ap.add_argument("--max", type=int, help="max items per source")
    args = ap.parse_args()
    asyncio.run(run(args.source, args.max))


if __name__ == "__main__":
    main()

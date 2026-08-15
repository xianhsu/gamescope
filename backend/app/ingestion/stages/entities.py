"""EXTRACT ENTITIES: link articles to known games via alias dictionary + word-boundary match.

Deterministic and cheap. Confidence is higher when the match is in the title than the excerpt.
The LLM fallback for the long tail is a documented future refinement, not needed for seeded games.
"""

from __future__ import annotations

import re

from app.ingestion.types import PipelineContext, PipelineItem


def _found(text: str, alias: str) -> bool:
    a = alias.strip()
    if not a:
        return False
    # Word-boundary-ish match that also works for CJK (no \b around CJK).
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(a)}(?![A-Za-z0-9])", text, re.I) is not None


def extract_entities(item: PipelineItem, ctx: PipelineContext) -> PipelineItem:
    title = item.title
    body = item.excerpt
    matches: list[tuple[int, float]] = []
    for game in ctx.games:
        names = [game.name, *(game.aliases or [])]
        in_title = any(_found(title, n) for n in names)
        in_body = any(_found(body, n) for n in names)
        if in_title:
            matches.append((game.id, 0.95))
        elif in_body:
            matches.append((game.id, 0.8))
    item.game_matches = matches
    return item

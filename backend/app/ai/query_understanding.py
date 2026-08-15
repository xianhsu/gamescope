"""Query understanding = deterministic rules first, LLM only as a fallback.

Rules cover the common cases cheaply and testably (game aliases, platform keywords, time
ranges, freshness intent, language). The LLM is consulted only to fill gaps for ambiguous
queries; with the local provider it is a no-op, so AI Search still works fully offline.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

CJK = re.compile(r"[\u4e00-\u9fff]")

# Ordered so multi-word/aliased platforms match before generic tokens.
_PLATFORM_PATTERNS: list[tuple[str, list[str]]] = [
    ("PlayStation", ["playstation 5", "playstation", "ps5", "ps4", "psn"]),
    ("Xbox", ["xbox series", "xbox", "game pass", "xsx"]),
    ("Nintendo", ["nintendo switch", "nintendo", "switch"]),
    ("PC", ["pc", "steam", "epic games", "epic store"]),
    ("Mobile", ["ios", "android", "mobile"]),
]

# (regex, time_range) — first match wins.
_TIME_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"today|just announced|刚刚|今天|今日"), "1d"),
    (re.compile(r"this week|past week|last week|最近一周|本周|这周|上周"), "7d"),
    (re.compile(r"two weeks|最近两周|近两周|最近半个月"), "14d"),
    (re.compile(r"this month|past month|最近一个月|本月|近一个月|这个月"), "30d"),
    (re.compile(r"recently|lately|最近|近期"), "14d"),
    (re.compile(r"this year|今年|最近一年"), "90d"),
]

_FRESHNESS = re.compile(
    r"latest|today|recent|recently|just announced|current|now|breaking|newest|"
    r"最新|最近|今天|今日|刚刚|现在|近期",
    re.IGNORECASE,
)


@dataclass
class ParsedQuery:
    query: str
    language: str = "en"
    game: str | None = None
    platform: str | None = None
    topic: str | None = None
    time_range: str | None = None
    intent: str = "news_summary"
    requires_freshness: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def detect_language(query: str) -> str:
    return "zh" if CJK.search(query) else "en"


def match_game(query: str, game_aliases: dict[str, list[str]]) -> str | None:
    """Return the canonical game name whose alias appears in the query (longest alias wins)."""
    q = query.lower()
    best: tuple[int, str] | None = None  # (alias_len, canonical)
    for canonical, aliases in game_aliases.items():
        for alias in [canonical, *aliases]:
            a = alias.lower().strip()
            if not a:
                continue
            if re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", q):
                if best is None or len(a) > best[0]:
                    best = (len(a), canonical)
    return best[1] if best else None


def match_platform(query: str) -> str | None:
    q = query.lower()
    for canonical, needles in _PLATFORM_PATTERNS:
        for n in needles:
            if re.search(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", q):
                return canonical
    return None


def match_time_range(query: str) -> str | None:
    for pattern, tr in _TIME_PATTERNS:
        if pattern.search(query):
            return tr
    return None


def parse_query(query: str, game_aliases: dict[str, list[str]] | None = None) -> ParsedQuery:
    """Pure, deterministic rule-based parse. Fully unit-testable."""
    game_aliases = game_aliases or {}
    q = query.strip()
    return ParsedQuery(
        query=q,
        language=detect_language(q),
        game=match_game(q, game_aliases),
        platform=match_platform(q),
        time_range=match_time_range(q),
        requires_freshness=bool(_FRESHNESS.search(q)),
    )


async def understand(
    query: str,
    game_aliases: dict[str, list[str]],
    llm,  # app.ai.llm.base.LLMProvider
) -> ParsedQuery:
    """Rules first; consult the LLM only to fill gaps (game/time) for ambiguous queries."""
    parsed = parse_query(query, game_aliases)
    if parsed.game and parsed.time_range:
        return parsed  # rules were sufficient — skip the LLM entirely

    from app.ai.prompts import QUERY_UNDERSTANDING_SYSTEM

    try:
        raw = await llm.complete(
            system=QUERY_UNDERSTANDING_SYSTEM,
            user=query,
            temperature=0.0,
            max_tokens=200,
            json_mode=True,
        )
        data = json.loads(raw) if raw.strip() else {}
    except Exception:  # noqa: BLE001 — never let understanding failure break search
        data = {}

    parsed.game = parsed.game or (data.get("game") or None)
    parsed.platform = parsed.platform or (data.get("platform") or None)
    parsed.time_range = parsed.time_range or (data.get("time_range") or None)
    parsed.topic = parsed.topic or (data.get("topic") or None)
    if data.get("intent"):
        parsed.intent = data["intent"]
    parsed.requires_freshness = parsed.requires_freshness or bool(data.get("requires_freshness"))
    return parsed

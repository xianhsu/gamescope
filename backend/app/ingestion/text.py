"""Pure text helpers used across ingestion stages (unit-tested, no I/O)."""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_", "ref", "cmpid", "igshid")
_WS = re.compile(r"\s+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def normalize_url(url: str) -> str:
    """Canonical dedup URL: lowercase scheme/host, drop tracking params + fragment, no trailing slash."""  # noqa: E501
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
    except ValueError:
        return url.strip()
    scheme = (p.scheme or "https").lower()
    netloc = p.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(_TRACKING_PREFIXES)]
    path = p.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, "", urlencode(query), ""))


def slugify(text: str, max_len: int = 80) -> str:
    text = _NON_SLUG.sub("-", (text or "").lower()).strip("-")
    return text[:max_len].strip("-") or "article"


def strip_html(html: str) -> str:
    if not html:
        return ""
    try:
        from selectolax.parser import HTMLParser

        text = HTMLParser(html).text(separator=" ")
    except Exception:  # noqa: BLE001 — fall back to a naive strip
        text = re.sub(r"<[^>]+>", " ", html)
    return _WS.sub(" ", text).strip()


def make_excerpt(text: str, max_chars: int = 500) -> str:
    text = _WS.sub(" ", text or "").strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last = cut.rfind(" ")
    return (cut[:last] if last > 0 else cut).rstrip() + "…"


def content_hash(*parts: str) -> str:
    joined = "\u0001".join(_WS.sub(" ", (p or "").strip().lower()) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def title_similarity(a: str, b: str) -> float:
    a2 = _WS.sub(" ", (a or "").lower()).strip()
    b2 = _WS.sub(" ", (b or "").lower()).strip()
    if not a2 or not b2:
        return 0.0
    return SequenceMatcher(None, a2, b2).ratio()

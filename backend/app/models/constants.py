"""Domain enums stored as strings (portable, migration-friendly)."""

from __future__ import annotations

from enum import StrEnum


class SourceType(StrEnum):
    RSS = "rss"
    API = "api"
    WEB = "web"


class ReliabilityLevel(StrEnum):
    OFFICIAL = "official"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(StrEnum):
    OFFICIAL = "official"
    MEDIA = "media"
    RUMOR = "rumor"
    UPDATE = "update"
    REVIEW = "review"
    DEAL = "deal"
    OTHER = "other"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SearchKind(StrEnum):
    KEYWORD = "keyword"
    AI = "ai"


PLATFORMS = ["PC", "PlayStation", "Xbox", "Nintendo", "Mobile"]

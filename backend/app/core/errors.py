"""Unified error model.

A single `AppError` hierarchy maps domain failures to stable error codes + HTTP status.
FastAPI exception handlers (registered in main.py) render every error as:

    {"error": {"code": "...", "message": "...", "request_id": "..."}}

Users never see stack traces or raw 500s.
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
    ARTICLE_PARSE_FAILED = "ARTICLE_PARSE_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_PROVIDER_UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Base application error. Subclasses set a default code + status."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    status_code: int = 500
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: ErrorCode | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message or self.message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class InvalidRequestError(AppError):
    code = ErrorCode.INVALID_REQUEST
    status_code = 400
    message = "The request was invalid."


class NotFoundError(AppError):
    code = ErrorCode.NOT_FOUND
    status_code = 404
    message = "Resource not found."


class RateLimitedError(AppError):
    code = ErrorCode.RATE_LIMITED
    status_code = 429
    message = "Rate limit exceeded. Please try again shortly."


class SourceFetchError(AppError):
    code = ErrorCode.SOURCE_FETCH_FAILED
    status_code = 502
    message = "Failed to fetch from the news source."


class ArticleParseError(AppError):
    code = ErrorCode.ARTICLE_PARSE_FAILED
    status_code = 422
    message = "Failed to parse the article."


class DatabaseError(AppError):
    code = ErrorCode.DATABASE_ERROR
    status_code = 500
    message = "A database error occurred."


class SearchError(AppError):
    code = ErrorCode.SEARCH_ERROR
    status_code = 500
    message = "Search is temporarily unavailable."


class AIProviderError(AppError):
    code = ErrorCode.AI_PROVIDER_ERROR
    status_code = 502
    message = "The AI provider returned an error."


class AIProviderUnavailableError(AppError):
    code = ErrorCode.AI_PROVIDER_UNAVAILABLE
    status_code = 503
    message = "AI search is temporarily unavailable."


class EmbeddingError(AppError):
    code = ErrorCode.EMBEDDING_ERROR
    status_code = 502
    message = "Failed to generate embeddings."

"""ORM -> Pydantic mappers. Keeps route/service code declarative."""

from __future__ import annotations

from app.models.article import Article
from app.schemas.article import ArticleDetail, ArticleListItem
from app.schemas.game import GameOut
from app.schemas.source import SourceOut


def _games(article: Article) -> list[GameOut]:
    return [GameOut.model_validate(link.game) for link in article.game_links]


def to_list_item(article: Article) -> ArticleListItem:
    return ArticleListItem(
        id=article.id,
        title=article.title,
        slug=article.slug,
        summary=article.summary,
        original_url=article.original_url,
        image_url=article.image_url,
        published_at=article.published_at,
        language=article.language,
        category=article.category,
        platforms=list(article.platforms or []),
        is_official=article.is_official,
        is_rumor=article.is_rumor,
        is_sample=article.is_sample,
        importance_score=article.importance_score,
        source=SourceOut.model_validate(article.source),
        games=_games(article),
    )


def to_detail(article: Article, related: list[Article]) -> ArticleDetail:
    base = to_list_item(article)
    return ArticleDetail(
        **base.model_dump(),
        content_excerpt=article.content_excerpt,
        fetched_at=article.fetched_at,
        related=[to_list_item(a) for a in related],
    )

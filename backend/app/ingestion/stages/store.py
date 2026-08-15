"""STORE: persist the Article + game links. search_vector is maintained by a DB trigger."""

from __future__ import annotations

from app.ingestion.text import slugify
from app.ingestion.types import PipelineContext, PipelineItem
from app.models.article import Article
from app.models.article_game import ArticleGame


async def store(item: PipelineItem, ctx: PipelineContext) -> Article:
    slug = f"{slugify(item.title)}-{item.content_hash[:6]}"
    article = Article(
        title=item.title,
        slug=slug,
        summary=item.summary,
        content_excerpt=item.excerpt,
        original_url=item.original_url,
        normalized_url=item.normalized_url,
        content_hash=item.content_hash,
        source_id=ctx.source.id,
        published_at=item.published_at,
        fetched_at=item.fetched_at,
        language=item.language,
        category=item.category,
        platforms=item.platforms,
        is_official=item.is_official,
        is_rumor=item.is_rumor,
        importance_score=item.importance_score,
        image_url=item.image_url,
        embedding=item.embedding,
    )
    ctx.db.add(article)
    await ctx.db.flush()  # assign article.id

    seen: set[int] = set()
    for game_id, confidence in item.game_matches:
        if game_id in seen:
            continue
        seen.add(game_id)
        ctx.db.add(ArticleGame(article_id=article.id, game_id=game_id, confidence=confidence))

    # Keep the in-memory dedup cache fresh so later items in the same run see this one.
    ctx.recent_titles.insert(0, (article.id, article.title, article.normalized_url))
    return article

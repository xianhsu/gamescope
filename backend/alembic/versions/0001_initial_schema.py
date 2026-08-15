"""initial schema: sources, games, articles (pgvector + FTS), links, jobs, logs

Revision ID: 0001
Revises:
Create Date: 2026-08-15

Design notes
------------
* pgvector `vector` column + HNSW cosine index power semantic retrieval.
* A Postgres `tsvector` column, maintained by a trigger and indexed with GIN,
  powers full-text retrieval. Weights: title=A, summary=B, excerpt=C.
* pg_trgm GIN index on title backs the ILIKE fallback used when FTS finds nothing.
* Embedding dimension comes from application settings so the DB and the embedding
  provider can never silently disagree.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from app.core.config import settings

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBED_DIM = settings.embedding_dim


def upgrade() -> None:
    # --- Extensions -------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- source -----------------------------------------------------------
    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False, server_default="rss"),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("feed_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "reliability_level", sa.String(length=16), nullable=False, server_default="medium"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_source_slug", "source", ["slug"], unique=True)

    # --- game -------------------------------------------------------------
    op.create_table(
        "game",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False),
        sa.Column("developer", sa.String(length=200), nullable=True),
        sa.Column("publisher", sa.String(length=200), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column(
            "aliases",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_game_slug", "game", ["slug"], unique=True)

    # --- article ----------------------------------------------------------
    op.create_table(
        "article",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=600), nullable=False),
        sa.Column("slug", sa.String(length=650), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_excerpt", sa.Text(), nullable=True),
        sa.Column("original_url", sa.String(length=1000), nullable=False),
        sa.Column("normalized_url", sa.String(length=1000), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("source.id"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("category", sa.String(length=16), nullable=False, server_default="other"),
        sa.Column(
            "platforms",
            postgresql.ARRAY(sa.String(length=32)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_rumor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("importance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("original_url", name="uq_article_original_url"),
        sa.UniqueConstraint("slug", name="uq_article_slug"),
    )
    op.create_index("ix_article_slug", "article", ["slug"])
    op.create_index("ix_article_normalized_url", "article", ["normalized_url"])
    op.create_index("ix_article_content_hash", "article", ["content_hash"])
    op.create_index("ix_article_source_id", "article", ["source_id"])
    op.create_index("ix_article_published_at", "article", ["published_at"])
    op.create_index("ix_article_category", "article", ["category"])

    # Full-text search vector, trigger-maintained (title=A, summary=B, excerpt=C).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION article_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(NEW.summary, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(NEW.content_excerpt, '')), 'C');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER article_search_vector_trigger
        BEFORE INSERT OR UPDATE OF title, summary, content_excerpt
        ON article FOR EACH ROW EXECUTE FUNCTION article_search_vector_update();
        """
    )
    op.execute(
        "CREATE INDEX ix_article_search_vector ON article USING gin (search_vector)"
    )
    # Trigram index for the ILIKE fallback path.
    op.execute(
        "CREATE INDEX ix_article_title_trgm ON article USING gin (title gin_trgm_ops)"
    )
    # HNSW cosine index for vector retrieval (nulls skipped automatically).
    op.execute(
        "CREATE INDEX ix_article_embedding_hnsw ON article "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # --- article_game (M2M) ----------------------------------------------
    op.create_table(
        "article_game",
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("article.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "game_id",
            sa.Integer(),
            sa.ForeignKey("game.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1"),
    )
    op.create_index("ix_article_game_game_id", "article_game", ["game_id"])

    # --- processing_job ---------------------------------------------------
    op.create_table(
        "processing_job",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("source.id"), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("articles_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_processing_job_source_id", "processing_job", ["source_id"])

    # --- search_log -------------------------------------------------------
    op.create_table(
        "search_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query", sa.String(length=500), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="keyword"),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_live", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("search_log")
    op.drop_index("ix_processing_job_source_id", table_name="processing_job")
    op.drop_table("processing_job")
    op.drop_index("ix_article_game_game_id", table_name="article_game")
    op.drop_table("article_game")

    op.execute("DROP INDEX IF EXISTS ix_article_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_article_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_article_search_vector")
    op.execute("DROP TRIGGER IF EXISTS article_search_vector_trigger ON article")
    op.execute("DROP FUNCTION IF EXISTS article_search_vector_update()")
    op.drop_table("article")

    op.drop_index("ix_game_slug", table_name="game")
    op.drop_table("game")
    op.drop_index("ix_source_slug", table_name="source")
    op.drop_table("source")
    # Extensions are left installed on purpose (may be shared).

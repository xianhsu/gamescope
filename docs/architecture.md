# Architecture

GameScope is a two-tier application (Next.js frontend + FastAPI backend) over a single
PostgreSQL database with the `pgvector` and `pg_trgm` extensions. The backend owns all business
logic and is independently deployable; the frontend is purely a client of the versioned REST API.

See the root [`ARCHITECTURE.md`](../ARCHITECTURE.md) for the full design and the "why not" decision
log. This document is the practical, code-oriented tour.

## Layered backend

```
app/
├── api/              # HTTP layer: routers, dependencies, request/response only
│   └── v1/routes/    # news, games, search, ai, trending, system, health
├── services/         # Business logic / orchestration (NewsService, AISearchService, …)
├── repositories/     # Data access (SQLAlchemy queries), one per aggregate
├── models/           # SQLAlchemy ORM models (Source, Article, Game, …)
├── schemas/          # Pydantic request/response contracts
├── retrieval/        # FTS / vector / live retrievers + RRF fusion + rerank
├── ingestion/        # Staged pipeline, sources (RSS), per-stage modules
├── ai/               # LLM + embedding provider abstractions, query understanding, RAG
├── core/             # config, logging (request IDs), errors, pagination
└── db/               # async engine/session, declarative base
```

**Dependency direction is strictly downward:** `api → services → repositories → models/db`.
Routes never touch the ORM directly; services never build HTTP responses; repositories never
contain business rules. This keeps each layer independently testable.

## Request lifecycle

1. **Middleware** assigns a `request_id` (UUID) and binds it to structured logs; it is echoed in
   the `X-Request-ID` response header.
2. **Router** validates path/query/body via Pydantic and FastAPI dependencies
   (`DbSession`, `Pagination`).
3. **Service** orchestrates repositories + (for AI) retrieval/AI modules.
4. **Repository** runs async SQLAlchemy queries.
5. **Response** is serialized from a Pydantic schema. Any raised `AppError` subclass is caught by a
   central exception handler and rendered as the unified error envelope — users never see a raw
   stack trace or 500.

## Data model

| Table | Purpose | Notable columns / indexes |
|---|---|---|
| `source` | News sources | `slug` unique, `reliability_level`, `feed_url` |
| `article` | Ingested articles | `original_url`/`slug` unique, `content_hash`, `normalized_url`, `embedding VECTOR(1536)`, `search_vector TSVECTOR` |
| `game` | Tracked games | `slug` unique, `aliases JSONB` |
| `article_game` | M2M article↔game | composite PK, `confidence`, cascade FKs |
| `processing_job` | Ingestion run records | `status`, found/stored/failed counts |
| `search_log` | Query analytics | `kind` (keyword/ai), `latency_ms`, `used_live` |

Indexes that matter:

- **FTS:** a trigger maintains `article.search_vector` (title = weight A, summary = B, excerpt = C);
  a **GIN** index backs `websearch_to_tsquery` search.
- **Vector:** an **HNSW** index on `embedding` with `vector_cosine_ops` for approximate NN search.
- **Trigram:** a **GIN** `pg_trgm` index on `title` for resilient `ILIKE` fallback.

Migrations are managed by **Alembic** using the async engine (`connection.run_sync`), so there is a
single database driver (`asyncpg`) across the app and migrations.

## Configuration & operations

- **12-factor config** in `core/config.py` (Pydantic Settings). Nothing secret is hard-coded;
  freshness/retrieval thresholds the brief asked us not to hard-code live here.
- **Structured logging** with request IDs; secrets are never logged.
- **Health check** (`/health`) reports per-dependency status (e.g. database connectivity).
- **Docker Compose** brings up `postgres` (pgvector), `backend` (migrates + optionally seeds on
  start), and `frontend`. **GitHub Actions CI** runs the backend against a real pgvector service
  and the frontend through lint + typecheck + build.

## Frontend

Next.js 14 App Router with React Server Components for data fetching (via the typed client in
`src/lib/api.ts`) and a few client components for interactivity (filters, AI Search). Every page
implements **loading / error / empty** states, and the design uses shadcn-style tokens. The AI
Search page deliberately surfaces the retrieval pipeline and per-stage counts so the system reads
as a real RAG engine, not a black box.

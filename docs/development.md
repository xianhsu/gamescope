# Development Guide

## Prerequisites

- **Docker** (recommended path) — or, for local dev: **Python 3.12**, **Node 20+**, and a
  **PostgreSQL 16** with the `pgvector` extension.

## Run everything with Docker

```bash
docker compose up --build
```

- Frontend → http://localhost:3000
- API docs → http://localhost:8000/api/docs
- Health → http://localhost:8000/api/v1/health

The backend container runs migrations on start and seeds labeled sample data
(`SEED_ON_START=true`). No API key is required — it defaults to deterministic local AI providers.

## Backend (local)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env                # point POSTGRES_* / DATABASE_URL at your DB
alembic upgrade head
python -m app.seed                  # optional labeled sample data
uvicorn app.main:app --reload
```

Ingest real news:

```bash
python -m app.ingestion.runner
```

### Backend quality gates

```bash
ruff check app alembic              # lint (line-length 100)
ruff format --check app             # formatting
pytest                              # unit + hermetic API tests
```

The test suite is DB-free and hermetic (pure logic + ASGI transport), so it runs anywhere. The
**real** end-to-end DB gate is CI, which runs migrations + seed + tests against a live
`pgvector/pgvector:pg16` service.

## Frontend (local)

```bash
cd frontend
npm install
npm run dev                         # http://localhost:3000
```

Configure the API base URL if needed (default `http://localhost:8000/api/v1`):

```bash
cp .env.example .env.local
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### Frontend quality gates

```bash
npm run lint
npm run typecheck
npm run build
```

## Configuration reference

Key settings (see `backend/app/core/config.py`, all read from the environment):

| Variable | Default | Purpose |
|---|---|---|
| `ENVIRONMENT` | `development` | env name surfaced in `/health` |
| `DATABASE_URL` / `POSTGRES_*` | assembled | async SQLAlchemy connection |
| `CORS_ORIGINS` | `http://localhost:3000` | comma-separated allowlist |
| `LLM_PROVIDER` | `local` | `local` \| `openai` |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | — | used when provider = openai |
| `EMBEDDING_PROVIDER` | `local` | `local` \| `openai` |
| `EMBEDDING_DIM` | `1536` | must match the `article.embedding` column |
| `RRF_K` | `60` | Reciprocal Rank Fusion damping |
| `RETRIEVAL_*_LIMIT` | 15/15/20/8 | fts / vector / fused / context sizes |
| `LIVE_RETRIEVAL_ENABLED` | `false` | enable the pluggable live retriever |
| `FRESHNESS_MAX_AGE_HOURS` | `48` | freshness window before preferring live |
| `INGEST_MAX_ITEMS_PER_SOURCE` | `40` | per-run cap |

> Changing `EMBEDDING_DIM` requires a matching migration for the `VECTOR(n)` column.

## Project layout

```
.
├── backend/        # FastAPI service (see docs/architecture.md)
├── frontend/       # Next.js app (App Router)
├── docs/           # this documentation
├── docker-compose.yml
├── .github/workflows/ci.yml
├── PROJECT.md  ARCHITECTURE.md  PLAN.md
└── README.md
```

## Conventions

- Backend: layered (api → service → repository → model), Pydantic at the edges, unified errors,
  request-ID logging, `ruff` for lint + format.
- Frontend: typed API client is the only place that talks HTTP; every page has loading / error /
  empty states; types mirror the backend schemas in `src/lib/types.ts`.
- Data honesty: real stats only; sample data is labeled; copyright-safe storage (excerpt + summary +
  link).

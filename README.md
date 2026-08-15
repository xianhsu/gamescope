# GameScope — AI-Powered Gaming News Intelligence

> Aggregates gaming news from real sources and answers natural-language questions with
> **grounded, cited** AI — every claim traces back to a retrieved article, or the system
> honestly says it doesn't know.

GameScope is a portfolio-grade, production-shaped full-stack system. It is built to be
**runnable, explainable, and honest** — not a demo of buzzwords. The centerpiece is an
AI Search that does real retrieval (hybrid full-text + vector) and grounds every answer
in sources, rather than being a thin wrapper around a chat API.

---

## 30-second value

- **Ask, don't just browse.** "What's the latest on GTA VI?" → a cited answer built from
  retrieved news, with a visible query-understanding + retrieval breakdown.
- **Real pipeline, real data.** News enters via real RSS feeds through a staged ingestion
  pipeline with per-item fault isolation. Every article keeps its source + original URL.
- **No black box.** The `/system` page shows real DB-backed statistics, health, and recent
  jobs. The AI Search UI shows the exact retrieval flow and counts (FTS / vector / fused / reranked).
- **Honest by design.** Sample/seed data is labeled with a "Sample" badge; no fabricated
  numbers; copyright-safe (excerpt + summary + link, never full-article copies).

## What it demonstrates

| Area | How |
|---|---|
| **Full-Stack** | Next.js 14 (App Router) + TypeScript, typed API client, loading/error/empty states across every page |
| **Backend** | Layered FastAPI (API → Service → Repository → DB), Pydantic validation, unified error envelope, OpenAPI |
| **Database** | PostgreSQL relational model, indexes, full-text search (`tsvector` + GIN), `pgvector` (HNSW), `pg_trgm`, Alembic migrations |
| **Data Engineering** | Staged ingestion (fetch → parse → normalize → dedup → classify → enrich → embed → store) with fault isolation + job records |
| **AI / RAG** | Query understanding → metadata filter → hybrid retrieval → RRF fusion → rerank → context builder → grounded generation + citations |
| **Software Engineering** | Docker Compose, GitHub Actions CI, pytest, structured logging with request IDs, health checks, docs |

---

## Quick start (Docker)

```bash
# From the repo root
docker compose up --build
```

Then open:

- **Frontend:** http://localhost:3000
- **API docs (Swagger):** http://localhost:8000/api/docs
- **Health:** http://localhost:8000/api/v1/health

The backend runs migrations on start and seeds clearly-labeled sample data
(`SEED_ON_START=true`). It works **without any API key** using deterministic local
LLM/embedding providers, so the whole system is runnable offline.

### Ingest real news (optional)

```bash
docker compose exec backend python -m app.ingestion.runner
```

This pulls from the configured RSS feeds, runs the full pipeline, and records a
`ProcessingJob` visible on the `/system` page.

## Local development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
# Requires a local Postgres with the pgvector extension; see backend/.env.example
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Set `NEXT_PUBLIC_API_BASE_URL` (see `frontend/.env.example`) if the API is not at
`http://localhost:8000/api/v1`.

## Testing & CI

```bash
# Backend
cd backend
ruff check app alembic && ruff format --check app
pytest

# Frontend
cd frontend
npm run lint && npm run typecheck && npm run build
```

CI (`.github/workflows/ci.yml`) runs the backend job against a real
`pgvector/pgvector:pg16` service (migrations + seed + tests are a true end-to-end DB gate)
and a frontend job (lint + typecheck + build).

---

## Architecture at a glance

```
┌───────────────┐      HTTP/JSON       ┌────────────────────────────────────────┐
│  Next.js (FE) │  ───────────────▶    │  FastAPI (API → Service → Repository)   │
│  typed client │                      │                                         │
└───────────────┘                      │   Ingestion pipeline (staged, isolated) │
                                       │   AI Search (RAG, hybrid retrieval)     │
                                       └───────────────┬─────────────────────────┘
                                                       │
                                            ┌──────────▼───────────┐
                                            │ PostgreSQL + pgvector │
                                            │ FTS (tsvector+GIN)    │
                                            └───────────────────────┘
```

The **AI Search flow is never `question → LLM → answer`**. It is:

```
Query → Query Understanding → Metadata Filter → [FTS + Vector Retrieval]
      → Merge / Dedup / Rerank (RRF) → Context Builder → LLM → Answer + Sources
```

## Documentation

- [`PROJECT.md`](./PROJECT.md) — scope, goals, non-goals, success criteria, data ethics
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — full architecture, schema, "why not" decisions
- [`PLAN.md`](./PLAN.md) — phased delivery plan
- [`docs/architecture.md`](./docs/architecture.md) — layered design & request lifecycle
- [`docs/api.md`](./docs/api.md) — REST API reference
- [`docs/data-pipeline.md`](./docs/data-pipeline.md) — ingestion stages & fault isolation
- [`docs/ai-search.md`](./docs/ai-search.md) — the RAG pipeline in detail
- [`docs/development.md`](./docs/development.md) — setup, workflow, conventions

## Key engineering decisions

- **Postgres FTS + pgvector instead of Elasticsearch** — one datastore covers v1's keyword +
  semantic needs; fewer moving parts, easier to reason about and operate.
- **Provider abstraction over OpenAI lock-in** — an OpenAI-compatible provider and a
  deterministic local provider sit behind one interface, so the system runs offline and can
  switch models via config.
- **RRF for fusion** — rank-based Reciprocal Rank Fusion is robust to incomparable score
  scales between FTS and vector retrievers.
- **Grounded generation with a citation contract** — the model answers only from numbered
  context and cites sources; empty retrieval yields an honest "insufficient information".
- **Deliberate non-goals** — no Kubernetes/Kafka/microservices/multi-DB/auth/payments; each
  exclusion is documented in `ARCHITECTURE.md` to show scope judgment.

## License & data ethics

GameScope stores only titles, metadata, a short excerpt, a GameScope-generated summary, the
source name, and the original URL. It prefers RSS/official feeds and links out to publishers.
Sample data is clearly labeled and never presented as real, live news.

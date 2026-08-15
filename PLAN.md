# PLAN.md — GameScope Delivery Plan

Phased plan. Each phase has **Goal / Tasks / Validation / Exit Criteria**. Phases build a working vertical
slice before widening. Status legend: ✅ done · 🟡 in progress · ⬜ planned.

> Consistency note: this plan implements exactly the scope in `PROJECT.md` and the design in `ARCHITECTURE.md`.
> The pipeline stages, DB tables, API routes, and retrieval flow named here match those documents 1:1.

---

## Phase 0 — Analysis & Planning ✅
- **Goal:** Scope review, final stack, repo/DB/API/pipeline/retrieval/frontend design.
- **Tasks:** Write `PROJECT.md`, `ARCHITECTURE.md`, `PLAN.md`; scaffold repo structure.
- **Validation:** Three docs are internally consistent (tables/routes/stages match).
- **Exit:** Docs committed; scaffold present.

## Phase 1 — Foundation ✅
- **Goal:** Runnable skeleton; frontend↔backend↔DB wired.
- **Tasks:** FastAPI app, `core/config`, `core/logging` (request IDs), `core/errors`, async SQLAlchemy
  session, `GET /health`, docker-compose (frontend/backend/postgres+pgvector), `.env.example`,
  GitHub Actions (backend lint+test, frontend lint+typecheck+build), Next.js app shell + API client.
- **Validation:** `GET /api/v1/health` returns healthy; `/api/docs` loads; frontend renders; compose config valid.
- **Exit:** Health check green end-to-end; CI workflows present.

## Phase 2 — News Domain ✅
- **Goal:** Persistent domain model + read APIs.
- **Tasks:** Models (Source/Article/Game/ArticleGame/ProcessingJob/SearchLog); Alembic initial migration
  incl. pgvector, FTS `tsvector` + GIN, `pg_trgm`, ivfflat/hnsw; repositories; services; API:
  `/news`, `/news/{slug}`, `/games`, `/games/{slug}`, `/games/{slug}/news`, `/trending`, `/system/*`.
- **Validation:** Migration up/down; endpoints return paginated, filtered data against seed rows.
- **Exit:** News + games browsable via API and Swagger.

## Phase 3 — News Ingestion ✅
- **Goal:** Real news enters via real sources, reliably.
- **Tasks:** `NewsSource` provider pattern (RSS first) + registry; stages fetch/parse/normalize/clean/dedup/store;
  pipeline orchestrator with per-article fault isolation; `ProcessingJob` writes; `runner.py` CLI.
- **Validation:** Run against ≥5 real RSS feeds; articles stored with source + original URL; dedup works; job recorded.
- **Exit:** `python -m app.ingestion.runner` ingests real articles idempotently.

## Phase 4 — AI Enrichment ✅
- **Goal:** Summaries, classification, entities, embeddings — without blocking ingestion.
- **Tasks:** classify/entities/summarize/embed stages; LLM + embedding provider abstraction (OpenAI-compatible +
  local fallback); content-hash idempotency; graceful degradation on AI failure.
- **Validation:** With no API key, local providers produce deterministic summary/embedding; with a key, real ones;
  AI failure still stores the article.
- **Exit:** Enriched articles present; failures isolated and logged.

## Phase 5 — Search ✅
- **Goal:** Traditional search that works.
- **Tasks:** FTS retriever (Postgres `websearch_to_tsquery`), vector retriever (pgvector cosine), hybrid RRF fusion;
  `GET /search`; `SearchLog`.
- **Validation:** Queries like "GTA VI", "Nintendo", "Steam" return relevant, ranked results.
- **Exit:** Search endpoint returns relevant results with scores.

## Phase 6 — AI Search (RAG) ✅
- **Goal:** The centerpiece: grounded, cited answers.
- **Tasks:** Query understanding (rules+LLM); metadata filter; hybrid retrieval; optional rerank; context builder
  (numbered, budgeted); grounded generation with citations; freshness logic + pluggable live retriever;
  `POST /ai/search`.
- **Validation:** "What happened with GTA VI this week?" / "最近一周 GTA6 有什么消息？" return an answer citing
  real retrieved sources; empty-retrieval → honest "insufficient information".
- **Exit:** AI Search returns answer + real citations + query_metadata.

## Phase 7 — Frontend ✅
- **Goal:** Portfolio-quality UI for all 5(+1) pages.
- **Tasks:** Home, News (+filters), News Detail, AI Search (query→sources→answer), System, Games; loading/error/empty
  states; responsive; dark-first editorial design; typed API client.
- **Validation:** UI self-check (§43 of brief): padding/typography/alignment/overflow/card height/mobile/dark mode/states.
- **Exit:** All pages render real API data with proper states.

## Phase 8 — Quality ✅
- **Goal:** Confidence + hygiene.
- **Tasks:** pytest unit tests (normalize, dedup, hybrid ranking, query parser, a service) + API tests (health, news, search);
  frontend lint/typecheck/build; security review (env, input validation, CORS, HTML sanitize, URL validation);
  error-handling + performance review (indexes, pagination, async, pooling, caching).
- **Validation:** `pytest` green; frontend `lint`+`typecheck`+`build` green; CI passes.
- **Exit:** All checks pass locally and in CI.

## Phase 9 — Portfolio Polish ✅
- **Goal:** 3–5 minute interviewer comprehension.
- **Tasks:** README (30-sec value up top, screenshots, architecture diagram, AI pipeline, stack, API, setup, testing,
  engineering decisions, future work); `docs/architecture.md`, `docs/api.md`, `docs/data-pipeline.md`,
  `docs/ai-search.md`, `docs/development.md`; demo instructions.
- **Validation:** A fresh reader understands what/why/how quickly; setup steps actually work.
- **Exit:** Docs complete and consistent with code.

---

## Self-check checklist (run after every phase)
Build? Run? API works? Migration up/down? Search relevant? AI cites real sources? Errors handled?
Logs readable (no secrets)? Frontend loading/error/empty states present?

## MVP vs Future Work
- **MVP:** everything in Phases 0–9 above.
- **Future Work:** personalized feed, accounts, game follow, daily digest, recommendations, notifications,
  mobile app, Discord bot, advanced rumor verification, knowledge graph, multi-agent research, Elasticsearch,
  Kafka, Kubernetes, learned reranker, real live-web provider, Redis + async workers.

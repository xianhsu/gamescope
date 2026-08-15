# PROJECT.md — GameScope

> AI-Powered Gaming News Intelligence Platform
> A portfolio-grade, production-shaped project that ingests gaming news, structures it,
> and lets users answer natural-language questions with **grounded, cited** AI answers.

---

## 1. Goal

Build a **realistic, runnable, explainable** full-stack system that demonstrates end-to-end
engineering ability across Full-Stack, Backend, Database, Data Engineering, and AI/RAG —
without over-engineering.

The primary audience is **a technical interviewer**, not end users. Every decision optimizes for:

- **Technical completeness > feature count**
- **Sound architecture > technology stacking**
- **Explainability > flash**
- **Finished vertical slices > broad half-built surface area**

If a technology has no real need in this scope, it is intentionally left out (see Non-goals).

## 2. Users

| Persona | Need | What they touch |
|---|---|---|
| **Interviewer / reviewer** (primary) | Understand engineering depth in 3–5 min | README, `/system` page, Swagger UI, source tree |
| **Gaming reader** (secondary, realistic) | See latest news, ask "what happened with X?" | Home, News, News Detail, AI Search |
| **Future clients** (App/Bot) | Reuse backend without the web UI | Versioned REST API (`/api/v1`) |

The frontend is a **client of the API**, never the owner of business logic. The backend is
independently deployable and reusable by future App / Bot / other frontends.

## 3. Interview Showcase Goals

The project must let an interviewer verify each of these by clicking, not by taking my word:

1. **Full-Stack** — a real Next.js/TypeScript app with loading / error / empty states and responsive, dark-first design.
2. **Backend** — clean layered FastAPI service (API → Service → Repository → DB), validation, unified errors, OpenAPI.
3. **Database** — PostgreSQL with a sensible relational model, indexes, full-text search, `pgvector`, constraints, migrations.
4. **Data Engineering** — a real staged ingestion pipeline (fetch → parse → normalize → clean → dedup → classify → enrich → embed → store) with per-item fault isolation.
5. **AI / RAG** — query understanding, hybrid retrieval (FTS + vector), rank fusion, context construction, grounded generation with citations and hallucination controls — **not a thin Chat API wrapper**.
6. **Software Engineering** — Git, CI, tests, Docker Compose, config management, structured logging, health checks, documentation, architecture diagrams.

## 4. Feature Scope (MVP / v1)

**Must implement:**

- News Home (hero + AI search box, featured/trending games, latest news cards)
- News List with filters: Latest / PC / PlayStation / Xbox / Nintendo (+ Official / Media / Rumor when data allows)
- News Detail (title, source, original publish time, original URL, GameScope AI summary, game, platform, category, related news)
- Traditional Search (title, summary, game, category)
- **AI Search** (the centerpiece): query understanding → metadata filter → FTS + vector retrieval → merge/dedup/rerank → context → grounded LLM answer + sources
- Hybrid retrieval (FTS + vector), with a **pluggable** live-web retriever behind the same interface
- Freshness logic (config-driven thresholds; keywords like "latest/today/recently" bias toward live retrieval)
- Grounded answers with citations, rumor vs official distinction, "insufficient information" honesty
- `/system` page ("How GameScope Works") with real pipeline stats, health, and recent jobs
- Optional: `/games/[slug]` game page (implemented because cost is low and value is high)

## 5. Non-goals (explicitly out of scope for v1)

Deliberately excluded to avoid over-engineering; each has a documented reason in ARCHITECTURE.md §"Why not":

- Kubernetes, Kafka, Service Mesh, large-scale microservices
- Multiple databases / polyglot persistence
- Complex auth / RBAC, accounts, profiles, favorites, comments, social, subscriptions, payments
- Recommendation platform, personalized feed, notifications
- Multi-agent orchestration (Manager/Search/Verify/Judge agents) — a reliable retrieval system is the goal
- Elasticsearch (Postgres FTS + pgvector covers v1 needs)
- Fine-tuning (RAG is the right tool for fresh, source-attributable facts)
- Full-text copying of copyrighted articles (see §7)

These live in **Future Work**, not v1.

## 6. Success Criteria

v1 is successful (independent of feature count) when **all** of the following are true and demonstrable:

- [ ] `docker compose up` brings up frontend + backend + postgres(pgvector)
- [ ] Real news enters the system via real sources (RSS) — every article keeps a source + original URL
- [ ] `/api/docs` (Swagger UI) is usable to exercise endpoints
- [ ] Traditional search returns relevant results
- [ ] AI Search performs actual retrieval and returns an answer with **real citations** to retrieved articles
- [ ] Errors are handled with a unified error model (no raw 500 / stack traces to users)
- [ ] Logs are structured and readable, with request IDs, and never leak secrets
- [ ] Frontend reaches portfolio quality with loading / error / empty states across pages
- [ ] Tests run (`pytest`) and CI passes (backend lint+test, frontend lint+typecheck+build)
- [ ] README + docs let an interviewer understand value in 3–5 minutes
- [ ] Any statistic shown in the UI is a **real** count from the DB — no fabricated numbers

## 7. Copyright & Data Ethics

The architecture does **not** assume the right to copy full third-party articles. We store and display:

- Title, metadata, a short excerpt, the **GameScope-generated** summary, the source name, and the original URL.

We prefer RSS / official APIs / public feeds, and never rely on high-risk scraping. Where a source's
license explicitly allows more, that is handled per-source — but the default is metadata + excerpt + summary + link.

## 8. Honesty of Data

Dev/seed/fixture data is allowed and clearly labeled as such in the UI (a "Sample data" badge in dev).
Any number presented as a real statistic (articles processed, sources connected, embeddings generated,
health, job status) is computed from the database at request time. No fabricated demo numbers.

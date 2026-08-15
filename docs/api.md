# API Reference

Base URL: `/api/v1` (interactive Swagger UI at `/api/docs`, OpenAPI JSON at `/api/openapi.json`).

All responses are JSON. Errors use a single envelope; lists that paginate use a single page envelope.

## Conventions

### Error envelope

Every handled error returns:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Article 'foo' was not found.",
    "request_id": "b1d9c0f2-..."
  }
}
```

- `code` — stable machine-readable code (`INVALID_REQUEST`, `NOT_FOUND`, `UPSTREAM_ERROR`, `INTERNAL_ERROR`, …).
- `request_id` — also returned in the `X-Request-ID` response header and included in structured logs, so a
  user-visible failure can be traced to a log line.

### Pagination envelope

```json
{ "items": [ ... ], "total": 128, "page": 1, "page_size": 20 }
```

Query params: `page` (≥ 1, default 1), `page_size` (1–100, default 20).

---

## Endpoints

### `GET /health`
Liveness + dependency readiness.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "components": [{ "name": "database", "status": "ok", "detail": null }]
}
```

### `GET /news`
Paginated, filterable news list.

| Param | Type | Notes |
|---|---|---|
| `platform` | string | `PC` \| `PlayStation` \| `Xbox` \| `Nintendo` \| `Mobile` |
| `category` | string | `official` \| `media` \| `rumor` \| `update` \| `review` \| `deal` |
| `source` | string | source slug |
| `game` | string | game slug |
| `q` | string | quick text filter over title/summary |
| `sort` | string | `latest` (default) \| `importance` |
| `page`, `page_size` | int | pagination |

Returns `Page<ArticleListItem>`.

### `GET /news/{slug}`
Article detail + related. Returns `ArticleDetail` (adds `content_excerpt`, `fetched_at`, `related[]`).
`404` if the slug does not exist.

### `GET /games`
All tracked games. Returns `GameOut[]`.

### `GET /games/{slug}`
Game detail with article count. Returns `GameWithCount`. `404` if unknown.

### `GET /games/{slug}/news`
Paginated news for one game. Returns `Page<ArticleListItem>`.

### `GET /search?q=&limit=`
Traditional keyword search (hybrid FTS + vector, RRF-fused). `q` required, `limit` 1–50 (default 20).
Returns `SearchResponse { query, total, items: SearchResultItem[] }` (each item has a `score`).

### `POST /ai/search`
The centerpiece — grounded RAG answer.

Request:
```json
{ "query": "What's the latest on GTA VI?", "language": "en" }
```
(`query` 2–500 chars; `language` optional `en` | `zh` hint.)

Response `AISearchResponse`:
```json
{
  "answer": "…grounded text with [1][2] citation markers…",
  "sources": [
    { "index": 1, "title": "…", "source": "IGN", "url": "https://…",
      "published_at": "…", "is_official": false, "is_rumor": true }
  ],
  "related_articles": [{ "slug": "…", "title": "…" }],
  "query_metadata": {
    "game": "Grand Theft Auto VI", "platform": null, "topic": null,
    "time_range": "past_week", "intent": "news", "language": "en",
    "requires_freshness": true, "used_live": false,
    "retrieval": { "fts": 12, "vector": 15, "live": 0, "fused": 20, "reranked": 8 }
  },
  "generated_at": "…"
}
```

If retrieval finds nothing relevant, `answer` is an honest "insufficient information" message and
`sources` is empty — the system never fabricates an answer.

### `GET /trending?limit=`
Games with the most recent coverage. `limit` 1–20 (default 8). Returns `GameWithCount[]`.

### `GET /system/stats`
Real, DB-backed pipeline statistics. Returns `SystemStats` (article/embedding/source/game/search
counts, `last_ingest_at`, and the **active** `llm_provider` / `embedding_provider`).

### `GET /system/jobs?limit=`
Recent ingestion jobs. `limit` 1–100 (default 20). Returns `JobOut[]`
(status `pending` | `running` | `success` | `partial` | `failed`, plus found/stored/failed counts).

---

## Core types (abridged)

```ts
interface ArticleListItem {
  id: number; title: string; slug: string; summary: string | null;
  original_url: string; image_url: string | null; published_at: string | null;
  language: string; category: string; platforms: string[];
  is_official: boolean; is_rumor: boolean; is_sample: boolean; importance_score: number;
  source: SourceOut; games: GameOut[];
}
```

The frontend mirrors all of these in `frontend/src/lib/types.ts`, kept in sync with
`backend/app/schemas/*.py`.

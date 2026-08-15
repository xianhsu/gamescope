# AI Search (RAG)

AI Search is the centerpiece. It is **not** `question → LLM → answer`. It is a retrieval pipeline
that grounds every answer in real, retrieved articles and cites them — and honestly declines when
nothing relevant is found.

## The flow

```
Query
  → Query Understanding      (rules first, LLM fallback)
  → Metadata Filtering       (game / platform / time-range → SQL filters)
  → FTS + Vector Retrieval   (parallel, both filtered)
  → [Freshness gate → Live]  (optional, pluggable, config-driven)
  → Merge / Dedup / Rerank   (Reciprocal Rank Fusion, then rerank)
  → Context Builder          (numbered, budgeted context)
  → LLM Generation           (grounded, citation contract)
  → Answer + Sources + query_metadata
```

Implemented in `app/services/ai_search_service.py`, orchestrating `app/ai/*` and `app/retrieval/*`.

## 1. Query understanding

`app/ai/query_understanding.py` parses the raw query into structured metadata: `game` (via
name/alias matching), `platform`, `topic`, `time_range`, `intent`, `language`, and
`requires_freshness`. It is **rule-based first** (fast, deterministic, no cost) with an **LLM
fallback** for ambiguous queries. Language is detected (en/zh) and can be overridden by the request.

## 2. Metadata filtering

The parsed entities become `RetrievalFilters` (e.g. a `game_id`, a `platform`, and a `since`
timestamp derived from the time range). Both retrievers apply the same filters, so retrieval is
scoped before ranking — not filtered after the fact.

## 3. Hybrid retrieval

Two retrievers run against Postgres:

- **Full-text** (`FullTextRetriever`) — `websearch_to_tsquery` over the weighted `search_vector`
  (title A / summary B / excerpt C), GIN-indexed.
- **Vector** (`VectorRetriever`) — embeds the query and does cosine ANN over the `pgvector` HNSW
  index.

Limits are config-driven (`retrieval_fts_limit`, `retrieval_vector_limit`).

## 4. Freshness & the pluggable live retriever

A **config-driven** freshness gate decides whether to consult a live-web retriever
(`app/retrieval/live.py`), behind the *same* retriever interface. Live is used only when:

- `live_retrieval_enabled` is on, **and** the query `requires_freshness`, **and**
- there are too few local results (`freshness_min_local_results`), or the freshest local hit is
  older than `freshness_max_age_hours`.

By default live retrieval is disabled and the system is fully self-contained; the interface exists
to show the design seam without shipping a fragile scraper. `used_live` is reported in the response.

## 5. Fusion & rerank

Results are fused with **Reciprocal Rank Fusion** (`app/retrieval/hybrid.py`, `k = rrf_k = 60`).
RRF is rank-based, so it is robust to the incomparable score scales of FTS vs. vector search, and
de-duplicates documents that appear in multiple lists. A light **rerank**
(`app/retrieval/rerank.py`) then boosts official sources, recency, and multi-retriever agreement,
trimmed to `retrieval_context_limit` (default 8).

## 6. Context builder

`app/ai/rag.py` builds a **numbered, budgeted** context block: each retained document becomes a
numbered source `[1], [2], …` with source name, rumor/official tags, and its summary/excerpt. The
numbering is the contract the model must cite against.

## 7. Grounded generation

The LLM is prompted to answer **only** from the numbered context and to cite sources inline as
`[n]`. Rumors are labeled; official statements are distinguished. If the context is empty, the
answer is an honest **"insufficient information"** message (in the query's language) rather than a
guess. The frontend turns the `[n]` markers into links to the matching source card.

### Provider abstraction (no OpenAI lock-in)

Both the LLM and the embedder sit behind interfaces (`app/ai/llm`, `app/ai/embedding`) with two
implementations each:

- **OpenAI-compatible** — used when `LLM_PROVIDER=openai` / `EMBEDDING_PROVIDER=openai` and a key is
  set; `LLM_BASE_URL` allows any compatible endpoint.
- **Local, deterministic** — the default. The local LLM returns a deterministic extractive summary
  (and `"{}"` in JSON mode); the local embedder is a hashed bag-of-words vector, L2-normalized to
  the configured dimension. This makes the whole system runnable offline and CI hermetic.

## Observability

Every AI query writes a `SearchLog` (kind, result count, `used_live`, latency). The response
includes `query_metadata` with the parsed entities and the per-stage retrieval counts
(`fts / vector / live / fused / reranked`), which the UI renders so a reviewer can see the pipeline
working end to end.

# Data Pipeline (Ingestion)

Real gaming news enters GameScope through a **staged ingestion pipeline** with per-item fault
isolation. The design goal is reliability and honesty: one malformed item never kills a run, AI
failures never block basic ingestion, and every stored article keeps a source + original URL.

## Sources (provider pattern)

Sources implement a common `NewsSource` interface; the only concrete provider today is `RSSSource`,
but adding an API/web provider is a matter of implementing the same interface and registering it —
no pipeline changes. The curated set (5–8 per the brief) mixes **official** platform feeds and
**high-reliability** media outlets, all via public RSS:

| Slug | Name | Reliability |
|---|---|---|
| `playstation-blog` | PlayStation Blog | official |
| `xbox-wire` | Xbox Wire | official |
| `nintendo-life` | Nintendo Life | high |
| `pc-gamer` | PC Gamer | high |
| `ign` | IGN | high |
| `eurogamer` | Eurogamer | high |
| `rock-paper-shotgun` | Rock Paper Shotgun | high |

Adding a source is one dict entry in `app/ingestion/sources/registry.py`.

## Stages

For each source the orchestrator (`app/ingestion/pipeline.py`) runs:

```
FETCH → PARSE → NORMALIZE → CLEAN → DEDUP → CLASSIFY → ENTITIES → SUMMARIZE → EMBED → STORE
```

| Stage | Responsibility |
|---|---|
| **fetch** | Pull raw feed items from the provider (HTTP timeout from config). A fetch failure fails the *job* cleanly (recorded), not the process. |
| **parse** | Map raw feed entry → internal item (title, url, published, excerpt, image). |
| **normalize** | Canonicalize the URL (lowercase host, strip `www`, drop tracking params + fragment, trailing slash), compute a `content_hash`, build an excerpt. |
| **clean** | Strip HTML/boilerplate; enforce copyright-safe excerpt length. |
| **dedup** | Skip items already seen — by normalized URL (in-run + DB), by content hash, and by fuzzy title similarity against recent titles. |
| **classify** | Assign a category (official/media/rumor/update/review/deal) and `is_official`/`is_rumor` flags from source reliability + keyword signals. |
| **entities** | Link the article to known games via name/alias matching (writes `article_game` with a confidence). |
| **summarize** | Generate a short GameScope summary via the LLM provider (local deterministic by default). |
| **embed** | Compute the vector embedding for semantic retrieval. |
| **store** | Upsert the article + relationships; the FTS `search_vector` is maintained by a DB trigger. |

## Fault isolation

- **Per-item try/except + per-item commit.** Each article is committed on its own; a failure is
  rolled back, counted, logged (with the URL), and the loop continues. The job ends `success` if
  nothing failed, otherwise `partial`.
- **AI degradation is graceful.** If `summarize`/`embed` fail (or run without an API key), the
  article is still stored — enrichment is best-effort, ingestion is not.
- **Idempotency.** Re-running is safe: dedup by normalized URL + content hash means the same feed
  item is not stored twice.

## Job records & observability

Every run writes a `ProcessingJob` (`status`, `articles_found`, `articles_stored`,
`articles_failed`, timings). These power the `/system` page — the counts shown there are the real
values written by the pipeline, never fabricated.

## Running it

```bash
# Docker
docker compose exec backend python -m app.ingestion.runner

# Local
cd backend && python -m app.ingestion.runner
```

The runner iterates active sources, runs the pipeline for each, and prints a per-source summary
(found / stored / failed).

## Seed vs. real data

`python -m app.seed` inserts clearly-labeled sample articles (`is_sample=True`) so the UI is
populated without network access. The frontend renders a **"Sample"** badge on such items; they are
never presented as real, live news.

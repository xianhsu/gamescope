/**
 * TypeScript mirrors of the backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/*.py and the API contract.
 */

export interface SourceOut {
  id: number;
  name: string;
  slug: string;
  type: string;
  base_url: string | null;
  reliability_level: string;
}

export interface GameOut {
  id: number;
  name: string;
  slug: string;
  developer: string | null;
  publisher: string | null;
  release_date: string | null;
}

export interface GameWithCount extends GameOut {
  article_count: number;
}

export interface ArticleListItem {
  id: number;
  title: string;
  slug: string;
  summary: string | null;
  original_url: string;
  image_url: string | null;
  published_at: string | null;
  language: string;
  category: string;
  platforms: string[];
  is_official: boolean;
  is_rumor: boolean;
  is_sample: boolean;
  importance_score: number;
  source: SourceOut;
  games: GameOut[];
}

export interface ArticleDetail extends ArticleListItem {
  content_excerpt: string | null;
  fetched_at: string;
  related: ArticleListItem[];
}

export interface SearchResultItem extends ArticleListItem {
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  items: SearchResultItem[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ---- AI Search ----

export interface Citation {
  index: number;
  title: string;
  source: string;
  url: string;
  published_at: string | null;
  is_official: boolean;
  is_rumor: boolean;
}

export interface RelatedArticle {
  slug: string;
  title: string;
}

export interface RetrievalStats {
  fts: number;
  vector: number;
  live: number;
  fused: number;
  reranked: number;
}

export interface QueryMetadata {
  game: string | null;
  platform: string | null;
  topic: string | null;
  time_range: string | null;
  intent: string | null;
  language: string;
  requires_freshness: boolean;
  used_live: boolean;
  retrieval: RetrievalStats;
}

export interface AISearchResponse {
  answer: string;
  sources: Citation[];
  related_articles: RelatedArticle[];
  query_metadata: QueryMetadata;
  generated_at: string;
}

// ---- System ----

export interface ComponentStatus {
  name: string;
  status: string; // "ok" | "degraded" | "down"
  detail: string | null;
}

export interface HealthResponse {
  status: string; // "ok" | "degraded"
  version: string;
  environment: string;
  components: ComponentStatus[];
}

export interface SystemStats {
  articles_total: number;
  articles_summarized: number;
  embeddings_generated: number;
  sources_total: number;
  sources_active: number;
  games_total: number;
  searches_total: number;
  last_ingest_at: string | null;
  llm_provider: string;
  embedding_provider: string;
}

export interface JobOut {
  id: number;
  source_id: number | null;
  source_name: string | null;
  status: string;
  articles_found: number;
  articles_stored: number;
  articles_failed: number;
  started_at: string;
  finished_at: string | null;
}

// ---- Error envelope ----

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}

// ---- Query param helpers ----

export type NewsSort = "latest" | "importance";

export interface NewsQuery {
  platform?: string;
  category?: string;
  source?: string;
  game?: string;
  q?: string;
  sort?: NewsSort;
  page?: number;
  page_size?: number;
}

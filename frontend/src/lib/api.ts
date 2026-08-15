/**
 * Typed API client for the GameScope backend.
 *
 * - Single source of truth for the base URL (env-driven, falls back to localhost).
 * - Unwraps the backend's unified error envelope `{ error: { code, message, request_id } }`
 *   into a typed `ApiError` so the UI can render friendly messages + request ids.
 * - All calls run on the server by default (RSC) unless invoked from a client component.
 */

import type {
  AISearchResponse,
  ArticleDetail,
  ArticleListItem,
  GameOut,
  GameWithCount,
  HealthResponse,
  JobOut,
  NewsQuery,
  Page,
  SearchResponse,
  SystemStats,
} from "./types";

/**
 * Resolve the API base URL at request time. This must NOT be a module-level constant because
 * Next.js evaluates modules during build when only `NEXT_PUBLIC_*` vars are available; server
 * components running inside Docker then end up with the public `localhost:8000` URL instead of
 * the internal service URL (`backend:8000`).
 */
function resolveBaseUrl(): string {
  const fallback = "http://localhost:8000/api/v1";
  if (typeof window === "undefined") {
    // Server-side rendering / route handlers run inside the compose network and should reach
    // the backend by its service name when `API_INTERNAL_BASE_URL` is provided.
    return (process.env.API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? fallback)
      .replace(/\/$/, "");
  }
  // Browser only sees build-time public vars.
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? fallback).replace(/\/$/, "");
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;

  constructor(status: number, code: string, message: string, requestId: string | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

type QueryValue = string | number | boolean | null | undefined;

function buildQuery(params?: Record<string, QueryValue>): string {
  if (!params) return "";
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    usp.set(key, String(value));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Next.js fetch cache/revalidate controls. */
  revalidate?: number | false;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, revalidate = 0, signal } = options;
  const baseUrl = resolveBaseUrl();
  const url = `${baseUrl}${path}`;

  const init: RequestInit & { next?: { revalidate: number | false } } = {
    method,
    headers: { Accept: "application/json" },
    signal,
  };

  if (body !== undefined) {
    init.headers = { ...init.headers, "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }

  // Next.js data cache: default to no-store for freshness; callers may opt into ISR.
  if (revalidate === false || revalidate === 0) {
    init.cache = "no-store";
  } else {
    init.next = { revalidate };
  }

  let res: Response;
  try {
    res = await fetch(url, init);
  } catch (err) {
    // Network / DNS / connection refused (backend down).
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      `无法连接到 API（${baseUrl}）。后端是否在运行？`,
      null,
    );
  }

  if (!res.ok) {
    let code = "HTTP_ERROR";
    let message = `请求失败，状态码 ${res.status}`;
    let requestId: string | null = res.headers.get("x-request-id");
    try {
      const data = (await res.json()) as { error?: { code?: string; message?: string; request_id?: string } };
      if (data?.error) {
        code = data.error.code ?? code;
        message = data.error.message ?? message;
        requestId = data.error.request_id ?? requestId;
      }
    } catch {
      // Non-JSON error body; keep defaults.
    }
    throw new ApiError(res.status, code, message, requestId);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---- Endpoints ----

export const api = {
  health(revalidate: number | false = 0) {
    return request<HealthResponse>("/health", { revalidate });
  },

  systemStats(revalidate: number | false = 0) {
    return request<SystemStats>("/system/stats", { revalidate });
  },

  systemJobs(limit = 20, revalidate: number | false = 0) {
    return request<JobOut[]>(`/system/jobs${buildQuery({ limit })}`, { revalidate });
  },

  news(query: NewsQuery = {}, revalidate: number | false = 0) {
    return request<Page<ArticleListItem>>(`/news${buildQuery({ ...query })}`, { revalidate });
  },

  article(slug: string, revalidate: number | false = 0) {
    return request<ArticleDetail>(`/news/${encodeURIComponent(slug)}`, { revalidate });
  },

  games(revalidate: number | false = 0) {
    return request<GameOut[]>("/games", { revalidate });
  },

  game(slug: string, revalidate: number | false = 0) {
    return request<GameWithCount>(`/games/${encodeURIComponent(slug)}`, { revalidate });
  },

  gameNews(slug: string, page = 1, page_size = 12, revalidate: number | false = 0) {
    return request<Page<ArticleListItem>>(
      `/games/${encodeURIComponent(slug)}/news${buildQuery({ page, page_size })}`,
      { revalidate },
    );
  },

  trending(limit = 8, revalidate: number | false = 0) {
    return request<GameWithCount[]>(`/trending${buildQuery({ limit })}`, { revalidate });
  },

  search(q: string, limit = 20) {
    return request<SearchResponse>(`/search${buildQuery({ q, limit })}`);
  },

  aiSearch(query: string, language?: string, signal?: AbortSignal) {
    return request<AISearchResponse>("/ai/search", {
      method: "POST",
      body: { query, language },
      signal,
    });
  },
};

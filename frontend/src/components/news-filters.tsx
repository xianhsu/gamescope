"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Search, X } from "lucide-react";
import { cn, categoryLabel } from "@/lib/utils";

const PLATFORMS = ["PC", "PlayStation", "Xbox", "Nintendo", "Mobile"];
const CATEGORIES = ["official", "media", "rumor", "update", "review", "deal"];
const SORTS = [
  { value: "latest", label: "最新" },
  { value: "importance", label: "重要度" },
];

const selectClass =
  "h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring";

/**
 * URL-driven filter bar for the news list. Writes params (platform/category/sort/q)
 * back to the querystring; the server component re-fetches from those params.
 */
export function NewsFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [q, setQ] = useState(searchParams.get("q") ?? "");

  // Keep the local input in sync when the URL changes externally (e.g. back button).
  useEffect(() => {
    setQ(searchParams.get("q") ?? "");
  }, [searchParams]);

  const push = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value === null || value === "") params.delete(key);
        else params.set(key, value);
      }
      // Any filter change resets to page 1.
      params.delete("page");
      const qs = params.toString();
      router.push(qs ? `${pathname}?${qs}` : pathname);
    },
    [router, pathname, searchParams],
  );

  const platform = searchParams.get("platform") ?? "";
  const category = searchParams.get("category") ?? "";
  const sort = searchParams.get("sort") ?? "latest";
  const hasFilters = Boolean(platform || category || searchParams.get("q") || sort !== "latest");

  return (
    <div className="flex flex-wrap items-center gap-2">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          push({ q: q.trim() || null });
        }}
        className="relative flex-1 basis-56"
      >
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="按关键词筛选…"
          className="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </form>

      <select
        value={platform}
        onChange={(e) => push({ platform: e.target.value || null })}
        className={selectClass}
        aria-label="平台"
      >
        <option value="">全部平台</option>
        {PLATFORMS.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>

      <select
        value={category}
        onChange={(e) => push({ category: e.target.value || null })}
        className={selectClass}
        aria-label="分类"
      >
        <option value="">全部分类</option>
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>
            {categoryLabel(c)}
          </option>
        ))}
      </select>

      <select
        value={sort}
        onChange={(e) => push({ sort: e.target.value === "latest" ? null : e.target.value })}
        className={selectClass}
        aria-label="排序"
      >
        {SORTS.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      {hasFilters ? (
        <button
          onClick={() => {
            setQ("");
            router.push(pathname);
          }}
          className={cn(
            "inline-flex h-9 items-center gap-1 rounded-md border border-input px-3 text-sm text-muted-foreground hover:bg-accent",
          )}
        >
          <X className="h-3.5 w-3.5" />
          清除
        </button>
      ) : null}
    </div>
  );
}

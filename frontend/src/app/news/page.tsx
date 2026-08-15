import type { Metadata } from "next";
import { api, ApiError } from "@/lib/api";
import type { NewsSort } from "@/lib/types";
import { ArticleCard } from "@/components/article-card";
import { NewsFilters } from "@/components/news-filters";
import { Pagination } from "@/components/ui/pagination";
import { EmptyState, ErrorState } from "@/components/ui/states";

export const metadata: Metadata = { title: "资讯" };
export const dynamic = "force-dynamic";

const PAGE_SIZE = 12;

type SearchParams = Record<string, string | string[] | undefined>;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function NewsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const page = Math.max(1, Number(first(searchParams.page) ?? "1") || 1);
  const platform = first(searchParams.platform);
  const category = first(searchParams.category);
  const q = first(searchParams.q);
  const sortRaw = first(searchParams.sort);
  const sort: NewsSort = sortRaw === "importance" ? "importance" : "latest";

  const query = { platform, category, q, sort, page, page_size: PAGE_SIZE };

  let result;
  let error: ApiError | Error | null = null;
  try {
    result = await api.news(query);
  } catch (err) {
    error = err as Error;
  }

  const hrefFor = (p: number) => {
    const params = new URLSearchParams();
    if (platform) params.set("platform", platform);
    if (category) params.set("category", category);
    if (q) params.set("q", q);
    if (sort !== "latest") params.set("sort", sort);
    if (p > 1) params.set("page", String(p));
    const qs = params.toString();
    return qs ? `/news?${qs}` : "/news";
  };

  return (
    <div className="container py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">游戏资讯</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          汇总所有来源的游戏报道。使用筛选与排序来缩小范围。
        </p>
      </div>

      <div className="mb-6">
        <NewsFilters />
      </div>

      {error ? (
        <ErrorState
          title="无法加载资讯"
          message={error instanceof ApiError ? error.message : "发生未知错误。"}
          isNetwork={error instanceof ApiError && error.code === "NETWORK_ERROR"}
          requestId={error instanceof ApiError ? error.requestId : null}
        />
      ) : result && result.items.length > 0 ? (
        <>
          <p className="mb-4 text-sm text-muted-foreground">
            {result.total.toLocaleString()} 篇文章
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {result.items.map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
          <div className="mt-10">
            <Pagination
              page={result.page}
              pageSize={result.page_size}
              total={result.total}
              hrefFor={hrefFor}
            />
          </div>
        </>
      ) : (
        <EmptyState
          title="没有匹配的文章"
          description="尝试清除筛选条件或更换关键词搜索。"
        />
      )}
    </div>
  );
}

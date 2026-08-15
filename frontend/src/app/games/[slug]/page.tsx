import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Gamepad2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { ArticleCard } from "@/components/article-card";
import { Badge } from "@/components/ui/badge";
import { Pagination } from "@/components/ui/pagination";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { formatDate } from "@/lib/utils";

export const dynamic = "force-dynamic";
const PAGE_SIZE = 12;

type SearchParams = Record<string, string | string[] | undefined>;

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  try {
    const game = await api.game(params.slug);
    return { title: game.name };
  } catch {
    return { title: "Game" };
  }
}

export default async function GameDetailPage({
  params,
  searchParams,
}: {
  params: { slug: string };
  searchParams: SearchParams;
}) {
  const pageRaw = searchParams.page;
  const page = Math.max(1, Number(Array.isArray(pageRaw) ? pageRaw[0] : pageRaw ?? "1") || 1);

  let game;
  try {
    game = await api.game(params.slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    return (
      <div className="container py-10">
        <ErrorState
          title="Could not load this game"
          message={err instanceof ApiError ? err.message : "Unexpected error."}
          isNetwork={err instanceof ApiError && err.code === "NETWORK_ERROR"}
          requestId={err instanceof ApiError ? err.requestId : null}
        />
      </div>
    );
  }

  let news;
  let newsError: Error | null = null;
  try {
    news = await api.gameNews(params.slug, page, PAGE_SIZE);
  } catch (err) {
    newsError = err as Error;
  }

  const hrefFor = (p: number) => (p > 1 ? `/games/${params.slug}?page=${p}` : `/games/${params.slug}`);

  return (
    <div className="container py-8">
      <Link
        href="/games"
        className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        All games
      </Link>

      <div className="mb-8 flex items-start gap-4">
        <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Gamepad2 className="h-7 w-7" />
        </span>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{game.name}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            {game.developer ? <span>{game.developer}</span> : null}
            {game.publisher ? <span>· {game.publisher}</span> : null}
            {game.release_date ? <span>· Released {formatDate(game.release_date)}</span> : null}
            <Badge variant="neutral">{game.article_count} articles</Badge>
          </div>
        </div>
      </div>

      <h2 className="mb-4 text-xl font-bold tracking-tight">Coverage</h2>

      {newsError ? (
        <ErrorState
          message={newsError instanceof ApiError ? newsError.message : "Failed to load coverage."}
          isNetwork={newsError instanceof ApiError && newsError.code === "NETWORK_ERROR"}
        />
      ) : news && news.items.length > 0 ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {news.items.map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
          <div className="mt-10">
            <Pagination
              page={news.page}
              pageSize={news.page_size}
              total={news.total}
              hrefFor={hrefFor}
            />
          </div>
        </>
      ) : (
        <EmptyState
          title="No coverage yet"
          description="There are no articles linked to this game yet."
        />
      )}
    </div>
  );
}

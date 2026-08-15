import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { ArticleBadges } from "@/components/article-badges";
import { ArticleCard } from "@/components/article-card";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/states";
import { cn, formatDate, relativeTime } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  try {
    const article = await api.article(params.slug);
    return { title: article.title, description: article.summary ?? undefined };
  } catch {
    return { title: "文章" };
  }
}

export default async function ArticleDetailPage({ params }: { params: { slug: string } }) {
  let article;
  try {
    article = await api.article(params.slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    return (
      <div className="container py-10">
        <ErrorState
          title="无法加载该文章"
          message={err instanceof ApiError ? err.message : "发生未知错误。"}
          isNetwork={err instanceof ApiError && err.code === "NETWORK_ERROR"}
          requestId={err instanceof ApiError ? err.requestId : null}
        />
      </div>
    );
  }

  return (
    <article className="container max-w-3xl py-8">
      <Link
        href="/news"
        className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        返回资讯
      </Link>

      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span className="font-medium text-foreground">{article.source.name}</span>
        <span>·</span>
        <span>{formatDate(article.published_at)}</span>
        <span className="text-muted-foreground/60">({relativeTime(article.published_at)})</span>
      </div>

      <h1 className="text-3xl font-bold leading-tight tracking-tight">{article.title}</h1>

      <div className="mt-4">
        <ArticleBadges article={article} />
      </div>

      {article.is_sample ? (
        <p className="mt-4 rounded-md border border-dashed border-primary/40 bg-primary/5 px-4 py-3 text-sm text-primary">
          这是用于演示的<strong>示例/种子数据</strong>——它已明确标注，不会作为真实的实时新闻呈现。
        </p>
      ) : null}

      {article.image_url ? (
        <div className="mt-6 overflow-hidden rounded-lg border bg-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={article.image_url} alt="" className="w-full object-cover" />
        </div>
      ) : null}

      {article.summary ? (
        <p className="mt-6 text-lg leading-relaxed text-foreground/90">{article.summary}</p>
      ) : null}

      {article.content_excerpt ? (
        <div className="mt-4 whitespace-pre-line text-[15px] leading-relaxed text-muted-foreground">
          {article.content_excerpt}
        </div>
      ) : null}

      {/* Copyright-safe: we only store an excerpt + summary and link out to the source. */}
      <Card className="mt-8 flex flex-col gap-3 bg-muted/40 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium">在来源处阅读完整报道</p>
          <p className="text-xs text-muted-foreground">
            GameScope 仅存储摘要并链接到原始发布方。
          </p>
        </div>
        <a
          href={article.original_url}
          target="_blank"
          rel="noreferrer"
          className={cn(buttonVariants({ size: "sm" }), "shrink-0")}
        >
          打开原文
          <ExternalLink className="h-4 w-4" />
        </a>
      </Card>

      {article.games.length > 0 ? (
        <div className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            相关游戏
          </h2>
          <div className="flex flex-wrap gap-2">
            {article.games.map((g) => (
              <Link key={g.id} href={`/games/${g.slug}`}>
                <Badge variant="outline" className="hover:bg-accent">
                  {g.name}
                </Badge>
              </Link>
            ))}
          </div>
        </div>
      ) : null}

      {article.related.length > 0 ? (
        <div className="mt-12">
          <h2 className="mb-4 text-xl font-bold tracking-tight">相关文章</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {article.related.slice(0, 4).map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
        </div>
      ) : null}
    </article>
  );
}

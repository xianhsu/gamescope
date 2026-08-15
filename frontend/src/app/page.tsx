import Link from "next/link";
import { ArrowRight, Database, Layers, Search, Sparkles } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { ArticleListItem, GameWithCount, SystemStats } from "@/lib/types";
import { ArticleCard } from "@/components/article-card";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { cn } from "@/lib/utils";

// Home aggregates a few read endpoints; keep it fresh but cache briefly for snappiness.
export const revalidate = 30;

async function loadHome() {
  const [latest, trending, stats] = await Promise.allSettled([
    api.news({ sort: "latest", page: 1, page_size: 6 }, 30),
    api.trending(6, 30),
    api.systemStats(30),
  ]);
  return { latest, trending, stats };
}

export default async function HomePage() {
  const { latest, trending, stats } = await loadHome();

  const statsValue = stats.status === "fulfilled" ? stats.value : null;
  const latestItems: ArticleListItem[] =
    latest.status === "fulfilled" ? latest.value.items : [];
  const trendingGames: GameWithCount[] = trending.status === "fulfilled" ? trending.value : [];
  const anyError =
    latest.status === "rejected" && trending.status === "rejected" && stats.status === "rejected";
  const firstError =
    latest.status === "rejected"
      ? latest.reason
      : trending.status === "rejected"
        ? trending.reason
        : stats.status === "rejected"
          ? stats.reason
          : null;

  return (
    <div>
      <Hero stats={statsValue} />

      {anyError ? (
        <section className="container py-10">
          <ErrorState
            title="后端不可用"
            message={
              firstError instanceof ApiError
                ? firstError.message
                : "无法从 API 加载首页数据。"
            }
            isNetwork={firstError instanceof ApiError && firstError.code === "NETWORK_ERROR"}
            requestId={firstError instanceof ApiError ? firstError.requestId : null}
          />
        </section>
      ) : (
        <>
          {/* Trending games */}
          <section className="container py-10">
            <SectionHeader
              title="热门游戏"
              description="索引中近期报道最多的游戏。"
              href="/games"
              linkLabel="全部游戏"
            />
            {trending.status === "rejected" ? (
              <ErrorState message="加载热门游戏失败。" />
            ) : trendingGames.length === 0 ? (
              <EmptyState title="暂无游戏" description="运行数据摄取以填充游戏列表。" />
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {trendingGames.map((g) => (
                  <Link key={g.id} href={`/games/${g.slug}`}>
                    <Card className="flex items-center justify-between p-4 hover:shadow-md">
                      <div className="min-w-0">
                        <p className="truncate font-semibold">{g.name}</p>
                        <p className="truncate text-xs text-muted-foreground">
                          {g.developer ?? "未知开发商"}
                        </p>
                      </div>
                      <Badge variant="neutral">{g.article_count} articles</Badge>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </section>

          {/* Latest news */}
          <section className="container py-10">
            <SectionHeader
              title="最新资讯"
              description="来自所有来源的实时入库报道。"
              href="/news"
              linkLabel="全部资讯"
            />
            {latest.status === "rejected" ? (
              <ErrorState message="加载最新资讯失败。" />
            ) : latestItems.length === 0 ? (
              <EmptyState
                title="暂无文章"
                description="流水线尚未摄取任何新闻。"
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {latestItems.map((a) => (
                  <ArticleCard key={a.id} article={a} />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      <HowItWorks />
    </div>
  );
}

function Hero({ stats }: { stats: SystemStats | null }) {
  return (
    <section className="app-gradient border-b">
      <div className="container flex flex-col items-center py-16 text-center">
          <Badge variant="default" className="mb-4">
          <Sparkles className="h-3 w-3" />
          检索增强生成 · 混合检索
        </Badge>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          可以<span className="text-primary">提问</span>的游戏资讯
        </h1>
        <p className="mt-4 max-w-2xl text-balance text-muted-foreground">
          GameScope 从多个来源聚合游戏资讯，并用带引用来源、基于检索的 AI 来回答你的问题——每一条陈述都能追溯到真实文章。
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/ai" className={cn(buttonVariants({ size: "lg" }))}>
            <Sparkles className="h-4 w-4" />
            试用 AI 搜索
          </Link>
          <Link href="/news" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
            浏览资讯
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {stats ? (
          <div className="mt-10 grid grid-cols-2 gap-6 sm:grid-cols-4">
            <Stat label="文章" value={stats.articles_total} />
            <Stat label="向量嵌入" value={stats.embeddings_generated} />
            <Stat label="来源" value={stats.sources_active} />
            <Stat label="游戏" value={stats.games_total} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col">
      <span className="text-2xl font-bold tabular-nums">{value.toLocaleString()}</span>
      <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
    </div>
  );
}

function SectionHeader({
  title,
  description,
  href,
  linkLabel,
}: {
  title: string;
  description: string;
  href: string;
  linkLabel: string;
}) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4">
      <div>
        <h2 className="text-xl font-bold tracking-tight">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      <Link
        href={href}
        className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-primary hover:underline"
      >
        {linkLabel}
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}

function HowItWorks() {
  const items = [
    {
      icon: Search,
      title: "查询理解",
      body: "在检索之前，每个问题都会被解析出游戏、平台、主题与时效性等要素。",
    },
    {
      icon: Layers,
      title: "混合检索",
      body: "全文检索与向量相似度通过互易排序融合（RRF）进行整合。",
    },
    {
      icon: Database,
      title: "可信回答",
      body: "大模型仅基于检索到的上下文作答，并引用所用到的每一条来源。",
    },
  ];
  return (
    <section className="container py-12">
      <div className="grid gap-4 md:grid-cols-3">
        {items.map((it) => (
          <Card key={it.title} className="p-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <it.icon className="h-5 w-5" />
            </div>
            <h3 className="font-semibold">{it.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{it.body}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}

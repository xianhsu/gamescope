"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import {
  BadgeCheck,
  ExternalLink,
  FlaskConical,
  Loader2,
  Search,
  Sparkles,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { AISearchResponse } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/states";
import { GroundedAnswer } from "@/components/grounded-answer";
import { formatDate, relativeTime } from "@/lib/utils";

const EXAMPLES = [
  "下一款《侠盗猎车手》最近有什么消息？",
  "近期公布了哪些 PlayStation 独占游戏？",
  "总结一下关于任天堂次世代主机的传闻",
  "近期有哪些值得关注的 PC 游戏优惠",
];

const PIPELINE = [
  "查询理解",
  "元数据过滤",
  "全文 + 向量检索",
  "合并 · 去重 · 重排",
  "上下文构建",
  "大模型作答 + 引用",
];

export default function AiSearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AISearchResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function run(q: string) {
    const trimmed = q.trim();
    if (trimmed.length < 2 || loading) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    try {
      const res = await api.aiSearch(trimmed, "zh", controller.signal);
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError) setError(err);
      else if ((err as Error).name !== "AbortError")
        setError(new ApiError(0, "UNKNOWN", (err as Error).message, null));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container max-w-4xl py-8">
      <div className="mb-6">
        <div className="mb-2 inline-flex items-center gap-1.5 text-sm font-medium text-primary">
          <Sparkles className="h-4 w-4" />
          AI 搜索
        </div>
        <h1 className="text-2xl font-bold tracking-tight">询问游戏资讯</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          回答<strong>仅</strong>基于检索到的文章生成，并引用每一条来源。若没有找到相关内容，它会如实说明，而不是猜测。
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void run(query);
        }}
        className="flex gap-2"
      >
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：下一款塞尔达游戏有什么新消息？"
          className="h-11 w-full rounded-md border border-input bg-background pl-10 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        </div>
        <Button type="submit" size="lg" disabled={loading || query.trim().length < 2}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          提问
        </Button>
      </form>

      {!result && !loading && !error ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setQuery(ex);
                void run(ex);
              }}
              className="rounded-full border border-input bg-background px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              {ex}
            </button>
          ))}
        </div>
      ) : null}

      {loading ? <LoadingPipeline /> : null}

      {error ? (
        <div className="mt-6">
          <ErrorState
            title="AI 搜索失败"
            message={error.message}
            isNetwork={error.code === "NETWORK_ERROR"}
            requestId={error.requestId}
            action={
              <Button variant="outline" size="sm" onClick={() => void run(query)}>
                重试
              </Button>
            }
          />
        </div>
      ) : null}

      {result && !loading ? <ResultView result={result} /> : null}
    </div>
  );
}

function LoadingPipeline() {
  return (
    <Card className="mt-6 p-5">
      <div className="mb-4 flex items-center gap-2 text-sm font-medium">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        正在运行检索流水线…
      </div>
      <ol className="flex flex-wrap items-center gap-x-2 gap-y-2 text-xs text-muted-foreground">
        {PIPELINE.map((step, i) => (
          <li key={step} className="flex items-center gap-2">
            <span className="rounded-full bg-muted px-2.5 py-1">{step}</span>
            {i < PIPELINE.length - 1 ? <span className="text-muted-foreground/50">→</span> : null}
          </li>
        ))}
      </ol>
      <div className="mt-4 space-y-2">
        <div className="shimmer h-3 w-full rounded" />
        <div className="shimmer h-3 w-11/12 rounded" />
        <div className="shimmer h-3 w-4/5 rounded" />
      </div>
    </Card>
  );
}

function ResultView({ result }: { result: AISearchResponse }) {
  const m = result.query_metadata;
  return (
    <div className="mt-6 space-y-6">
      {/* Query metadata — makes the pipeline observable, not a black box. */}
      <Card className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            查询理解
          </p>
          {m.used_live ? (
            <Badge variant="default">已使用实时来源</Badge>
          ) : (
            <Badge variant="neutral">已索引来源</Badge>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {m.intent ? <Meta k="意图" v={m.intent} /> : null}
          {m.game ? <Meta k="游戏" v={m.game} /> : null}
          {m.platform ? <Meta k="平台" v={m.platform} /> : null}
          {m.topic ? <Meta k="主题" v={m.topic} /> : null}
          {m.time_range ? <Meta k="时间" v={m.time_range} /> : null}
          <Meta k="语言" v={m.language} />
          {m.requires_freshness ? <Meta k="时效性" v="需要" /> : null}
        </div>
        <div className="mt-3 flex flex-wrap gap-3 border-t pt-3 text-xs text-muted-foreground">
          <RetrievalStat label="全文检索" value={m.retrieval.fts} />
          <RetrievalStat label="向量" value={m.retrieval.vector} />
          {m.retrieval.live > 0 ? <RetrievalStat label="实时" value={m.retrieval.live} /> : null}
          <RetrievalStat label="融合" value={m.retrieval.fused} />
          <RetrievalStat label="重排" value={m.retrieval.reranked} />
        </div>
      </Card>

      {/* The grounded answer */}
      <Card className="p-6">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold">回答</h2>
        </div>
        <GroundedAnswer answer={result.answer} sources={result.sources} />
        <p className="mt-4 text-xs text-muted-foreground">
          生成于 {relativeTime(result.generated_at)} · 基于 {result.sources.length} 条来源
        </p>
      </Card>

      {/* Sources */}
      {result.sources.length > 0 ? (
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            来源
          </h2>
          <div className="space-y-2">
            {result.sources.map((s) => (
              <Card
                key={s.index}
                id={`source-${s.index}`}
                className="flex items-start gap-3 p-4 target:ring-2 target:ring-primary"
              >
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {s.index}
                </span>
                <div className="min-w-0 flex-1">
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-start gap-1 font-medium hover:text-primary"
                  >
                    <span className="line-clamp-2">{s.title}</span>
                    <ExternalLink className="mt-1 h-3 w-3 shrink-0" />
                  </a>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span>{s.source}</span>
                    {s.published_at ? (
                      <>
                        <span>·</span>
                        <span>{formatDate(s.published_at)}</span>
                      </>
                    ) : null}
                    {s.is_official ? (
                      <Badge variant="official">
                        <BadgeCheck className="h-3 w-3" />
                        官方
                      </Badge>
                    ) : null}
                    {s.is_rumor ? (
                      <Badge variant="rumor">
                        <FlaskConical className="h-3 w-3" />
                        传闻
                      </Badge>
                    ) : null}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ) : null}

      {/* Related internal articles */}
      {result.related_articles.length > 0 ? (
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            相关文章
          </h2>
          <div className="flex flex-wrap gap-2">
            {result.related_articles.map((r) => (
              <Link
                key={r.slug}
                href={`/news/${r.slug}`}
                className="rounded-md border border-input px-3 py-1.5 text-sm hover:bg-accent"
              >
                {r.title}
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Meta({ k, v }: { k: string; v: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-xs">
      <span className="text-muted-foreground">{k}:</span>
      <span className="font-medium">{v}</span>
    </span>
  );
}

function RetrievalStat({ label, value }: { label: string; value: number }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span>{label}</span>
      <span className="font-semibold tabular-nums text-foreground">{value}</span>
    </span>
  );
}

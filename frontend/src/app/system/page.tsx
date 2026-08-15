import type { Metadata } from "next";
import {
  Activity,
  Boxes,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  FileText,
  Gamepad2,
  Radio,
  Search,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ComponentStatus, HealthResponse, JobOut, SystemStats } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { formatDate, relativeTime } from "@/lib/utils";

export const metadata: Metadata = { title: "System" };
export const dynamic = "force-dynamic";

export default async function SystemPage() {
  const [statsR, healthR, jobsR] = await Promise.allSettled([
    api.systemStats(),
    api.health(),
    api.systemJobs(15),
  ]);

  const stats = statsR.status === "fulfilled" ? statsR.value : null;
  const health = healthR.status === "fulfilled" ? healthR.value : null;
  const jobs = jobsR.status === "fulfilled" ? jobsR.value : null;
  const allDown = !stats && !health && !jobs;

  return (
    <div className="container py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">系统状态</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          来自流水线的真实实时统计数据——此处没有任何伪造内容。
        </p>
      </div>

      {allDown ? (
        <ErrorState
          title="后端不可用"
          message="无法连接到任何系统接口。请确保 API 正在运行。"
          isNetwork
        />
      ) : (
        <div className="space-y-8">
          <HealthBar health={health} />
          {stats ? <StatsGrid stats={stats} /> : null}
          {stats ? <Providers stats={stats} /> : null}
          <Jobs jobs={jobs} failed={jobsR.status === "rejected"} />
        </div>
      )}
    </div>
  );
}

function statusVariant(status: string): "official" | "rumor" | "neutral" {
  if (status === "ok") return "official";
  if (status === "degraded") return "rumor";
  return "neutral";
}

const STATUS_LABELS: Record<string, string> = {
  ok: "正常",
  degraded: "降级",
  down: "故障",
};

function HealthBar({ health }: { health: HealthResponse | null }) {
  if (!health) {
    return <ErrorState title="健康检查失败" message="无法读取 /health。" isNetwork />;
  }
  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {health.status === "ok" ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          ) : (
            <Activity className="h-5 w-5 text-amber-600" />
          )}
          <span className="font-semibold">
            {health.status === "ok" ? "系统运行正常" : "系统性能下降"}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="neutral">v{health.version}</Badge>
          <Badge variant="neutral">{health.environment}</Badge>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {health.components.map((c: ComponentStatus) => (
          <div
            key={c.name}
            className="flex items-center justify-between rounded-md border bg-muted/30 px-3 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium capitalize">{c.name}</p>
              {c.detail ? (
                <p className="truncate text-xs text-muted-foreground">{c.detail}</p>
              ) : null}
            </div>
            <Badge variant={statusVariant(c.status)}>{STATUS_LABELS[c.status] ?? c.status}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

function StatsGrid({ stats }: { stats: SystemStats }) {
  const items = [
    { icon: FileText, label: "文章", value: stats.articles_total },
    { icon: Brain, label: "已总结", value: stats.articles_summarized },
    { icon: Boxes, label: "向量嵌入", value: stats.embeddings_generated },
    { icon: Radio, label: "活跃来源", value: stats.sources_active },
    { icon: Gamepad2, label: "游戏", value: stats.games_total },
    { icon: Search, label: "搜索次数", value: stats.searches_total },
  ];
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        流水线统计
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {items.map((it) => (
          <Card key={it.label} className="p-4">
            <it.icon className="mb-2 h-4 w-4 text-primary" />
            <p className="text-2xl font-bold tabular-nums">{it.value.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">{it.label}</p>
          </Card>
        ))}
      </div>
      {stats.last_ingest_at ? (
        <p className="mt-3 text-xs text-muted-foreground">
          最近一次摄取 {relativeTime(stats.last_ingest_at)}（{formatDate(stats.last_ingest_at)}）
        </p>
      ) : (
        <p className="mt-3 text-xs text-muted-foreground">尚未运行摄取任务。</p>
      )}
    </div>
  );
}

function Providers({ stats }: { stats: SystemStats }) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        AI 配置
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <Card className="flex items-center gap-3 p-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Cpu className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs text-muted-foreground">大模型供应商</p>
            <p className="font-semibold capitalize">{stats.llm_provider}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Database className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs text-muted-foreground">向量嵌入供应商</p>
            <p className="font-semibold capitalize">{stats.embedding_provider}</p>
          </div>
        </Card>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        供应商采用了抽象设计——平台默认使用确定性的本地供应商，无需 API 密钥；配置后也可切换到托管的云端模型。
      </p>
    </div>
  );
}

function Jobs({ jobs, failed }: { jobs: JobOut[] | null; failed: boolean }) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        最近的摄取任务
      </h2>
      {failed ? (
        <ErrorState message="无法加载最近的摄取任务。" />
      ) : !jobs || jobs.length === 0 ? (
        <EmptyState
          title="暂无任务"
          description="流水线运行后，摄取任务会显示在这里。"
        />
      ) : (
        <Card className="divide-y overflow-hidden p-0">
          {jobs.map((j) => (
            <div key={j.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="flex min-w-0 items-center gap-3">
                {j.status === "success" ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                ) : j.status === "failed" ? (
                  <XCircle className="h-4 w-4 shrink-0 text-red-600" />
                ) : (
                  <Activity className="h-4 w-4 shrink-0 text-amber-600" />
                )}
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">
                    {j.source_name ?? `来源 #${j.source_id ?? "?"}`}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {relativeTime(j.started_at)} · 发现 {j.articles_found} 篇 · 已存储{" "}
                    {j.articles_stored} 篇 · 失败 {j.articles_failed} 篇
                  </p>
                </div>
              </div>
              <Badge variant={j.status === "success" ? "official" : j.status === "failed" ? "rumor" : "neutral"}>
                {j.status === "success" ? "成功" : j.status === "failed" ? "失败" : "进行中"}
              </Badge>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

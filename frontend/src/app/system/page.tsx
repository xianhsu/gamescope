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
        <h1 className="text-2xl font-bold tracking-tight">System status</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Real, live statistics from the pipeline — nothing here is faked.
        </p>
      </div>

      {allDown ? (
        <ErrorState
          title="Backend unavailable"
          message="Could not reach any system endpoint. Make sure the API is running."
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

function HealthBar({ health }: { health: HealthResponse | null }) {
  if (!health) {
    return <ErrorState title="Health check failed" message="Could not read /health." isNetwork />;
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
            System {health.status === "ok" ? "healthy" : "degraded"}
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
            <Badge variant={statusVariant(c.status)}>{c.status}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

function StatsGrid({ stats }: { stats: SystemStats }) {
  const items = [
    { icon: FileText, label: "Articles", value: stats.articles_total },
    { icon: Brain, label: "Summarized", value: stats.articles_summarized },
    { icon: Boxes, label: "Embeddings", value: stats.embeddings_generated },
    { icon: Radio, label: "Active sources", value: stats.sources_active },
    { icon: Gamepad2, label: "Games", value: stats.games_total },
    { icon: Search, label: "Searches", value: stats.searches_total },
  ];
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Pipeline statistics
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
          Last ingest {relativeTime(stats.last_ingest_at)} ({formatDate(stats.last_ingest_at)})
        </p>
      ) : (
        <p className="mt-3 text-xs text-muted-foreground">No ingestion has run yet.</p>
      )}
    </div>
  );
}

function Providers({ stats }: { stats: SystemStats }) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        AI configuration
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <Card className="flex items-center gap-3 p-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Cpu className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs text-muted-foreground">LLM provider</p>
            <p className="font-semibold capitalize">{stats.llm_provider}</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Database className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs text-muted-foreground">Embedding provider</p>
            <p className="font-semibold capitalize">{stats.embedding_provider}</p>
          </div>
        </Card>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Providers are abstracted — the platform runs on a deterministic local provider without an API
        key, and switches to a hosted model when configured.
      </p>
    </div>
  );
}

function Jobs({ jobs, failed }: { jobs: JobOut[] | null; failed: boolean }) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Recent ingestion jobs
      </h2>
      {failed ? (
        <ErrorState message="Could not load recent jobs." />
      ) : !jobs || jobs.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Ingestion jobs will appear here once the pipeline runs."
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
                    {j.source_name ?? `Source #${j.source_id ?? "?"}`}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {relativeTime(j.started_at)} · {j.articles_found} found · {j.articles_stored}{" "}
                    stored · {j.articles_failed} failed
                  </p>
                </div>
              </div>
              <Badge variant={j.status === "success" ? "official" : j.status === "failed" ? "rumor" : "neutral"}>
                {j.status}
              </Badge>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

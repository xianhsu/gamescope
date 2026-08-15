import type { Metadata } from "next";
import Link from "next/link";
import { Gamepad2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { formatDate } from "@/lib/utils";

export const metadata: Metadata = { title: "Games" };
export const revalidate = 60;

export default async function GamesPage() {
  let games;
  let error: Error | null = null;
  try {
    games = await api.games(60);
  } catch (err) {
    error = err as Error;
  }

  return (
    <div className="container py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Games</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Titles tracked across ingested news. Open one to see all related coverage.
        </p>
      </div>

      {error ? (
        <ErrorState
          title="Could not load games"
          message={error instanceof ApiError ? error.message : "Unexpected error."}
          isNetwork={error instanceof ApiError && error.code === "NETWORK_ERROR"}
          requestId={error instanceof ApiError ? error.requestId : null}
        />
      ) : games && games.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {games.map((g) => (
            <Link key={g.id} href={`/games/${g.slug}`}>
              <Card className="flex h-full items-start gap-3 p-4 hover:shadow-md">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Gamepad2 className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="truncate font-semibold">{g.name}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {g.developer ?? "Unknown developer"}
                    {g.publisher ? ` · ${g.publisher}` : ""}
                  </p>
                  {g.release_date ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Released {formatDate(g.release_date)}
                    </p>
                  ) : null}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No games tracked yet"
          description="Games are extracted from ingested articles. Run the pipeline to populate this list."
        />
      )}
    </div>
  );
}

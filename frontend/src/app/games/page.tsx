import type { Metadata } from "next";
import Link from "next/link";
import { Gamepad2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { formatDate } from "@/lib/utils";

export const metadata: Metadata = { title: "游戏" };
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
        <h1 className="text-2xl font-bold tracking-tight">游戏</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          从入库新闻中追踪的游戏作品。点开任意一款可查看所有相关报道。
        </p>
      </div>

      {error ? (
        <ErrorState
          title="无法加载游戏"
          message={error instanceof ApiError ? error.message : "发生未知错误。"}
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
                    {g.developer ?? "未知开发商"}
                    {g.publisher ? ` · ${g.publisher}` : ""}
                  </p>
                  {g.release_date ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      发售于 {formatDate(g.release_date)}
                    </p>
                  ) : null}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          title="暂无已追踪的游戏"
          description="游戏从入库文章中提取。运行流水线以填充此列表。"
        />
      )}
    </div>
  );
}

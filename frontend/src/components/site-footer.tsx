import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t bg-muted/30">
      <div className="container flex flex-col gap-2 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-medium text-foreground">GameScope</span> — AI 驱动的游戏资讯情报平台。所有回答均基于检索到的来源。
        </p>
        <div className="flex items-center gap-4">
          <Link href="/system" className="hover:text-foreground">
            系统状态
          </Link>
          <a
            href="/api/docs"
            className="hover:text-foreground"
            target="_blank"
            rel="noreferrer"
          >
            API 文档
          </a>
        </div>
      </div>
    </footer>
  );
}

import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t bg-muted/30">
      <div className="container flex flex-col gap-2 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-medium text-foreground">GameScope</span> — AI-powered gaming news
          intelligence. Answers are grounded in retrieved sources.
        </p>
        <div className="flex items-center gap-4">
          <Link href="/system" className="hover:text-foreground">
            System status
          </Link>
          <a
            href="/api/docs"
            className="hover:text-foreground"
            target="_blank"
            rel="noreferrer"
          >
            API docs
          </a>
        </div>
      </div>
    </footer>
  );
}

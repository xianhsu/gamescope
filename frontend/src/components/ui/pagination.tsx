import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  /** Build an href for a given 1-based page number. */
  hrefFor: (page: number) => string;
}

/** Compact numeric pager with prev/next. Renders nothing for single-page results. */
export function Pagination({ page, pageSize, total, hrefFor }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  // Window of pages around the current page.
  const windowSize = 5;
  let start = Math.max(1, page - Math.floor(windowSize / 2));
  const end = Math.min(totalPages, start + windowSize - 1);
  start = Math.max(1, end - windowSize + 1);
  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const linkBase =
    "inline-flex h-9 min-w-9 items-center justify-center rounded-md border px-3 text-sm transition-colors";

  return (
    <nav className="flex flex-wrap items-center justify-center gap-1.5" aria-label="Pagination">
      <PagerLink
        href={hrefFor(page - 1)}
        disabled={page <= 1}
        className={linkBase}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </PagerLink>

      {start > 1 ? <span className="px-1 text-muted-foreground">…</span> : null}

      {pages.map((p) => (
        <Link
          key={p}
          href={hrefFor(p)}
          aria-current={p === page ? "page" : undefined}
          className={cn(
            linkBase,
            p === page
              ? "border-primary bg-primary text-primary-foreground"
              : "bg-background hover:bg-accent",
          )}
        >
          {p}
        </Link>
      ))}

      {end < totalPages ? <span className="px-1 text-muted-foreground">…</span> : null}

      <PagerLink
        href={hrefFor(page + 1)}
        disabled={page >= totalPages}
        className={linkBase}
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </PagerLink>
    </nav>
  );
}

function PagerLink({
  href,
  disabled,
  className,
  children,
  ...rest
}: {
  href: string;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
} & React.AriaAttributes) {
  if (disabled) {
    return (
      <span className={cn(className, "pointer-events-none opacity-40")} {...rest}>
        {children}
      </span>
    );
  }
  return (
    <Link href={href} className={cn(className, "bg-background hover:bg-accent")} {...rest}>
      {children}
    </Link>
  );
}

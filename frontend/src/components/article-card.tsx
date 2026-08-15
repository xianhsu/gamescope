import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { ArticleBadges } from "@/components/article-badges";
import { relativeTime } from "@/lib/utils";
import type { ArticleListItem } from "@/lib/types";

/**
 * News card used across Home / News list / Game detail.
 * Links to the internal detail page; the original source URL lives on the detail view.
 */
export function ArticleCard({ article }: { article: ArticleListItem }) {
  return (
    <Card className="group flex flex-col overflow-hidden hover:shadow-md">
      {article.image_url ? (
        <Link href={`/news/${article.slug}`} className="block overflow-hidden bg-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={article.image_url}
            alt=""
            loading="lazy"
            className="h-40 w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        </Link>
      ) : null}

      <div className="flex flex-1 flex-col p-5">
        <div className="mb-2 flex items-center justify-between gap-2 text-xs text-muted-foreground">
          <span className="truncate font-medium text-foreground/70">{article.source.name}</span>
          <span className="shrink-0">{relativeTime(article.published_at)}</span>
        </div>

        <Link href={`/news/${article.slug}`} className="group/title">
          <h3 className="line-clamp-2 text-base font-semibold leading-snug tracking-tight group-hover/title:text-primary">
            {article.title}
          </h3>
        </Link>

        {article.summary ? (
          <p className="mt-2 line-clamp-3 text-sm text-muted-foreground">{article.summary}</p>
        ) : null}

        <div className="mt-4 flex-1" />

        <div className="flex items-end justify-between gap-2">
          <ArticleBadges article={article} />
          <Link
            href={`/news/${article.slug}`}
            className="inline-flex shrink-0 items-center gap-0.5 text-xs font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100"
          >
            Read <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
      </div>
    </Card>
  );
}

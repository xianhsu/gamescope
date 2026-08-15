import { BadgeCheck, FlaskConical, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { categoryLabel } from "@/lib/utils";
import type { ArticleListItem } from "@/lib/types";

/**
 * Renders the trust/classification badges for an article.
 * `is_sample` is surfaced honestly so demo/seed data is never presented as real.
 */
export function ArticleBadges({
  article,
  showCategory = true,
}: {
  article: Pick<ArticleListItem, "category" | "platforms" | "is_official" | "is_rumor" | "is_sample">;
  showCategory?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {article.is_official ? (
        <Badge variant="official">
          <BadgeCheck className="h-3 w-3" />
          官方
        </Badge>
      ) : null}
      {article.is_rumor ? (
        <Badge variant="rumor">
          <FlaskConical className="h-3 w-3" />
          传闻
        </Badge>
      ) : null}
      {article.is_sample ? (
        <Badge variant="sample">
          <Sparkles className="h-3 w-3" />
          示例
        </Badge>
      ) : null}
      {/* Skip the category badge when it duplicates the official/rumor status badge. */}
      {showCategory && article.category &&
      article.category.toLowerCase() !== "official" &&
      article.category.toLowerCase() !== "rumor" ? (
        <Badge variant="neutral">{categoryLabel(article.category)}</Badge>
      ) : null}
      {article.platforms?.slice(0, 3).map((p) => (
        <Badge key={p} variant="outline">
          {p}
        </Badge>
      ))}
    </div>
  );
}

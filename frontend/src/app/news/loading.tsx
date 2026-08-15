import { ArticleCardSkeleton, Skeleton } from "@/components/ui/skeleton";

export default function NewsLoading() {
  return (
    <div className="container py-8">
      <Skeleton className="mb-2 h-8 w-48" />
      <Skeleton className="mb-6 h-4 w-80" />
      <Skeleton className="mb-6 h-9 w-full max-w-xl" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <ArticleCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

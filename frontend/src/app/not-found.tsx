import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <div className="container flex flex-col items-center justify-center py-24 text-center">
      <p className="text-5xl font-bold tracking-tight text-primary">404</p>
      <h1 className="mt-4 text-xl font-semibold">页面未找到</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        你访问的页面或文章不存在，可能已被移除。
      </p>
      <Link href="/" className={cn(buttonVariants({ variant: "outline", size: "sm" }), "mt-6")}>
        返回首页
      </Link>
    </div>
  );
}

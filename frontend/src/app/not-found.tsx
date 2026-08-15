import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <div className="container flex flex-col items-center justify-center py-24 text-center">
      <p className="text-5xl font-bold tracking-tight text-primary">404</p>
      <h1 className="mt-4 text-xl font-semibold">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        The page or article you are looking for does not exist or may have been removed.
      </p>
      <Link href="/" className={cn(buttonVariants({ variant: "outline", size: "sm" }), "mt-6")}>
        Back to home
      </Link>
    </div>
  );
}

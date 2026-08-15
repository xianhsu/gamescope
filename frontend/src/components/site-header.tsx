"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Gamepad2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Home", exact: true },
  { href: "/news", label: "News" },
  { href: "/games", label: "Games" },
  { href: "/ai", label: "AI Search" },
  { href: "/system", label: "System" },
];

export function SiteHeader() {
  const pathname = usePathname();

  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="container flex h-14 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Gamepad2 className="h-5 w-5" />
          </span>
          <span className="text-base">
            Game<span className="text-primary">Scope</span>
          </span>
        </Link>

        <nav className="flex items-center gap-0.5">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                isActive(item.href, item.exact)
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                item.href === "/ai" && "flex items-center gap-1",
              )}
            >
              {item.href === "/ai" ? <Sparkles className="h-3.5 w-3.5" /> : null}
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

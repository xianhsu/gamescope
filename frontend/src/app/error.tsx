"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/states";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface unexpected client errors in the console for debugging.
    console.error(error);
  }, [error]);

  const isNetwork =
    error.message.toLowerCase().includes("cannot reach the api") ||
    error.message.includes("无法连接");

  return (
    <div className="container py-16">
      <ErrorState
        title="页面发生错误"
        message={error.message || "渲染此页面时发生未知错误。"}
        isNetwork={isNetwork}
        action={
          <Button onClick={reset} variant="outline" size="sm">
            重试
          </Button>
        }
      />
    </div>
  );
}

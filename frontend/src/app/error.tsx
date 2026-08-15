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

  const isNetwork = error.message.toLowerCase().includes("cannot reach the api");

  return (
    <div className="container py-16">
      <ErrorState
        title="This page hit an error"
        message={error.message || "An unexpected error occurred while rendering this page."}
        isNetwork={isNetwork}
        action={
          <Button onClick={reset} variant="outline" size="sm">
            Try again
          </Button>
        }
      />
    </div>
  );
}

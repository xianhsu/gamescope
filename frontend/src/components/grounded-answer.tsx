import type { Citation } from "@/lib/types";

/**
 * Renders a grounded answer, turning inline `[n]` citation markers into
 * superscript links that jump to the matching source in the list below.
 * This makes the grounding contract visible: every claim points at a source.
 */
export function GroundedAnswer({ answer, sources }: { answer: string; sources: Citation[] }) {
  const byIndex = new Map(sources.map((s) => [s.index, s]));
  const parts = answer.split(/(\[\d+\])/g);

  return (
    <div className="whitespace-pre-line text-[15px] leading-relaxed text-foreground/90">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const idx = Number(match[1]);
          const source = byIndex.get(idx);
          if (source) {
            return (
              <a
                key={i}
                href={`#source-${idx}`}
                title={source.title}
                className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded bg-primary/10 px-1 align-super text-[10px] font-semibold text-primary hover:bg-primary/20"
              >
                {idx}
              </a>
            );
          }
        }
        return <span key={i}>{part}</span>;
      })}
    </div>
  );
}

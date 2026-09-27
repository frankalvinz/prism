"use client";

import type { ReviewSummary } from "@prism/shared";

export function VerdictCard({ review }: { review: ReviewSummary | null }) {
  if (!review) {
    return null;
  }

  return (
    <section className="rounded-xl border border-border bg-panel p-5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Verdict</p>
      <h2 className="mt-2 text-lg font-semibold text-foreground sm:text-xl">{review.headline}</h2>
      <p className="mt-3 text-sm leading-relaxed text-muted">{review.overview}</p>
      {review.highlights.length > 0 ? (
        <ul className="mt-4 space-y-1.5">
          {review.highlights.map((item) => (
            <li key={item} className="flex gap-2 text-sm text-foreground">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" aria-hidden />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

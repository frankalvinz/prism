"use client";

import { useState } from "react";
import type { ActionItem } from "@prism/shared";

import { cn } from "@/lib/utils";

export function ActionItems({ items }: { items: ActionItem[] }) {
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  if (items.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-border bg-panel p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">
        Action items
      </h2>
      <p className="mt-1 text-sm text-muted">Prioritized next steps from this analysis.</p>
      <ul className="mt-4 space-y-3">
        {items.map((item, index) => {
          const key = `${item.priority}-${item.title}-${index}`;
          const done = checked[key] ?? false;
          return (
            <li
              key={key}
              className={cn(
                "flex gap-3 rounded-lg border border-border bg-panel-2/60 p-3",
                done && "opacity-60",
              )}
            >
              <input
                type="checkbox"
                checked={done}
                onChange={(e) =>
                  setChecked((prev) => ({ ...prev, [key]: e.target.checked }))
                }
                className="mt-1 h-4 w-4 cursor-pointer accent-[var(--primary)]"
                aria-label={`Mark done: ${item.title}`}
              />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] text-muted">P{item.priority}</span>
                  <span className={cn("text-sm font-medium", done && "line-through")}>
                    {item.title}
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted">{item.detail}</p>
                {item.files.length > 0 ? (
                  <p className="mt-2 font-mono text-[11px] text-secondary">
                    {item.files.slice(0, 4).join(" · ")}
                    {item.files.length > 4 ? ` · +${item.files.length - 4} more` : ""}
                  </p>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

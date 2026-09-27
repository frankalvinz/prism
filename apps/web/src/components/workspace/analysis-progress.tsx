"use client";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  ANALYSIS_STEPS,
  phaseStatusMessage,
  phaseStepIndex,
  type UiPhase,
} from "@/lib/analysis/phases";

export function AnalysisProgress({ phase }: { phase: UiPhase }) {
  if (phase === "idle" || phase === "completed" || phase === "error") {
    return null;
  }

  const current = phaseStepIndex(phase);
  const message = phaseStatusMessage(phase);

  return (
    <Card className="px-4 py-3">
      <div className="mb-2 text-sm text-muted" role="status">
        {message}
      </div>
      <ol className="flex flex-wrap gap-2">
        {ANALYSIS_STEPS.map((step, index) => {
          const done = index < current;
          const active = index === current;
          return (
            <li
              key={step.id}
              className={cn(
                "inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-medium",
                done && "border-ok/40 bg-ok/10 text-ok",
                active && "border-primary/50 bg-primary/10 text-primary",
                !done && !active && "border-border text-muted",
              )}
            >
              <span className="font-mono">{String(index + 1).padStart(2, "0")}</span>
              {step.label}
            </li>
          );
        })}
      </ol>
    </Card>
  );
}

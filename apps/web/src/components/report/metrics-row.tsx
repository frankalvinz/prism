"use client";

import type { AnalysisReport } from "@prism/shared";

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-panel px-3 py-3">
      <div className="text-[11px] uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 font-mono text-xl text-foreground">{value}</div>
    </div>
  );
}

export function MetricsRow({ report }: { report: AnalysisReport }) {
  const { pr, statistics, risks } = report;
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
      <Metric label="Files changed" value={statistics.total_files} />
      <Metric label="Lines added" value={`+${statistics.additions}`} />
      <Metric label="Lines removed" value={`-${statistics.deletions}`} />
      <Metric label="Commits" value={pr.commits.length} />
      <Metric label="Findings" value={risks.length} />
    </div>
  );
}

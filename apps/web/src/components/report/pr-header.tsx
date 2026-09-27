"use client";

import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/outline";
import type { AnalysisReport, RiskLevel } from "@prism/shared";

import { cn } from "@/lib/utils";

const RISK_STYLE: Record<RiskLevel, string> = {
  low: "border-ok/40 bg-ok/10 text-ok",
  moderate: "border-warn/40 bg-warn/10 text-warn",
  high: "border-danger/40 bg-danger/10 text-danger",
};

export function PrHeader({ report }: { report: AnalysisReport }) {
  const { pr, review } = report;
  const riskLevel = review?.risk_level ?? "low";

  return (
    <header className="rounded-xl border border-border bg-panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-muted">
            <span>
              {pr.owner}/{pr.repository} · #{pr.number}
            </span>
            {pr.is_private ? (
              <span
                className="inline-flex items-center gap-1 rounded border border-warn/40 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-warn"
                title="Private repository"
              >
                <span aria-hidden className="font-bold">
                  P
                </span>
                Private
              </span>
            ) : null}
            <span
              className={cn(
                "inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                RISK_STYLE[riskLevel],
              )}
            >
              {riskLevel} risk
            </span>
          </div>
          <h1 className="text-xl font-semibold text-foreground sm:text-2xl">{pr.title}</h1>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
            <span>@{pr.author}</span>
            <span>
              {pr.base_branch} ← {pr.head_branch}
            </span>
            <span>{pr.commits.length} commit(s)</span>
          </div>
        </div>
        <a
          href={pr.html_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:border-secondary"
        >
          Open on GitHub
          <ArrowTopRightOnSquareIcon className="h-4 w-4" />
        </a>
      </div>
      {report.partial && report.partial_message ? (
        <p className="mt-4 rounded border border-warn/40 bg-warn/10 px-3 py-2 text-sm text-warn">
          {report.partial_message}
        </p>
      ) : null}
    </header>
  );
}

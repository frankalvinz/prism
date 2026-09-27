import type { Severity } from "@prism/shared";

import { cn } from "@/lib/utils";

const LABEL: Record<Severity, string> = {
  info: "Info",
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

const STYLE: Record<Severity, string> = {
  info: "border-border text-muted",
  low: "border-ok/40 text-ok",
  medium: "border-warn/50 text-warn",
  high: "border-danger/50 text-danger",
  critical: "border-danger bg-danger/10 text-danger",
};

const MARK: Record<Severity, string> = {
  info: "i",
  low: "L",
  medium: "M",
  high: "H",
  critical: "!",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide",
        STYLE[severity],
      )}
      title={`Severity: ${LABEL[severity]}`}
    >
      <span aria-hidden className="inline-flex h-4 w-4 items-center justify-center rounded-sm border border-current/40 text-[10px] font-bold">
        {MARK[severity]}
      </span>
      {LABEL[severity]}
    </span>
  );
}

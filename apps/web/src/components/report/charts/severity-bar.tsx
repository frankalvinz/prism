"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RiskFinding, Severity } from "@prism/shared";

import type { FindingsFilter } from "@/components/report/use-findings-filter";

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];
const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "var(--chart-4)",
  high: "var(--chart-4)",
  medium: "var(--chart-3)",
  low: "var(--chart-5)",
  info: "var(--chart-8)",
};

export function SeverityBar({
  risks,
  filter,
}: {
  risks: RiskFinding[];
  filter: FindingsFilter;
}) {
  const counts = new Map<Severity, number>();
  for (const r of risks) {
    counts.set(r.severity, (counts.get(r.severity) ?? 0) + 1);
  }
  const data = SEVERITY_ORDER.filter((s) => (counts.get(s) ?? 0) > 0).map((severity) => ({
    severity,
    count: counts.get(severity) ?? 0,
    fill: SEVERITY_COLOR[severity],
  }));

  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-muted">No severity data.</p>;
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="severity"
            tick={{ fill: "var(--muted)", fontSize: 11 }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "var(--muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--foreground)",
              fontSize: 12,
            }}
          />
          <Bar
            dataKey="count"
            name="Findings"
            radius={[4, 4, 0, 0]}
            onClick={(entry) => {
              const sev = (entry as { severity?: Severity }).severity;
              if (sev) filter.toggleSeverity(sev);
            }}
            style={{ cursor: "pointer" }}
          >
            {data.map((d) => (
              <Cell
                key={d.severity}
                fill={d.fill}
                opacity={!filter.severity || filter.severity === d.severity ? 1 : 0.35}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-muted">Click a bar to filter by severity</p>
    </div>
  );
}

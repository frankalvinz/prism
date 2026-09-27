"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChangeStatistics } from "@prism/shared";

function label(area: string) {
  return area.replaceAll("_", " ");
}

export function ChurnBar({ statistics }: { statistics: ChangeStatistics }) {
  const data = Object.entries(statistics.area_churn ?? {}).map(([area, churn]) => ({
    area: label(area),
    additions: churn.additions,
    deletions: churn.deletions,
  }));

  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-muted">No churn data.</p>;
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="area"
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
          <Legend wrapperStyle={{ fontSize: 12, color: "var(--muted)" }} />
          <Bar dataKey="additions" stackId="churn" fill="var(--chart-5)" name="Additions" />
          <Bar dataKey="deletions" stackId="churn" fill="var(--chart-4)" name="Deletions" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

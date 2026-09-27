"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { RiskFinding } from "@prism/shared";

import { chartColor } from "@/constants/theme";
import type { FindingsFilter } from "@/components/report/use-findings-filter";

function label(category: string) {
  return category.replaceAll("_", " ");
}

export function FindingsDonut({
  risks,
  filter,
}: {
  risks: RiskFinding[];
  filter: FindingsFilter;
}) {
  const counts = new Map<string, number>();
  for (const r of risks) {
    counts.set(r.category, (counts.get(r.category) ?? 0) + 1);
  }
  const data = [...counts.entries()].map(([name, value], i) => ({
    name,
    value,
    fill: chartColor(i),
  }));
  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return <p className="py-8 text-center text-sm text-muted">No findings to chart.</p>;
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={48}
            outerRadius={80}
            paddingAngle={2}
            onClick={(entry) => {
              const cat = (entry as { name?: string }).name;
              if (cat) filter.toggleCategory(cat as RiskFinding["category"]);
            }}
            style={{ cursor: "pointer" }}
          >
            {data.map((d) => (
              <Cell
                key={d.name}
                fill={d.fill}
                stroke={filter.category === d.name ? "var(--foreground)" : "transparent"}
                strokeWidth={filter.category === d.name ? 2 : 0}
                opacity={!filter.category || filter.category === d.name ? 1 : 0.35}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name) => {
              const n = Number(value) || 0;
              const pct = total ? Math.round((n / total) * 100) : 0;
              return [`${n} (${pct}%)`, label(String(name))];
            }}
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--foreground)",
              fontSize: 12,
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-muted">Click a slice to filter findings</p>
    </div>
  );
}

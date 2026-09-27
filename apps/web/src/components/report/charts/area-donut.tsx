"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ChangeStatistics } from "@prism/shared";

import { chartColor } from "@/constants/theme";

function label(area: string) {
  return area.replaceAll("_", " ");
}

export function AreaDonut({ statistics }: { statistics: ChangeStatistics }) {
  const entries = Object.entries(statistics.area_distribution ?? {});
  const data = entries.map(([name, value], i) => ({
    name,
    value,
    fill: chartColor(i),
  }));
  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return <p className="py-8 text-center text-sm text-muted">No area distribution.</p>;
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
          >
            {data.map((d) => (
              <Cell key={d.name} fill={d.fill} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name) => {
              const n = Number(value) || 0;
              const pct = total ? Math.round((n / total) * 100) : 0;
              return [`${n} files (${pct}%)`, label(String(name))];
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
      <ul className="mt-2 flex flex-wrap justify-center gap-x-3 gap-y-1 text-[11px] text-muted">
        {data.map((d) => (
          <li key={d.name} className="inline-flex items-center gap-1.5 capitalize">
            <span className="h-2 w-2 rounded-full" style={{ background: d.fill }} />
            {label(d.name)}
          </li>
        ))}
      </ul>
    </div>
  );
}

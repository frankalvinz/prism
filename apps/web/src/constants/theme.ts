export type Theme = "light" | "dark";

export const DEFAULT_THEME: Theme = "dark";

export const SPECTRUM = [
  { label: "Change overview", colorVar: "var(--spectrum-blue)", token: "spectrum-blue" },
  { label: "Tests", colorVar: "var(--spectrum-green)", token: "spectrum-green" },
  { label: "Risks", colorVar: "var(--spectrum-yellow)", token: "spectrum-yellow" },
  { label: "Security patterns", colorVar: "var(--spectrum-red)", token: "spectrum-red" },
] as const;

export const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
  "var(--chart-7)",
  "var(--chart-8)",
] as const;

export function chartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length]!;
}

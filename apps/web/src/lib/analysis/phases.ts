export type UiPhase =
  | "idle"
  | "parsing"
  | "fetching"
  | "analyzing"
  | "completed"
  | "error";

export const ANALYSIS_STEPS = [
  { id: "parsing", label: "Parse" },
  { id: "fetching", label: "Fetch" },
  { id: "analyzing", label: "Analyze" },
] as const;

export function phaseStepIndex(phase: UiPhase): number {
  if (phase === "parsing") return 0;
  if (phase === "fetching") return 1;
  if (phase === "analyzing" || phase === "completed") return 2;
  return -1;
}

export function phaseStatusMessage(phase: UiPhase): string | null {
  if (phase === "parsing") return "Parsing pull request URL…";
  if (phase === "fetching") return "Fetching pull request and changed files from GitHub…";
  if (phase === "analyzing") return "Running deterministic analysis…";
  return null;
}

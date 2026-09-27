export const WELCOME_STEPS = [
  {
    title: "Paste or pick a PR",
    body: "Drop in a GitHub pull request URL, try the demo, or choose from your open PRs after signing in.",
  },
  {
    title: "Deterministic analysis",
    body: "PRISM fetches metadata and diffs, then runs rule-based analyzers — no LLM or API key required.",
  },
  {
    title: "Reviewer-ready report",
    body: "Get change stats, risks, testing gaps, complexity notes, and focused review questions.",
  },
] as const;

export const WELCOME_TRUST = [
  "Unlock private repositories and your open pull requests list.",
  "Uses the GitHub OAuth repo scope so PRISM can read private diffs.",
  "Your token is encrypted in an HttpOnly cookie — never stored in a database or exposed to browser JavaScript.",
  "PRISM never clones repositories or executes pull request code.",
  "Disconnect any time from the account menu.",
] as const;

export const QUICK_START_CHECKS = [
  "Change statistics and file roles",
  "Risk heuristics (auth, data, deps)",
  "Testing coverage signals",
  "Complexity observations",
  "Focused review questions",
] as const;

export const SITE_COPYRIGHT = "© 2026 MonarchX — Frank Ekwomadu";

export const SITE_FOOTER_NOTE =
  "PRISM analyzes PR metadata and diffs only. It never executes repository code. Private repos require signing in with GitHub.";

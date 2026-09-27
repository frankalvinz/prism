# Analysis Engine

PRISM's analysis engine is deterministic and fixture-testable.

## Analyzers

| Analyzer | Purpose |
|----------|---------|
| ChangeAnalyzer | File/line statistics, role & language distributions |
| TestAnalyzer | Test-file change detection and cautious wording |
| RiskAnalyzer | Path/keyword **risk indicators** (not vulns) |
| DependencyAnalyzer | Manifest diffs (npm, pip, go, etc.) |
| ComplexityAnalyzer | Python AST + radon; JS/TS heuristics; fallback line stats |
| ImpactAnalyzer | Lightweight import/path edges with confidence |
| ReviewQuestionGenerator | Questions derived only from actual findings |

## Finding contract

Every finding includes:

- `severity`, `category`, `title`, `description`
- `evidence` (concrete observation)
- `confidence` (0–1)
- `source` (`deterministic` | `ai`)

## Language support

**Supported with deeper analysis:** Python, JavaScript, TypeScript  
**Fallback:** line-based statistics and file-level observations

## Wording rules

- Prefer indicators: “Authentication-related code was modified.”
- Never claim confirmed vulnerabilities from pattern matches.
- Tests: “PRISM did not detect corresponding test-file changes.”

## Limits & partial analysis

When limits are exceeded, PRISM returns a report for the analyzed subset and sets:

- `partial: true`
- `partial_message`: e.g. “Analysis completed for 80 of 150 changed files.”

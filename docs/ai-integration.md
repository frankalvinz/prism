# AI Integration (Future)

AI is **optional**. The deterministic engine must produce a complete useful report with `ai_analysis = null`.

## Why AI is optional

- Portfolio demos and offline use must work without paid APIs or local models.
- Deterministic findings are explainable and testable.
- AI should **enhance**, not gate, analysis.

## AnalysisProvider

```python
class AnalysisProvider(Protocol):
    async def analyze(
        self,
        pull_request: PullRequest,
        analysis_report: AnalysisReport,
    ) -> AIAnalysis | None: ...
```

MVP providers:

- `NullAnalysisProvider` — used when `AI_ENABLED=false`
- `DeterministicAnalysisProvider` — contract placeholder (returns `None`)

Future providers (not implemented in MVP):

- `OllamaAnalysisProvider`
- `OpenAIAnalysisProvider`
- `AnthropicAnalysisProvider`

## Configuration

```env
AI_ENABLED=false
AI_PROVIDER=ollama
AI_MODEL=llama3.1
AI_BASE_URL=http://localhost:11434
```

## Structured context for LLMs

Providers should receive PRISM's structured report slices, not only the raw PR:

```json
{
  "pr_summary": {},
  "statistics": {},
  "risk_findings": [],
  "complexity_findings": [],
  "test_findings": [],
  "dependency_changes": [],
  "relevant_diff_chunks": []
}
```

This reduces tokens and keeps prompts grounded in already-computed evidence.

## Separating AI vs deterministic findings

- Deterministic findings use `source: deterministic`.
- AI findings use `source: ai` and live under `analysis_report.ai_analysis`.
- UI should label AI content as probabilistic assistance.

## Prompt injection stance

Treat PR titles, descriptions, comments, and diffs as **untrusted**.

- Never execute model-suggested tool calls against user repos.
- Prefer structured JSON outputs validated by Pydantic.
- Do not let model text override severity enums without validation.
- Strip or bound untrusted text before inclusion in prompts.

## Important caveat

AI-generated observations are probabilistic and **must not** be presented as definitive security findings.

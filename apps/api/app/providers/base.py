from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from app.models.domain import AIAnalysis, AnalysisReport, PullRequest


@runtime_checkable
class AnalysisProvider(Protocol):
    """Optional AI enhancement provider. Never required for a complete report."""

    @property
    def name(self) -> str: ...

    async def analyze(self, pull_request: PullRequest, analysis_report: AnalysisReport) -> AIAnalysis | None: ...


class NullAnalysisProvider:
    """Default provider used when AI is disabled."""

    @property
    def name(self) -> str:
        return "null"

    async def analyze(
        self, pull_request: PullRequest, analysis_report: AnalysisReport
    ) -> AIAnalysis | None:
        return None


class DeterministicAnalysisProvider:
    """
    Placeholder that demonstrates the provider contract without calling an LLM.
    Returns None so AI remains optional; can be swapped for Ollama/OpenAI later.
    """

    @property
    def name(self) -> str:
        return "deterministic"

    async def analyze(
        self, pull_request: PullRequest, analysis_report: AnalysisReport
    ) -> AIAnalysis | None:
        # Intentionally does not invent AI content in MVP.
        _ = (pull_request, analysis_report, datetime.now(UTC))
        return None

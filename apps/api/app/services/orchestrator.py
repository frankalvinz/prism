import asyncio
from datetime import UTC, datetime

from app.analyzers import (
    ChangeAnalyzer,
    ComplexityAnalyzer,
    DependencyAnalyzer,
    ImpactAnalyzer,
    ReviewQuestionGenerator,
    RiskAnalyzer,
    TestAnalyzer,
)
from app.analyzers.summary import SummaryGenerator
from app.core.config import Settings
from app.core.exceptions import GitHubNotFoundError
from app.core.logging import get_logger
from app.github.client import GitHubClient
from app.github.normalizer import normalize_pull_request
from app.models.domain import AnalysisReport, RiskFinding
from app.models.enums import Severity
from app.providers import AnalysisProvider, NullAnalysisProvider
from app.services.cache import AnalysisCache, InMemoryCache, cache_key

logger = get_logger(__name__)


class AnalysisOrchestrator:
    def __init__(
        self,
        *,
        github: GitHubClient,
        settings: Settings,
        cache: AnalysisCache | None = None,
        ai_provider: AnalysisProvider | None = None,
        viewer_login: str | None = None,
    ) -> None:
        self._github = github
        self._settings = settings
        self._cache = cache if cache is not None else InMemoryCache()
        self._ai = ai_provider or NullAnalysisProvider()
        self._viewer_login = viewer_login
        self._change = ChangeAnalyzer()
        self._test = TestAnalyzer()
        self._risk = RiskAnalyzer()
        self._deps = DependencyAnalyzer()
        self._complexity = ComplexityAnalyzer()
        self._impact = ImpactAnalyzer()
        self._questions = ReviewQuestionGenerator()
        self._summary = SummaryGenerator()

    async def analyze(self, owner: str, repo: str, number: int) -> AnalysisReport:
        started = datetime.now(UTC)
        logger.info(
            "analysis.started repository=%s/%s pr=%s viewer=%s",
            owner,
            repo,
            number,
            self._viewer_login or "anonymous",
        )

        try:
            raw_pr = await self._github.get_pull_request(owner, repo, number)
        except GitHubNotFoundError:
            await self._raise_disambiguated_not_found(owner, repo, number)
            raise  # pragma: no cover - unreachable

        head_sha = str((raw_pr.get("head") or {}).get("sha") or "")
        key = cache_key(
            owner,
            repo,
            number,
            head_sha,
            viewer_login=self._viewer_login,
        )

        if self._settings.cache_enabled:
            cached = self._cache.get(key)
            if isinstance(cached, AnalysisReport):
                logger.info("analysis.cache_hit key=%s", key)
                return cached

        raw_files, raw_commits = await asyncio.gather(
            self._github.get_pull_request_files(owner, repo, number),
            self._github.get_pull_request_commits(owner, repo, number),
        )

        pr, partial, partial_message = normalize_pull_request(
            raw_pr, raw_files, raw_commits, self._settings
        )

        stats, change_findings = await asyncio.to_thread(self._change.analyze, pr)
        testing = await asyncio.to_thread(self._test.analyze, pr)
        risks = await asyncio.to_thread(self._risk.analyze, pr)
        dependencies = await asyncio.to_thread(self._deps.analyze, pr)
        complexity_obs, complexity_findings = await asyncio.to_thread(self._complexity.analyze, pr)
        edges = await asyncio.to_thread(self._impact.analyze, pr)

        all_risks = self._merge_findings(
            change_findings + risks + complexity_findings + testing.findings
        )
        areas = {f.area for f in pr.changed_files}
        questions = self._questions.generate(
            risks=all_risks,
            testing=testing,
            dependencies=dependencies,
            complexity_findings=complexity_findings,
            areas=areas,
        )
        review = self._summary.generate(
            pr=pr,
            stats=stats,
            risks=all_risks,
            testing=testing,
            dependencies=dependencies,
            partial_message=partial_message,
        )

        report = AnalysisReport(
            pr=pr,
            summary=review.overview,
            statistics=stats,
            complexity=complexity_obs,
            risks=all_risks,
            testing=testing,
            dependencies=dependencies,
            dependency_edges=edges,
            review_questions=questions,
            analyzed_at=datetime.now(UTC),
            analyzer_version=self._settings.analyzer_version,
            partial=partial,
            partial_message=partial_message,
            files_analyzed=len(pr.changed_files),
            files_total=pr.changed_files_count or len(raw_files),
            ai_analysis=None,
            review=review,
        )

        if self._settings.ai_enabled:
            ai = await self._ai.analyze(pr, report)
            report.ai_analysis = ai

        if self._settings.cache_enabled:
            self._cache.set(key, report, self._settings.cache_ttl_seconds)

        duration_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
        logger.info(
            "analysis.completed repository=%s/%s pr=%s files=%s duration_ms=%s",
            owner,
            repo,
            number,
            len(pr.changed_files),
            duration_ms,
        )
        return report

    async def _raise_disambiguated_not_found(self, owner: str, repo: str, number: int) -> None:
        try:
            await self._github.get_repository(owner, repo)
            raise GitHubNotFoundError(
                f"Pull request #{number} doesn't exist in {owner}/{repo}.",
                details={"owner": owner, "repo": repo, "number": number, "hint": "missing_pr"},
            )
        except GitHubNotFoundError as repo_exc:
            if repo_exc.details.get("hint") == "missing_pr":
                raise
            if self._viewer_login:
                raise GitHubNotFoundError(
                    "Repository not found, or your GitHub account doesn't have access.",
                    details={
                        "owner": owner,
                        "repo": repo,
                        "number": number,
                        "hint": "no_access",
                    },
                ) from repo_exc
            raise GitHubNotFoundError(
                "Repository not found or private. Connect GitHub to analyze private repositories.",
                details={
                    "owner": owner,
                    "repo": repo,
                    "number": number,
                    "hint": "connect_github",
                },
            ) from repo_exc

    def _merge_findings(self, findings: list[RiskFinding]) -> list[RiskFinding]:
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        seen: set[str] = set()
        unique: list[RiskFinding] = []
        for f in findings:
            if f.id in seen:
                continue
            seen.add(f.id)
            unique.append(f)
        unique.sort(key=lambda x: (severity_order.get(x.severity, 9), x.category.value))
        return unique

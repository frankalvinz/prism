"""Deterministic, human-readable review summary and action items."""

from __future__ import annotations

from app.models.domain import (
    ActionItem,
    ChangeStatistics,
    DependencyChange,
    PullRequest,
    ReviewSummary,
    RiskFinding,
    TestingAnalysis,
)
from app.models.enums import FileArea, RiskCategory, RiskLevel, Severity

_AREA_LABELS: dict[str, str] = {
    FileArea.UI.value: "UI",
    FileArea.API.value: "API",
    FileArea.SERVICE.value: "services",
    FileArea.DATA_MODEL.value: "data models",
    FileArea.DATABASE.value: "database",
    FileArea.AUTH.value: "auth",
    FileArea.CONFIG.value: "configuration",
    FileArea.INFRA.value: "infrastructure",
    FileArea.CI.value: "CI/CD",
    FileArea.TEST.value: "tests",
    FileArea.DOCS.value: "docs",
    FileArea.STYLES.value: "styles",
    FileArea.DEPENDENCY.value: "dependencies",
    FileArea.CONSTANTS.value: "constants",
    FileArea.HOOKS_STATE.value: "hooks/state",
    FileArea.OTHER.value: "other",
}

_CATEGORY_LABELS: dict[RiskCategory, str] = {
    RiskCategory.AUTHENTICATION: "authentication",
    RiskCategory.AUTHORIZATION: "authorization",
    RiskCategory.DATABASE: "database/migrations",
    RiskCategory.API: "API routes",
    RiskCategory.DEPENDENCIES: "dependencies",
    RiskCategory.CONFIGURATION: "configuration",
    RiskCategory.INFRASTRUCTURE: "infrastructure",
    RiskCategory.SECURITY: "security-sensitive code",
    RiskCategory.PAYMENTS: "payments",
    RiskCategory.DATA_HANDLING: "data handling",
    RiskCategory.CI_CD: "CI/CD",
    RiskCategory.ENVIRONMENT: "environment config",
    RiskCategory.TESTING: "testing gaps",
    RiskCategory.CHANGE: "change size",
    RiskCategory.COMPLEXITY: "complexity",
    RiskCategory.IMPACT: "impact",
    RiskCategory.OTHER: "other",
}

_WEIGHT = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
    Severity.INFO: 0,
}


class SummaryGenerator:
    def generate(
        self,
        *,
        pr: PullRequest,
        stats: ChangeStatistics,
        risks: list[RiskFinding],
        testing: TestingAnalysis,
        dependencies: list[DependencyChange],
        partial_message: str | None = None,
    ) -> ReviewSummary:
        risk_level = self._risk_level(risks, stats, testing)
        dominant = self._dominant_areas(stats)
        highlights = self._highlights(pr, stats, risks, testing, dependencies)
        action_items = self._action_items(risks, testing, dependencies, stats)
        overview = self._overview(
            pr, stats, risks, testing, dominant, risk_level, partial_message
        )
        headline = self._headline(risk_level, dominant, testing, risks)
        return ReviewSummary(
            risk_level=risk_level,
            headline=headline,
            overview=overview,
            highlights=highlights,
            action_items=action_items,
        )

    def _risk_level(
        self,
        risks: list[RiskFinding],
        stats: ChangeStatistics,
        testing: TestingAnalysis,
    ) -> RiskLevel:
        score = sum(_WEIGHT.get(r.severity, 0) for r in risks)
        if any(r.id.startswith("test-no-corresponding") for r in testing.findings):
            score += 2
        if stats.total_files >= 30 or stats.additions + stats.deletions >= 1000:
            score += 2
        if score >= 8 or any(r.severity == Severity.CRITICAL for r in risks):
            return RiskLevel.HIGH
        if score >= 3 or any(r.severity == Severity.HIGH for r in risks):
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    def _dominant_areas(self, stats: ChangeStatistics) -> list[tuple[str, int]]:
        items = sorted(stats.area_distribution.items(), key=lambda x: x[1], reverse=True)
        return [(k, v) for k, v in items if k != FileArea.OTHER.value][:3] or items[:3]

    def _headline(
        self,
        risk_level: RiskLevel,
        dominant: list[tuple[str, int]],
        testing: TestingAnalysis,
        risks: list[RiskFinding],
    ) -> str:
        area_bits = [
            _AREA_LABELS.get(a, a) for a, _ in dominant[:2] if a != FileArea.TEST.value
        ]
        area_phrase = " and ".join(area_bits) if area_bits else "mixed"
        missing_tests = any(f.id.startswith("test-no-corresponding") for f in testing.findings)
        level = {
            RiskLevel.LOW: "Low-risk",
            RiskLevel.MODERATE: "Moderate-risk",
            RiskLevel.HIGH: "High-risk",
        }[risk_level]
        if missing_tests:
            return f"{level} {area_phrase} change; tests not updated."
        if risks:
            top = _CATEGORY_LABELS.get(risks[0].category, risks[0].category.value)
            return f"{level} {area_phrase} change with {top} attention needed."
        return f"{level} {area_phrase} change with no major risk indicators."

    def _overview(
        self,
        pr: PullRequest,
        stats: ChangeStatistics,
        risks: list[RiskFinding],
        testing: TestingAnalysis,
        dominant: list[tuple[str, int]],
        risk_level: RiskLevel,
        partial_message: str | None,
    ) -> str:
        area_desc = ", ".join(
            f"{_AREA_LABELS.get(a, a)} ({n})" for a, n in dominant[:3]
        ) or "various areas"
        sentences = [
            f"PR #{pr.number} “{pr.title}” by @{pr.author} touches "
            f"{stats.total_files} file(s) (+{stats.additions}/-{stats.deletions}), "
            f"mainly {area_desc}."
        ]

        if risks:
            top = risks[:3]
            labels = ", ".join(_CATEGORY_LABELS.get(r.category, r.category.value) for r in top)
            sentences.append(
                f"PRISM flagged {len(risks)} review focus area(s) — notably {labels} — "
                f"at an overall {risk_level.value} risk level."
            )
        else:
            sentences.append(
                f"No category-level risk indicators stood out; overall risk looks {risk_level.value}."
            )

        if any(f.id.startswith("test-no-corresponding") for f in testing.findings):
            sentences.append(
                f"{testing.production_files_changed} production file(s) changed without "
                "matching test-file updates — confirm existing coverage still applies."
            )
        elif testing.test_files_added or testing.test_files_modified:
            sentences.append(
                f"Test files were updated ({testing.test_files_added} added, "
                f"{testing.test_files_modified} modified)."
            )

        if partial_message:
            sentences.append(partial_message)

        return " ".join(sentences)

    def _highlights(
        self,
        pr: PullRequest,
        stats: ChangeStatistics,
        risks: list[RiskFinding],
        testing: TestingAnalysis,
        dependencies: list[DependencyChange],
    ) -> list[str]:
        _ = testing
        highlights: list[str] = []
        if stats.area_distribution:
            top_area, count = max(stats.area_distribution.items(), key=lambda x: x[1])
            label = _AREA_LABELS.get(top_area, top_area)
            highlights.append(f"Mostly {label} work ({count} of {stats.total_files} files)")

        for f in pr.changed_files:
            if f.area == FileArea.API and f.status.value == "added":
                highlights.append(f"New API route: {f.filename.split('/')[-2] if '/' in f.filename else f.filename}")
                break

        for r in risks[:3]:
            highlights.append(
                f"{r.title} ({len(r.files) or 1} file{'s' if (len(r.files) or 1) != 1 else ''})"
            )

        if dependencies:
            highlights.append(f"{len(dependencies)} dependency change(s)")

        return highlights[:6]

    def _action_items(
        self,
        risks: list[RiskFinding],
        testing: TestingAnalysis,
        dependencies: list[DependencyChange],
        stats: ChangeStatistics,
    ) -> list[ActionItem]:
        items: list[ActionItem] = []
        priority = 1
        for r in risks:
            if not r.recommendation:
                continue
            items.append(
                ActionItem(
                    priority=priority,
                    title=r.title,
                    detail=r.recommendation,
                    files=list(r.files) if r.files else ([r.file] if r.file else []),
                )
            )
            priority += 1
            if priority > 6:
                break

        for f in testing.findings:
            items.append(
                ActionItem(
                    priority=priority,
                    title=f.title,
                    detail=f.recommendation
                    or "Confirm existing tests cover the changed production paths.",
                    files=list(f.files) if f.files else [],
                )
            )
            priority += 1

        if dependencies and not any(i.title.startswith("Dependency") for i in items):
            names = ", ".join(d.name for d in dependencies[:4])
            items.append(
                ActionItem(
                    priority=priority,
                    title="Review dependency updates",
                    detail=f"Check changelogs and run tests for: {names}.",
                    files=list({d.file for d in dependencies}),
                )
            )
            priority += 1

        if stats.total_files >= 30 and not any("Large pull" in i.title for i in items):
            items.append(
                ActionItem(
                    priority=priority,
                    title="Large pull request",
                    detail="Split by area or call out the highest-risk files for focused review.",
                    files=[],
                )
            )

        # Deduplicate by title
        seen: set[str] = set()
        unique: list[ActionItem] = []
        for item in items:
            if item.title in seen:
                continue
            seen.add(item.title)
            unique.append(item)
        return unique[:8]

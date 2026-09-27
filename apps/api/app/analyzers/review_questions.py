from app.models.domain import (
    DependencyChange,
    RiskFinding,
    TestingAnalysis,
)
from app.models.enums import FileArea, RiskCategory


class ReviewQuestionGenerator:
    """Deterministic review questions derived from findings and file areas."""

    def generate(
        self,
        *,
        risks: list[RiskFinding],
        testing: TestingAnalysis,
        dependencies: list[DependencyChange],
        complexity_findings: list[RiskFinding],
        areas: set[FileArea] | None = None,
    ) -> list[str]:
        questions: list[str] = []
        categories = {r.category for r in risks}
        areas = areas or set()

        if RiskCategory.AUTHENTICATION in categories or RiskCategory.AUTHORIZATION in categories:
            questions.append("Are authentication/authorization changes covered by integration tests?")
        if RiskCategory.DATABASE in categories:
            questions.append("Is the migration backwards compatible with the previous schema?")
        if RiskCategory.API in categories or FileArea.API in areas:
            questions.append("Are existing API consumers compatible with this change?")
        if dependencies or RiskCategory.DEPENDENCIES in categories:
            questions.append(
                "Are there compatibility or breaking-change considerations for the updated dependency?"
            )
        if RiskCategory.PAYMENTS in categories:
            questions.append("Have payment flows been verified in a non-production environment?")
        if RiskCategory.SECURITY in categories or RiskCategory.ENVIRONMENT in categories:
            questions.append("Have secrets and environment values been reviewed for accidental exposure?")
        if RiskCategory.CI_CD in categories:
            questions.append("Do CI/CD changes affect required checks or deployment safety?")
        if RiskCategory.INFRASTRUCTURE in categories:
            questions.append("Have infrastructure changes been validated against staging?")
        if FileArea.UI in areas and RiskCategory.API not in categories:
            questions.append("Do the UI changes handle empty, loading, and error states?")

        if any(f.id.startswith("test-no-corresponding") for f in testing.findings):
            questions.append("Are the affected scenarios covered by existing tests?")
        if any(f.id.startswith("test-files-deleted") for f in testing.findings):
            questions.append("Is removing these tests intentional, and is coverage retained elsewhere?")

        if any(f.category == RiskCategory.COMPLEXITY for f in complexity_findings):
            questions.append("Can complex or large functions be simplified or split for maintainability?")

        if RiskCategory.CHANGE in categories:
            questions.append("Should this large change be split into smaller, reviewable pull requests?")

        seen: set[str] = set()
        unique: list[str] = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        return unique

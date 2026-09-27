import os
from collections import Counter, defaultdict

from app.models.domain import ChangeStatistics, PullRequest, RiskFinding
from app.models.enums import FileStatus, FindingSource, RiskCategory, Severity


class ChangeAnalyzer:
    def analyze(self, pr: PullRequest) -> tuple[ChangeStatistics, list[RiskFinding]]:
        files = pr.changed_files
        area_churn: dict[str, dict[str, int]] = defaultdict(lambda: {"additions": 0, "deletions": 0})
        for f in files:
            key = f.area.value
            area_churn[key]["additions"] += f.additions
            area_churn[key]["deletions"] += f.deletions

        stats = ChangeStatistics(
            total_files=len(files),
            additions=sum(f.additions for f in files),
            deletions=sum(f.deletions for f in files),
            net_change=sum(f.additions - f.deletions for f in files),
            files_added=sum(1 for f in files if f.status == FileStatus.ADDED),
            files_modified=sum(1 for f in files if f.status == FileStatus.MODIFIED),
            files_deleted=sum(1 for f in files if f.status == FileStatus.REMOVED),
            files_renamed=sum(1 for f in files if f.status == FileStatus.RENAMED),
            binary_files=sum(1 for f in files if f.is_binary),
            file_type_distribution=dict(Counter(self._ext(f.filename) for f in files)),
            language_distribution=dict(
                Counter(f.language or "Unknown" for f in files if not f.is_binary)
            ),
            role_distribution=dict(Counter(f.role.value for f in files)),
            area_distribution=dict(Counter(f.area.value for f in files)),
            area_churn=dict(area_churn),
        )

        findings: list[RiskFinding] = []
        if stats.total_files >= 30:
            findings.append(
                RiskFinding(
                    id="change-large-pr",
                    severity=Severity.MEDIUM,
                    category=RiskCategory.CHANGE,
                    title="Large pull request",
                    description=(
                        "This PR changes many files, which makes thorough review harder and "
                        "raises the chance of missing a regression."
                    ),
                    evidence=f"{stats.total_files} files changed",
                    confidence=0.9,
                    source=FindingSource.DETERMINISTIC,
                    recommendation=(
                        "Consider splitting into smaller PRs by area (UI, API, data), or call out "
                        "the highest-risk files for focused review."
                    ),
                    files=[f.filename for f in files[:8]],
                )
            )
        if stats.additions + stats.deletions >= 1000:
            findings.append(
                RiskFinding(
                    id="change-large-diff",
                    severity=Severity.MEDIUM,
                    category=RiskCategory.CHANGE,
                    title="Large diff size",
                    description="High line churn may warrant splitting or focused review.",
                    evidence=f"+{stats.additions} / -{stats.deletions} lines",
                    confidence=0.85,
                    source=FindingSource.DETERMINISTIC,
                    recommendation=(
                        "Prioritize reviewing new public APIs, auth paths, and data migrations first."
                    ),
                )
            )
        return stats, findings

    @staticmethod
    def _ext(filename: str) -> str:
        _, ext = os.path.splitext(filename)
        return ext.lower() or "(none)"

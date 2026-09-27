import re

from app.models.domain import PullRequest, RiskFinding, TestingAnalysis
from app.models.enums import FileRole, FileStatus, FindingSource, RiskCategory, Severity

FRAMEWORK_HINTS = [
    (re.compile(r"pytest", re.I), "pytest"),
    (re.compile(r"unittest", re.I), "unittest"),
    (re.compile(r"jest", re.I), "jest"),
    (re.compile(r"vitest", re.I), "vitest"),
    (re.compile(r"mocha", re.I), "mocha"),
    (re.compile(r"@testing-library", re.I), "testing-library"),
    (re.compile(r"playwright", re.I), "playwright"),
    (re.compile(r"cypress", re.I), "cypress"),
]


class TestAnalyzer:
    def analyze(self, pr: PullRequest) -> TestingAnalysis:
        files = pr.changed_files
        test_files = [f for f in files if f.is_test_file or f.role == FileRole.TEST]
        prod_files = [
            f
            for f in files
            if f.role == FileRole.SOURCE and not f.is_test_file and not f.is_generated_file
        ]

        test_added = sum(1 for f in test_files if f.status == FileStatus.ADDED)
        test_modified = sum(1 for f in test_files if f.status == FileStatus.MODIFIED)
        test_deleted = sum(1 for f in test_files if f.status == FileStatus.REMOVED)

        ratio = None
        if prod_files:
            ratio = len(test_files) / len(prod_files)

        frameworks: list[str] = []
        for f in files:
            blob = f"{f.filename}\n{f.patch or ''}"
            for pattern, name in FRAMEWORK_HINTS:
                if pattern.search(blob) and name not in frameworks:
                    frameworks.append(name)

        test_dir = any(
            "/test" in f.filename.replace("\\", "/").lower()
            or f.filename.replace("\\", "/").lower().startswith("tests/")
            or "/__tests__/" in f.filename.replace("\\", "/")
            for f in files
        )

        findings: list[RiskFinding] = []
        if prod_files and not test_files:
            findings.append(
                RiskFinding(
                    id="test-no-corresponding-changes",
                    severity=Severity.MEDIUM,
                    category=RiskCategory.TESTING,
                    title="No corresponding test-file changes detected",
                    description=(
                        "Production code changed, but PRISM did not detect corresponding "
                        "test-file changes. Existing tests may still cover these scenarios."
                    ),
                    evidence=(
                        f"{len(prod_files)} production file(s) changed without detected "
                        "test-file changes"
                    ),
                    confidence=0.75,
                    source=FindingSource.DETERMINISTIC,
                    recommendation=(
                        "Add or update tests for the changed production paths, or document why "
                        "existing coverage is enough."
                    ),
                    files=[f.filename for f in prod_files[:8]],
                )
            )
        elif prod_files and ratio is not None and ratio < 0.25:
            findings.append(
                RiskFinding(
                    id="test-low-ratio",
                    severity=Severity.LOW,
                    category=RiskCategory.TESTING,
                    title="Low test-to-source change ratio",
                    description=(
                        "Relatively few test files changed compared to production files. "
                        "PRISM did not detect broad corresponding test-file coverage for this PR."
                    ),
                    evidence=f"test/source file change ratio ≈ {ratio:.2f}",
                    confidence=0.65,
                    source=FindingSource.DETERMINISTIC,
                    recommendation=(
                        "Consider expanding tests for the highest-risk production files in this PR."
                    ),
                    files=[f.filename for f in prod_files[:5]],
                )
            )

        if test_deleted and not test_added:
            findings.append(
                RiskFinding(
                    id="test-files-deleted",
                    severity=Severity.MEDIUM,
                    category=RiskCategory.TESTING,
                    title="Test files deleted",
                    description="Test files were removed in this PR.",
                    evidence=f"{test_deleted} test file(s) deleted",
                    confidence=0.9,
                    source=FindingSource.DETERMINISTIC,
                    recommendation=(
                        "Confirm deletions are intentional and that equivalent coverage remains elsewhere."
                    ),
                    files=[f.filename for f in test_files if f.status == FileStatus.REMOVED][:8],
                )
            )

        return TestingAnalysis(
            test_files_added=test_added,
            test_files_modified=test_modified,
            test_files_deleted=test_deleted,
            production_files_changed=len(prod_files),
            test_to_source_ratio=ratio,
            test_directory_present=test_dir,
            frameworks_detected=frameworks,
            findings=findings,
        )

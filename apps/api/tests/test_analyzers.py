from collections import Counter

from app.analyzers.change import ChangeAnalyzer
from app.analyzers.complexity import ComplexityAnalyzer
from app.analyzers.dependency import DependencyAnalyzer
from app.analyzers.review_questions import ReviewQuestionGenerator
from app.analyzers.risk import RiskAnalyzer, tokenize_path
from app.analyzers.summary import SummaryGenerator
from app.analyzers.test_analyzer import TestAnalyzer
from app.core.config import Settings
from app.github.normalizer import normalize_pull_request
from app.models.enums import FileArea, RiskCategory
from app.services.demo import load_fixture


def _pr(name: str):
    data = load_fixture(name)
    settings = Settings()
    pr, _, _ = normalize_pull_request(
        data["pull_request"], data["files"], data.get("commits", []), settings
    )
    return pr


def test_change_analyzer_stats():
    pr = _pr("small_python_pr")
    stats, _ = ChangeAnalyzer().analyze(pr)
    assert stats.total_files == 2
    assert stats.files_added == 1
    assert stats.additions >= 1
    assert stats.area_distribution
    assert stats.area_churn


def test_risk_analyzer_auth():
    pr = _pr("auth_change_pr")
    findings = RiskAnalyzer().analyze(pr)
    assert any(f.category == RiskCategory.AUTHENTICATION for f in findings)


def test_risk_analyzer_database():
    pr = _pr("database_change_pr")
    findings = RiskAnalyzer().analyze(pr)
    assert any(f.category == RiskCategory.DATABASE for f in findings)


def test_dependency_analyzer():
    pr = _pr("dependency_change_pr")
    deps = DependencyAnalyzer().analyze(pr)
    assert len(deps) >= 1
    assert any(d.name == "axios" and d.change_type == "updated" for d in deps)


def test_test_analyzer_no_tests_wording():
    pr = _pr("no_tests_pr")
    testing = TestAnalyzer().analyze(pr)
    assert testing.production_files_changed >= 1
    assert testing.test_files_added == 0
    assert any("did not detect corresponding test-file changes" in f.description for f in testing.findings)


def test_complexity_analyzer_python():
    pr = _pr("complexity_pr")
    obs, findings = ComplexityAnalyzer().analyze(pr)
    assert obs
    assert obs[0].language == "Python"
    assert obs[0].function_count >= 1
    assert isinstance(findings, list)


def test_review_questions_contextual():
    pr = _pr("auth_change_pr")
    risks = RiskAnalyzer().analyze(pr)
    testing = TestAnalyzer().analyze(pr)
    deps = DependencyAnalyzer().analyze(pr)
    questions = ReviewQuestionGenerator().generate(
        risks=risks,
        testing=testing,
        dependencies=deps,
        complexity_findings=[],
        areas={f.area for f in pr.changed_files},
    )
    assert questions
    assert any("authentication" in q.lower() or "authorization" in q.lower() for q in questions)


def test_tokenize_path_no_auth_false_positive():
    tokens = tokenize_path("src/components/ui/serviceArea/UnsupportedAreaNotice.tsx")
    assert "auth" not in tokens
    assert "area" in tokens
    assert "notice" in tokens


def test_ui_component_pr_areas_and_risks():
    pr = _pr("ui_component_pr")
    areas = {f.filename: f.area for f in pr.changed_files}
    assert areas["src/components/ui/serviceArea/UnsupportedAreaNotice.tsx"] == FileArea.UI
    assert areas["src/constants/appConstants/launchAreaConstants.ts"] == FileArea.CONSTANTS
    assert areas["src/app/api/launch-waitlist/route.ts"] == FileArea.API

    findings = RiskAnalyzer().analyze(pr)
    categories = [f.category for f in findings]
    assert RiskCategory.API in categories
    assert RiskCategory.AUTHENTICATION not in categories
    assert RiskCategory.AUTHORIZATION not in categories
    assert RiskCategory.DATA_HANDLING not in categories

    api_findings = [f for f in findings if f.category == RiskCategory.API]
    assert len(api_findings) == 1
    assert "src/app/api/launch-waitlist/route.ts" in api_findings[0].files
    assert api_findings[0].recommendation

    # Grouping: one finding per category
    counts = Counter(f.category for f in findings)
    assert all(n == 1 for n in counts.values())


def test_import_export_do_not_trigger_data_handling():
    pr = _pr("ui_component_pr")
    findings = RiskAnalyzer().analyze(pr)
    assert not any(f.category == RiskCategory.DATA_HANDLING for f in findings)


def test_summary_generator_review():
    pr = _pr("ui_component_pr")
    stats, change_findings = ChangeAnalyzer().analyze(pr)
    risks = RiskAnalyzer().analyze(pr) + change_findings
    testing = TestAnalyzer().analyze(pr)
    deps = DependencyAnalyzer().analyze(pr)
    review = SummaryGenerator().generate(
        pr=pr,
        stats=stats,
        risks=risks + testing.findings,
        testing=testing,
        dependencies=deps,
    )
    assert review.risk_level
    assert review.overview
    assert review.headline
    assert isinstance(review.highlights, list)
    assert any(item.detail for item in review.action_items) or review.action_items == []
    if review.action_items:
        assert review.action_items[0].title

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app
from app.services.cache import InMemoryCache
from app.services.demo import fixture_github_client
from app.services.orchestrator import AnalysisOrchestrator


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return Settings(cache_enabled=False, ai_enabled=False, max_files=100)


@pytest.mark.asyncio
async def test_orchestrator_full_report(settings: Settings):
    github = fixture_github_client("demo_pr")
    orch = AnalysisOrchestrator(github=github, settings=settings, cache=InMemoryCache())
    report = await orch.analyze("prism-demo", "sample-repo", 1)
    assert report.pr.number == 1
    assert report.statistics.total_files >= 1
    assert report.ai_analysis is None
    assert report.summary
    assert report.review is not None
    assert report.summary == report.review.overview
    assert report.review.risk_level
    assert isinstance(report.review_questions, list)
    await github.aclose()


@pytest.mark.asyncio
async def test_orchestrator_ui_component_fixture(settings: Settings):
    github = fixture_github_client("ui_component_pr")
    orch = AnalysisOrchestrator(github=github, settings=settings, cache=InMemoryCache())
    report = await orch.analyze("frankalvinz", "nearvo", 4)
    assert report.review is not None
    assert report.summary == report.review.overview
    assert report.statistics.area_distribution.get("ui") == 1
    assert report.statistics.area_distribution.get("api") == 1
    categories = {f.category for f in report.risks}
    assert "authentication" not in categories
    assert "api" in categories or any(f.area.value == "api" for f in report.pr.changed_files)
    await github.aclose()


@pytest.mark.asyncio
async def test_orchestrator_large_pr_partial(settings: Settings):
    settings = Settings(cache_enabled=False, ai_enabled=False, max_files=40)
    github = fixture_github_client("large_pr")
    orch = AnalysisOrchestrator(github=github, settings=settings, cache=InMemoryCache())
    report = await orch.analyze("acme", "widgets", 99)
    assert report.partial is True
    assert report.files_analyzed == 40
    await github.aclose()


@pytest.mark.asyncio
async def test_analyze_demo_endpoint():
    get_settings.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/analyze", json={"demo": True})
    assert response.status_code == 200
    data = response.json()
    assert data["pr"]["number"] == 1
    assert data["ai_analysis"] is None


@pytest.mark.asyncio
async def test_health_and_version():
    get_settings.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/api/v1/health")
        version = await client.get("/api/v1/version")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert version.status_code == 200
    assert "version" in version.json()


@pytest.mark.asyncio
async def test_invalid_url_error_shape():
    get_settings.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyze", json={"url": "https://example.com/not-a-pr"}
        )
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "INVALID_URL"

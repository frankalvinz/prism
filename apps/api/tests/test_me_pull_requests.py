import json
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.me_routes import FILTER_QUERIES, open_prs_cache_key
from app.core.config import Settings, get_settings
from app.core.session import SESSION_COOKIE, encrypt_session
from app.github.rest_client import GitHubRestClient
from app.github.search_normalizer import normalize_search_results
from app.main import create_app
from app.services.cache import InMemoryCache

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "fixtures" / "github" / "search_open_prs.json"


@pytest.fixture
def oauth_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    get_settings.cache_clear()
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret-32chars!!")
    monkeypatch.setenv("PUBLIC_WEB_URL", "http://localhost:3000")
    get_settings.cache_clear()
    return get_settings()


def test_filter_queries():
    assert "author:@me" in FILTER_QUERIES["authored"]
    assert "review-requested:@me" in FILTER_QUERIES["review_requested"]
    assert "assignee:@me" in FILTER_QUERIES["assigned"]


def test_normalize_search_results():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    items = normalize_search_results(payload)
    assert len(items) == 2
    assert items[0].owner == "acme"
    assert items[0].repo == "widgets"
    assert items[0].number == 42
    assert items[0].title.startswith("Harden")
    assert items[0].labels == ["security", "backend"]
    assert items[1].draft is True
    assert items[1].repo == "maps"


@pytest.mark.asyncio
async def test_list_prs_requires_auth(oauth_settings: Settings):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/me/pull-requests")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_list_prs_invalid_filter(oauth_settings: Settings):
    cookie = encrypt_session(oauth_settings, token="tok", login="frank", avatar_url=None)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/me/pull-requests",
            params={"filter": "bogus"},
            cookies={SESSION_COOKIE: cookie or ""},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_prs_success_and_cache(oauth_settings: Settings):
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    calls = {"n": 0}

    def factory(settings: Settings) -> GitHubRestClient:
        def handler(request: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            assert request.url.path == "/search/issues"
            assert "author:@me" in str(request.url.params.get("q"))
            return httpx.Response(200, json=payload)

        return GitHubRestClient(
            settings,
            client=httpx.AsyncClient(
                base_url="https://api.github.com",
                transport=httpx.MockTransport(handler),
            ),
            token="viewer-token",
        )

    cookie = encrypt_session(oauth_settings, token="viewer-token", login="frank", avatar_url=None)
    app = create_app()
    app.state.github_client_factory = factory
    app.state.cache = InMemoryCache()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get(
            "/api/v1/me/pull-requests",
            params={"filter": "authored"},
            cookies={SESSION_COOKIE: cookie or ""},
        )
        second = await client.get(
            "/api/v1/me/pull-requests",
            params={"filter": "authored"},
            cookies={SESSION_COOKIE: cookie or ""},
        )
    assert first.status_code == 200
    body = first.json()
    assert body["total_count"] == 2
    assert body["items"][0]["owner"] == "acme"
    assert body["items"][0]["number"] == 42
    assert second.status_code == 200
    assert calls["n"] == 1
    assert app.state.cache.get(open_prs_cache_key("frank", "authored")) is not None


@pytest.mark.asyncio
async def test_list_prs_401_clears_session(oauth_settings: Settings):
    def factory(settings: Settings) -> GitHubRestClient:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"message": "Bad credentials"})

        return GitHubRestClient(
            settings,
            client=httpx.AsyncClient(
                base_url="https://api.github.com",
                transport=httpx.MockTransport(handler),
            ),
            token="expired",
        )

    cookie = encrypt_session(oauth_settings, token="expired", login="frank", avatar_url=None)
    app = create_app()
    app.state.github_client_factory = factory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/me/pull-requests",
            cookies={SESSION_COOKIE: cookie or ""},
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "GITHUB_AUTH_EXPIRED"
    assert SESSION_COOKIE in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_rest_client_search_pull_requests(oauth_settings: Settings):
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search/issues"
        assert request.url.params.get("sort") == "updated"
        assert request.url.params.get("order") == "desc"
        return httpx.Response(200, json=payload)

    client = GitHubRestClient(
        oauth_settings,
        client=httpx.AsyncClient(
            base_url="https://api.github.com",
            transport=httpx.MockTransport(handler),
        ),
        token="tok",
    )
    result = await client.search_pull_requests("is:pr is:open author:@me", per_page=30)
    assert result["total_count"] == 2
    await client.aclose()

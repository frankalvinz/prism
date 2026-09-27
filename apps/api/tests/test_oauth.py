import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.core.session import SESSION_COOKIE, encrypt_session
from app.github.rest_client import GitHubRestClient
from app.main import create_app
from app.services.cache import InMemoryCache, cache_key
from app.services.demo import load_fixture
from app.services.orchestrator import AnalysisOrchestrator


@pytest.fixture
def oauth_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    get_settings.cache_clear()
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret-32chars!!")
    monkeypatch.setenv("PUBLIC_WEB_URL", "http://localhost:3000")
    get_settings.cache_clear()
    return get_settings()


@pytest.mark.asyncio
async def test_auth_me_anonymous(oauth_settings: Settings):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["oauth_enabled"] is True
    assert body["authenticated"] is False
    assert "token" not in body


@pytest.mark.asyncio
async def test_callback_state_mismatch(oauth_settings: Settings):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as client:
        response = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "abc", "state": "wrong"},
            cookies={"prism_oauth_state": "other.1.deadbeef"},
        )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "/welcome" in location
    assert "auth_error=state_mismatch" in location


@pytest.mark.asyncio
async def test_callback_success_sets_session(
    oauth_settings: Settings, monkeypatch: pytest.MonkeyPatch
):
    async def fake_exchange(settings, code: str) -> str:
        assert code == "good-code"
        return "gho_user_token"

    async def fake_user(settings, token: str) -> dict:
        assert token == "gho_user_token"
        return {"login": "frank", "avatar_url": "https://example.com/a.png"}

    monkeypatch.setattr("app.github.oauth.exchange_code", fake_exchange)
    monkeypatch.setattr("app.github.oauth.fetch_user", fake_user)

    from app.core.session import create_oauth_state

    raw, signed = create_oauth_state(oauth_settings)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as client:
        response = await client.get(
            "/api/v1/auth/github/callback",
            params={"code": "good-code", "state": raw},
            cookies={"prism_oauth_state": signed},
        )
        assert response.status_code == 302
        assert response.headers["location"].endswith("/")
        assert SESSION_COOKIE in response.cookies

        me = await client.get(
            "/api/v1/auth/me",
            cookies={SESSION_COOKIE: response.cookies[SESSION_COOKIE]},
        )
    assert me.status_code == 200
    body = me.json()
    assert body["authenticated"] is True
    assert body["login"] == "frank"
    assert "token" not in body
    assert "gho_" not in str(body)


@pytest.mark.asyncio
async def test_analyze_uses_viewer_token(oauth_settings: Settings):
    captured: dict[str, str | None] = {"token": None}

    def factory(settings: Settings) -> GitHubRestClient:
        # Capture by inspecting Authorization via a mock transport.
        def handler(request: httpx.Request) -> httpx.Response:
            auth = request.headers.get("authorization")
            captured["token"] = auth
            data = load_fixture("small_python_pr")
            if request.url.path.endswith("/pulls/12"):
                return httpx.Response(200, json=data["pull_request"])
            if "/files" in request.url.path:
                return httpx.Response(200, json=data["files"])
            if "/commits" in request.url.path:
                return httpx.Response(200, json=data.get("commits", []))
            return httpx.Response(404, json={"message": "Not Found"})

        return GitHubRestClient(
            settings,
            client=httpx.AsyncClient(
                base_url="https://api.github.com",
                transport=httpx.MockTransport(handler),
                headers={"Authorization": "Bearer viewer-token"},
            ),
            token="viewer-token",
        )

    cookie = encrypt_session(
        oauth_settings, token="viewer-token", login="frank", avatar_url=None
    )
    app = create_app()
    app.state.github_client_factory = factory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://github.com/acme/widgets/pull/12"},
            cookies={SESSION_COOKIE: cookie or ""},
        )
    assert response.status_code == 200
    assert captured["token"] == "Bearer viewer-token"


@pytest.mark.asyncio
async def test_analyze_401_clears_session(oauth_settings: Settings):
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
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://github.com/acme/widgets/pull/12"},
            cookies={SESSION_COOKIE: cookie or ""},
        )
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "GITHUB_AUTH_EXPIRED"
    # Set-Cookie clearing the session
    set_cookie = response.headers.get("set-cookie", "")
    assert SESSION_COOKIE in set_cookie


@pytest.mark.asyncio
async def test_cache_isolation_viewer_vs_anonymous(oauth_settings: Settings):
    settings = Settings(cache_enabled=True, ai_enabled=False)
    cache = InMemoryCache()
    data = load_fixture("small_python_pr")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/pulls/12"):
            return httpx.Response(200, json=data["pull_request"])
        if "/files" in request.url.path:
            return httpx.Response(200, json=data["files"])
        if "/commits" in request.url.path:
            return httpx.Response(200, json=data.get("commits", []))
        return httpx.Response(404, json={"message": "Not Found"})

    github = GitHubRestClient(
        settings,
        client=httpx.AsyncClient(
            base_url="https://api.github.com",
            transport=httpx.MockTransport(handler),
        ),
    )
    viewer_orch = AnalysisOrchestrator(
        github=github, settings=settings, cache=cache, viewer_login="frank"
    )
    report = await viewer_orch.analyze("acme", "widgets", 12)
    sha = report.pr.head_sha
    viewer_key = cache_key("acme", "widgets", 12, sha, viewer_login="frank")
    anon_key = cache_key("acme", "widgets", 12, sha)
    assert cache.get(viewer_key) is not None
    assert cache.get(anon_key) is None
    await github.aclose()


@pytest.mark.asyncio
async def test_not_found_private_anonymous(oauth_settings: Settings):
    settings = Settings(cache_enabled=False, ai_enabled=False)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    github = GitHubRestClient(
        settings,
        client=httpx.AsyncClient(
            base_url="https://api.github.com",
            transport=httpx.MockTransport(handler),
        ),
    )
    orch = AnalysisOrchestrator(github=github, settings=settings, cache=InMemoryCache())
    from app.core.exceptions import GitHubNotFoundError

    with pytest.raises(GitHubNotFoundError) as exc:
        await orch.analyze("frankalvinz", "nearvo", 4)
    assert exc.value.details.get("hint") == "connect_github"
    assert "Connect GitHub" in exc.value.message
    await github.aclose()


@pytest.mark.asyncio
async def test_not_found_signed_in_no_access(oauth_settings: Settings):
    settings = Settings(cache_enabled=False, ai_enabled=False)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    github = GitHubRestClient(
        settings,
        client=httpx.AsyncClient(
            base_url="https://api.github.com",
            transport=httpx.MockTransport(handler),
        ),
    )
    orch = AnalysisOrchestrator(
        github=github, settings=settings, cache=InMemoryCache(), viewer_login="frank"
    )
    from app.core.exceptions import GitHubNotFoundError

    with pytest.raises(GitHubNotFoundError) as exc:
        await orch.analyze("frankalvinz", "nearvo", 4)
    assert exc.value.details.get("hint") == "no_access"
    await github.aclose()


@pytest.mark.asyncio
async def test_not_found_missing_pr(oauth_settings: Settings):
    settings = Settings(cache_enabled=False, ai_enabled=False)

    def handler(request: httpx.Request) -> httpx.Response:
        if "/pulls/" in request.url.path:
            return httpx.Response(404, json={"message": "Not Found"})
        if request.url.path.endswith("/nearvo"):
            return httpx.Response(200, json={"full_name": "frankalvinz/nearvo", "private": False})
        return httpx.Response(404, json={"message": "Not Found"})

    github = GitHubRestClient(
        settings,
        client=httpx.AsyncClient(
            base_url="https://api.github.com",
            transport=httpx.MockTransport(handler),
        ),
    )
    orch = AnalysisOrchestrator(github=github, settings=settings, cache=InMemoryCache())
    from app.core.exceptions import GitHubNotFoundError

    with pytest.raises(GitHubNotFoundError) as exc:
        await orch.analyze("frankalvinz", "nearvo", 4)
    assert exc.value.details.get("hint") == "missing_pr"
    assert "#4" in exc.value.message
    await github.aclose()

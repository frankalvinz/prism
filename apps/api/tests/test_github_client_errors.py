import json

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import (
    GitHubApiError,
    GitHubAuthError,
    GitHubNotFoundError,
    GitHubRateLimitedError,
)
from app.github.rest_client import GitHubRestClient


def _settings() -> Settings:
    return Settings(github_token=None, github_api_base="https://api.github.com")


def _mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url="https://api.github.com",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_404_maps_to_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    gh = GitHubRestClient(_settings(), client=_mock_client(handler))
    with pytest.raises(GitHubNotFoundError) as exc:
        await gh.get_pull_request("acme", "widgets", 1)
    assert exc.value.code == "GITHUB_NOT_FOUND"
    assert exc.value.details.get("github_message") == "Not Found"
    await gh.aclose()


@pytest.mark.asyncio
async def test_403_remaining_zero_maps_to_rate_limited():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1710000000"},
        )

    gh = GitHubRestClient(_settings(), client=_mock_client(handler))
    with pytest.raises(GitHubRateLimitedError) as exc:
        await gh.get_pull_request("acme", "widgets", 1)
    assert exc.value.code == "GITHUB_RATE_LIMITED"
    await gh.aclose()


@pytest.mark.asyncio
async def test_403_without_rate_limit_is_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"message": "Repository access blocked"},
            headers={"x-ratelimit-remaining": "60"},
        )

    gh = GitHubRestClient(_settings(), client=_mock_client(handler))
    with pytest.raises(GitHubApiError) as exc:
        await gh.get_pull_request("acme", "widgets", 1)
    assert exc.value.code == "GITHUB_API_ERROR"
    assert exc.value.details.get("status") == 403
    assert exc.value.details.get("github_message") == "Repository access blocked"
    assert "403" in exc.value.message
    assert "Repository access blocked" in exc.value.message
    await gh.aclose()


@pytest.mark.asyncio
async def test_401_maps_to_auth_expired():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/pulls/1")
        body = json.dumps({"message": "Bad credentials"})
        return httpx.Response(401, content=body, headers={"content-type": "application/json"})

    gh = GitHubRestClient(_settings(), client=_mock_client(handler))
    with pytest.raises(GitHubAuthError) as exc:
        await gh.get_pull_request("acme", "widgets", 1)
    assert exc.value.code == "GITHUB_AUTH_EXPIRED"
    assert exc.value.details.get("github_message") == "Bad credentials"
    await gh.aclose()


@pytest.mark.asyncio
async def test_429_maps_to_rate_limited():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"message": "You have exceeded a secondary rate limit"},
            headers={"retry-after": "30"},
        )

    gh = GitHubRestClient(_settings(), client=_mock_client(handler))
    with pytest.raises(GitHubRateLimitedError) as exc:
        await gh.get_pull_request("acme", "widgets", 1)
    assert exc.value.details.get("retry_after") == "30"
    await gh.aclose()

from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import (
    GitHubApiError,
    GitHubAuthError,
    GitHubNotFoundError,
    GitHubRateLimitedError,
)
from app.core.http import system_ssl_context
from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_GITHUB_MESSAGE = 240
_MAX_ERROR_REASON = 200


def _extract_github_message(response: httpx.Response) -> str | None:
    """Best-effort parse of GitHub error message; never includes secrets."""
    try:
        payload = response.json()
    except Exception:
        text = (response.text or "").strip()
        return text[:_MAX_GITHUB_MESSAGE] if text else None

    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()[:_MAX_GITHUB_MESSAGE]
    return None


def _is_rate_limited(response: httpx.Response) -> bool:
    if response.status_code == 429:
        return True
    if response.status_code != 403:
        return False
    body = (response.text or "").lower()
    if "rate limit" in body:
        return True
    return response.headers.get("x-ratelimit-remaining") == "0"


class GitHubRestClient:
    """Async GitHub REST API client. Tokens are never logged."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        *,
        token: str | None = None,
    ) -> None:
        self._settings = settings
        self._owns_client = client is None
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": settings.github_user_agent,
        }
        auth_token = token if token is not None else settings.github_token
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        self._client = client or httpx.AsyncClient(
            base_url=settings.github_api_base.rstrip("/"),
            headers=headers,
            timeout=30.0,
            verify=system_ssl_context(),
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            reason = str(exc)[:_MAX_ERROR_REASON]
            logger.warning(
                "github.request_failed path=%s type=%s reason=%s",
                path,
                type(exc).__name__,
                reason,
            )
            raise GitHubApiError(
                "Failed to reach GitHub API.",
                details={"reason": reason, "path": path},
            ) from exc

        github_message = _extract_github_message(response)

        if response.status_code == 401:
            logger.warning("github.auth_expired path=%s", path)
            raise GitHubAuthError(
                "GitHub session expired. Please reconnect GitHub.",
                details={"path": path, "github_message": github_message},
            )

        if response.status_code == 404:
            logger.info("github.not_found path=%s", path)
            raise GitHubNotFoundError(
                "Repository or pull request was not found.",
                details={"path": path, "github_message": github_message},
            )

        if _is_rate_limited(response):
            logger.warning(
                "github.rate_limited path=%s status=%s message=%s",
                path,
                response.status_code,
                github_message,
            )
            raise GitHubRateLimitedError(
                "GitHub API rate limit reached.",
                details={
                    "path": path,
                    "status": response.status_code,
                    "reset": response.headers.get("x-ratelimit-reset"),
                    "retry_after": response.headers.get("retry-after"),
                    "github_message": github_message,
                },
            )

        if response.status_code >= 400:
            detail = github_message or "No additional detail from GitHub."
            message = f"GitHub API returned {response.status_code}: {detail}"
            logger.warning(
                "github.api_error path=%s status=%s message=%s",
                path,
                response.status_code,
                github_message,
            )
            raise GitHubApiError(
                message,
                details={
                    "status": response.status_code,
                    "path": path,
                    "github_message": github_message,
                },
            )

        if response.status_code == 204:
            return None
        return response.json()

    async def get_pull_request(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        logger.info("github.fetch_pr owner=%s repo=%s number=%s", owner, repo, number)
        data = await self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}")
        return data  # type: ignore[no-any-return]

    async def get_pull_request_files(
        self, owner: str, repo: str, number: int
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/pulls/{number}/files",
                params={"per_page": 100, "page": page},
            )
            if not batch:
                break
            results.extend(batch)
            if len(batch) < 100:
                break
            page += 1
            if page > 20:
                break
        return results

    async def get_pull_request_commits(
        self, owner: str, repo: str, number: int
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/pulls/{number}/commits",
                params={"per_page": 100, "page": page},
            )
            if not batch:
                break
            results.extend(batch)
            if len(batch) < 100:
                break
            page += 1
            if page > 10:
                break
        return results

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        data = await self._request("GET", f"/repos/{owner}/{repo}")
        return data  # type: ignore[no-any-return]

    async def get_file_contents(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        try:
            data = await self._request(
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": ref},
            )
        except (GitHubNotFoundError, GitHubApiError, GitHubAuthError):
            return None
        if not isinstance(data, dict):
            return None
        if data.get("encoding") == "base64" and isinstance(data.get("content"), str):
            import base64

            try:
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            except Exception:
                return None
        return None

    async def search_pull_requests(self, query: str, per_page: int = 30) -> dict[str, Any]:
        logger.info("github.search_prs per_page=%s", per_page)
        data = await self._request(
            "GET",
            "/search/issues",
            params={
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": min(max(per_page, 1), 100),
            },
        )
        return data if isinstance(data, dict) else {"total_count": 0, "items": []}

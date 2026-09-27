"""GitHub OAuth App helpers. Tokens are never logged."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.core.exceptions import GitHubApiError
from app.core.http import system_ssl_context
from app.core.logging import get_logger

logger = get_logger(__name__)

# OAuth Apps have no read-only private-repo scope; `repo` is required.
OAUTH_SCOPES = "repo"


def authorize_url(settings: Settings, state: str) -> str:
    params = urlencode(
        {
            "client_id": settings.github_oauth_client_id or "",
            "redirect_uri": settings.oauth_callback_url,
            "scope": OAUTH_SCOPES,
            "state": state,
            "allow_signup": "false",
        }
    )
    return f"https://github.com/login/oauth/authorize?{params}"


async def exchange_code(settings: Settings, code: str) -> str:
    async with httpx.AsyncClient(timeout=30.0, verify=system_ssl_context()) as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json", "User-Agent": settings.github_user_agent},
            data={
                "client_id": settings.github_oauth_client_id,
                "client_secret": settings.github_oauth_client_secret,
                "code": code,
                "redirect_uri": settings.oauth_callback_url,
            },
        )
    if response.status_code >= 400:
        logger.warning("oauth.exchange_failed status=%s", response.status_code)
        raise GitHubApiError(
            "GitHub OAuth token exchange failed.",
            details={"status": response.status_code},
        )
    data = response.json()
    token = data.get("access_token")
    if not isinstance(token, str) or not token:
        logger.warning("oauth.exchange_missing_token error=%s", data.get("error"))
        raise GitHubApiError(
            "GitHub OAuth did not return an access token.",
            details={"error": data.get("error")},
        )
    return token


async def fetch_user(settings: Settings, token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0, verify=system_ssl_context()) as client:
        response = await client.get(
            f"{settings.github_api_base.rstrip('/')}/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": settings.github_user_agent,
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
    if response.status_code >= 400:
        logger.warning("oauth.fetch_user_failed status=%s", response.status_code)
        raise GitHubApiError(
            "Failed to fetch GitHub user profile.",
            details={"status": response.status_code},
        )
    data = response.json()
    if not isinstance(data, dict) or not data.get("login"):
        raise GitHubApiError("GitHub user profile was incomplete.")
    return data


async def revoke_grant(settings: Settings, token: str) -> None:
    """Best-effort revoke of the OAuth grant for this application."""
    if not settings.github_oauth_client_id or not settings.github_oauth_client_secret:
        return
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=system_ssl_context()) as client:
            await client.request(
                "DELETE",
                f"{settings.github_api_base.rstrip('/')}/applications/"
                f"{settings.github_oauth_client_id}/grant",
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": settings.github_user_agent,
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                auth=(settings.github_oauth_client_id, settings.github_oauth_client_secret),
                json={"access_token": token},
            )
    except Exception:
        logger.warning("oauth.revoke_failed")

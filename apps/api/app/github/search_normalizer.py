"""Normalize GitHub Search API PR items into OpenPullRequest models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from app.models.domain import OpenPullRequest


def _parse_owner_repo(item: dict[str, Any]) -> tuple[str, str]:
    repo_url = item.get("repository_url")
    if isinstance(repo_url, str) and repo_url:
        # https://api.github.com/repos/owner/repo
        path = urlparse(repo_url).path.strip("/")
        parts = path.split("/")
        if len(parts) >= 3 and parts[0] == "repos":
            return parts[1], parts[2]

    html_url = item.get("html_url")
    if isinstance(html_url, str) and html_url:
        # https://github.com/owner/repo/pull/N
        path = urlparse(html_url).path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]

    return "unknown", "unknown"


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_search_item(item: dict[str, Any]) -> OpenPullRequest:
    owner, repo = _parse_owner_repo(item)
    user = item.get("user") if isinstance(item.get("user"), dict) else {}
    labels_raw = item.get("labels") if isinstance(item.get("labels"), list) else []
    labels: list[str] = []
    for label in labels_raw:
        if isinstance(label, dict) and isinstance(label.get("name"), str):
            labels.append(label["name"])
        elif isinstance(label, str):
            labels.append(label)

    number = item.get("number")
    title = item.get("title")
    html_url = item.get("html_url")

    return OpenPullRequest(
        owner=owner,
        repo=repo,
        number=int(number) if isinstance(number, int) else 0,
        title=str(title) if title is not None else "",
        html_url=str(html_url) if html_url is not None else "",
        author_login=user.get("login") if isinstance(user.get("login"), str) else None,
        author_avatar_url=(
            user.get("avatar_url") if isinstance(user.get("avatar_url"), str) else None
        ),
        draft=bool(item.get("draft")),
        comments=int(item["comments"]) if isinstance(item.get("comments"), int) else 0,
        labels=labels,
        created_at=_parse_dt(item.get("created_at")),
        updated_at=_parse_dt(item.get("updated_at")),
    )


def normalize_search_results(payload: dict[str, Any]) -> list[OpenPullRequest]:
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    results: list[OpenPullRequest] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        # Search /issues can include issues; require pull_request key for PRs.
        if "pull_request" not in item and "/pull/" not in str(item.get("html_url") or ""):
            continue
        results.append(normalize_search_item(item))
    return results

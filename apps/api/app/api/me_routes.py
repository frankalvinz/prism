from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.api.deps import get_cache, get_github_client_factory, get_viewer
from app.api.errors import auth_expired_response
from app.core.config import get_settings
from app.core.constants import ME_PREFIX, OPEN_PRS_CACHE_TTL
from app.core.exceptions import AuthRequiredError, GitHubAuthError
from app.core.session import ViewerSession
from app.github.search_normalizer import normalize_search_results
from app.models.domain import OpenPullRequest

router = APIRouter(prefix=ME_PREFIX)

PullRequestFilter = Literal["authored", "review_requested", "assigned"]

FILTER_QUERIES: dict[str, str] = {
    "authored": "is:pr is:open archived:false author:@me",
    "review_requested": "is:pr is:open archived:false review-requested:@me",
    "assigned": "is:pr is:open archived:false assignee:@me",
}


class OpenPullRequestsResponse(BaseModel):
    filter: PullRequestFilter
    total_count: int
    items: list[OpenPullRequest]


def open_prs_cache_key(login: str, filter_name: str) -> str:
    return f"viewer:{login}:open_prs:{filter_name}"


@router.get("/pull-requests", response_model=OpenPullRequestsResponse)
async def list_my_pull_requests(
    request: Request,
    filter: PullRequestFilter = Query(default="authored"),  # noqa: B008, A002
    viewer: ViewerSession | None = Depends(get_viewer),  # noqa: B008
    client_factory=Depends(get_github_client_factory),  # noqa: B008
):
    if viewer is None:
        raise AuthRequiredError("Sign in with GitHub to list your open pull requests.")

    settings = get_settings()
    cache = get_cache(request)
    cache_key = open_prs_cache_key(viewer.login, filter)
    cached = cache.get(cache_key)
    if isinstance(cached, dict):
        return OpenPullRequestsResponse.model_validate(cached)

    query = FILTER_QUERIES[filter]
    github = client_factory(settings)
    try:
        payload = await github.search_pull_requests(query, per_page=30)
        items = normalize_search_results(payload if isinstance(payload, dict) else {})
        total = payload.get("total_count") if isinstance(payload, dict) else len(items)
        response = OpenPullRequestsResponse(
            filter=filter,
            total_count=int(total) if isinstance(total, int) else len(items),
            items=items,
        )
        cache.set(cache_key, response.model_dump(mode="json"), OPEN_PRS_CACHE_TTL)
        return response
    except GitHubAuthError as exc:
        return auth_expired_response(exc)
    finally:
        await github.aclose()

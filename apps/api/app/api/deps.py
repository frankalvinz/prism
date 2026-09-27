from collections.abc import Callable

from fastapi import Request

from app.core.config import Settings, get_settings
from app.core.session import SESSION_COOKIE, ViewerSession, decrypt_session
from app.github.rest_client import GitHubRestClient
from app.services.cache import InMemoryCache

_fallback_cache = InMemoryCache()


def get_viewer(request: Request) -> ViewerSession | None:
    settings = get_settings()
    return decrypt_session(settings, request.cookies.get(SESSION_COOKIE))


def get_cache(request: Request) -> InMemoryCache:
    return getattr(request.app.state, "cache", _fallback_cache)


def build_github_client(
    settings: Settings, *, token: str | None = None
) -> GitHubRestClient:
    return GitHubRestClient(settings, token=token)


GitHubClientFactory = Callable[[Settings], GitHubRestClient]


def get_github_client_factory(request: Request) -> GitHubClientFactory:
    override = getattr(request.app.state, "github_client_factory", None)
    if callable(override):
        return override  # type: ignore[no-any-return]

    viewer = get_viewer(request)

    def factory(settings: Settings) -> GitHubRestClient:
        return build_github_client(
            settings,
            token=viewer.token if viewer is not None else None,
        )

    return factory

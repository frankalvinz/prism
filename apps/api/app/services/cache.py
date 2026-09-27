import time
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AnalysisCache(Protocol):
    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any, ttl_seconds: int) -> None: ...

    def clear(self) -> None: ...


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)

    def clear(self) -> None:
        self._store.clear()


def cache_key(
    owner: str,
    repo: str,
    number: int,
    head_sha: str,
    *,
    viewer_login: str | None = None,
) -> str:
    base = f"{owner}/{repo}#{number}@{head_sha}"
    if viewer_login:
        return f"viewer:{viewer_login}:{base}"
    return base

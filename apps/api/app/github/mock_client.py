from typing import Any


class GitHubMockClient:
    """Fixture-backed GitHub client for tests and demo mode."""

    def __init__(
        self,
        *,
        pull_request: dict[str, Any],
        files: list[dict[str, Any]] | None = None,
        commits: list[dict[str, Any]] | None = None,
        repository: dict[str, Any] | None = None,
        contents: dict[str, str] | None = None,
        search_results: dict[str, Any] | None = None,
    ) -> None:
        self._pull_request = pull_request
        self._files = files or []
        self._commits = commits or []
        self._repository = repository or {
            "full_name": pull_request.get("base", {}).get("repo", {}).get("full_name", "demo/demo")
        }
        self._contents = contents or {}
        self._search_results = search_results or {"total_count": 0, "incomplete_results": False, "items": []}

    async def get_pull_request(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        return self._pull_request

    async def get_pull_request_files(
        self, owner: str, repo: str, number: int
    ) -> list[dict[str, Any]]:
        return list(self._files)

    async def get_pull_request_commits(
        self, owner: str, repo: str, number: int
    ) -> list[dict[str, Any]]:
        return list(self._commits)

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return self._repository

    async def get_file_contents(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        return self._contents.get(path)

    async def search_pull_requests(self, query: str, per_page: int = 30) -> dict[str, Any]:
        return dict(self._search_results)

    async def aclose(self) -> None:
        return None

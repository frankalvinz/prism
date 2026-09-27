from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GitHubClient(Protocol):
    async def get_pull_request(self, owner: str, repo: str, number: int) -> dict[str, Any]: ...

    async def get_pull_request_files(
        self, owner: str, repo: str, number: int
    ) -> list[dict[str, Any]]: ...

    async def get_pull_request_commits(
        self, owner: str, repo: str, number: int
    ) -> list[dict[str, Any]]: ...

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]: ...

    async def get_file_contents(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None: ...

    async def search_pull_requests(self, query: str, per_page: int = 30) -> dict[str, Any]: ...

    async def aclose(self) -> None: ...

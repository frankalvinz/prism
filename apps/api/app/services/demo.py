import json
from pathlib import Path
from typing import Any

from app.github.mock_client import GitHubMockClient

# Repo root: apps/api/app/services/demo.py -> parents[4] = prism root
FIXTURES_DIR = Path(__file__).resolve().parents[4] / "fixtures" / "github"


def load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURES_DIR / f"{name}.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def demo_github_client() -> GitHubMockClient:
    data = load_fixture("demo_pr")
    return GitHubMockClient(
        pull_request=data["pull_request"],
        files=data.get("files", []),
        commits=data.get("commits", []),
        repository=data.get("repository"),
    )


def fixture_github_client(name: str) -> GitHubMockClient:
    data = load_fixture(name)
    return GitHubMockClient(
        pull_request=data["pull_request"],
        files=data.get("files", []),
        commits=data.get("commits", []),
        repository=data.get("repository"),
    )

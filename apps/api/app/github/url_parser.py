import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.exceptions import InvalidUrlError

_PR_PATH = re.compile(r"^/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)/?$")


@dataclass(frozen=True)
class ParsedPrUrl:
    owner: str
    repo: str
    number: int
    html_url: str


def parse_github_pr_url(url: str) -> ParsedPrUrl:
    if not url or not isinstance(url, str):
        raise InvalidUrlError("A GitHub pull request URL is required.")

    raw = url.strip()
    parsed = urlparse(raw)

    if parsed.scheme not in {"http", "https"}:
        raise InvalidUrlError("URL must use http or https.", details={"url": raw})

    host = (parsed.hostname or "").lower()
    if host not in {"github.com", "www.github.com"}:
        raise InvalidUrlError(
            "Only github.com pull request URLs are supported.",
            details={"hostname": host},
        )

    match = _PR_PATH.match(parsed.path or "")
    if not match:
        raise InvalidUrlError(
            "URL must match https://github.com/{owner}/{repo}/pull/{number}",
            details={"path": parsed.path},
        )

    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))

    if number < 1:
        raise InvalidUrlError("Pull request number must be a positive integer.")

    html_url = f"https://github.com/{owner}/{repo}/pull/{number}"
    return ParsedPrUrl(owner=owner, repo=repo, number=number, html_url=html_url)

import pytest

from app.core.exceptions import InvalidUrlError
from app.github.url_parser import parse_github_pr_url


def test_parse_valid_url():
    parsed = parse_github_pr_url("https://github.com/owner/repo/pull/123")
    assert parsed.owner == "owner"
    assert parsed.repo == "repo"
    assert parsed.number == 123


def test_parse_www_and_trailing_slash():
    parsed = parse_github_pr_url("https://www.github.com/acme/widgets/pull/7/")
    assert parsed.owner == "acme"
    assert parsed.number == 7


def test_reject_non_github_host():
    with pytest.raises(InvalidUrlError) as exc:
        parse_github_pr_url("https://gitlab.com/owner/repo/pull/1")
    assert exc.value.code == "INVALID_URL"


def test_reject_malformed_path():
    with pytest.raises(InvalidUrlError):
        parse_github_pr_url("https://github.com/owner/repo/issues/1")

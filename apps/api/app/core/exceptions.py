from typing import Any


class PrismError(Exception):
    """Base application error."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidUrlError(PrismError):
    code = "INVALID_URL"
    status_code = 400


class GitHubNotFoundError(PrismError):
    code = "GITHUB_NOT_FOUND"
    status_code = 404


class GitHubRateLimitedError(PrismError):
    code = "GITHUB_RATE_LIMITED"
    status_code = 429


class GitHubApiError(PrismError):
    code = "GITHUB_API_ERROR"
    status_code = 502


class GitHubAuthError(PrismError):
    code = "GITHUB_AUTH_EXPIRED"
    status_code = 401


class AuthRequiredError(PrismError):
    code = "AUTH_REQUIRED"
    status_code = 401


class PrTooLargeError(PrismError):
    code = "PR_TOO_LARGE"
    status_code = 413


class AnalysisFailedError(PrismError):
    code = "ANALYSIS_FAILED"
    status_code = 500


class UnsupportedContentError(PrismError):
    code = "UNSUPPORTED_CONTENT"
    status_code = 422

from fastapi.responses import JSONResponse

from app.core.exceptions import GitHubAuthError
from app.core.session import clear_session_cookie


def auth_expired_response(exc: GitHubAuthError) -> JSONResponse:
    """Build a GITHUB_AUTH_EXPIRED JSON body and clear the session cookie."""
    error_response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
    clear_session_cookie(error_response)
    return error_response

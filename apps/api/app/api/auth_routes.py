from urllib.parse import quote

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import get_settings
from app.core.constants import (
    AUTH_PREFIX,
    SESSION_COOKIE,
    STATE_COOKIE,
    WEB_HOME_PATH,
    WEB_WELCOME_PATH,
)
from app.core.exceptions import GitHubApiError
from app.core.logging import get_logger
from app.core.session import (
    clear_session_cookie,
    clear_state_cookie,
    create_oauth_state,
    decrypt_session,
    encrypt_session,
    set_session_cookie,
    set_state_cookie,
    verify_oauth_state,
)
from app.github import oauth as github_oauth

logger = get_logger(__name__)

router = APIRouter(prefix=AUTH_PREFIX)


@router.get("/github/login")
async def github_login() -> Response:
    settings = get_settings()
    if not settings.oauth_enabled:
        return RedirectResponse(
            url=(
                f"{settings.public_web_url.rstrip('/')}{WEB_WELCOME_PATH}"
                f"?auth_error={quote('oauth_disabled')}"
            ),
            status_code=302,
        )
    raw_state, signed = create_oauth_state(settings)
    response = RedirectResponse(url=github_oauth.authorize_url(settings, raw_state), status_code=302)
    set_state_cookie(response, settings, signed)
    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> Response:
    settings = get_settings()
    home = settings.public_web_url.rstrip("/")

    def fail(reason: str) -> RedirectResponse:
        resp = RedirectResponse(
            url=f"{home}{WEB_WELCOME_PATH}?auth_error={quote(reason)}",
            status_code=302,
        )
        clear_state_cookie(resp)
        return resp

    if error:
        return fail(error)
    if not settings.oauth_enabled:
        return fail("oauth_disabled")
    if not code or not state:
        return fail("missing_code")

    cookie_state = request.cookies.get(STATE_COOKIE)
    if not verify_oauth_state(settings, cookie_state, state):
        logger.warning("oauth.state_mismatch")
        return fail("state_mismatch")

    try:
        token = await github_oauth.exchange_code(settings, code)
        user = await github_oauth.fetch_user(settings, token)
    except GitHubApiError:
        return fail("exchange_failed")
    except Exception:
        logger.warning("oauth.callback_unexpected")
        return fail("exchange_failed")

    login = str(user.get("login") or "")
    avatar = user.get("avatar_url") if isinstance(user.get("avatar_url"), str) else None
    cookie_value = encrypt_session(settings, token=token, login=login, avatar_url=avatar)
    if not cookie_value:
        return fail("session_failed")

    response = RedirectResponse(url=f"{home}{WEB_HOME_PATH}", status_code=302)
    set_session_cookie(response, settings, cookie_value)
    clear_state_cookie(response)
    logger.info("oauth.login_success login=%s", login)
    return response


@router.get("/me")
async def auth_me(request: Request) -> JSONResponse:
    settings = get_settings()
    session = decrypt_session(settings, request.cookies.get(SESSION_COOKIE))
    if session is None:
        return JSONResponse(
            {
                "oauth_enabled": settings.oauth_enabled,
                "authenticated": False,
                "login": None,
                "avatar_url": None,
            }
        )
    return JSONResponse(
        {
            "oauth_enabled": settings.oauth_enabled,
            "authenticated": True,
            "login": session.login,
            "avatar_url": session.avatar_url,
        }
    )


@router.post("/logout")
async def auth_logout(request: Request) -> JSONResponse:
    settings = get_settings()
    session = decrypt_session(settings, request.cookies.get(SESSION_COOKIE))
    if session is not None:
        await github_oauth.revoke_grant(settings, session.token)
        logger.info("oauth.logout login=%s", session.login)
    response = JSONResponse({"ok": True})
    clear_session_cookie(response)
    clear_state_cookie(response)
    return response

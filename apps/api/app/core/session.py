"""Encrypted viewer session and OAuth state cookies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Response

from app.core.config import Settings

# Re-export cookie names so existing imports keep working.
from app.core.constants import (  # noqa: F401
    SESSION_COOKIE,
    STATE_COOKIE,
    STATE_TTL_SECONDS,
)


@dataclass(frozen=True)
class ViewerSession:
    token: str
    login: str
    avatar_url: str | None
    exp: float

    @property
    def expired(self) -> bool:
        return time.time() >= self.exp


def _fernet(settings: Settings) -> Fernet | None:
    secret = settings.session_secret or settings.github_oauth_client_secret
    if not secret:
        return None
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_session(settings: Settings, *, token: str, login: str, avatar_url: str | None) -> str | None:
    f = _fernet(settings)
    if f is None:
        return None
    payload = {
        "token": token,
        "login": login,
        "avatar_url": avatar_url,
        "exp": time.time() + settings.session_ttl_seconds,
    }
    return f.encrypt(json.dumps(payload).encode("utf-8")).decode("utf-8")


def decrypt_session(settings: Settings, value: str | None) -> ViewerSession | None:
    if not value:
        return None
    f = _fernet(settings)
    if f is None:
        return None
    try:
        raw = f.decrypt(value.encode("utf-8"))
        data: dict[str, Any] = json.loads(raw.decode("utf-8"))
    except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError):
        return None

    token = data.get("token")
    login = data.get("login")
    exp = data.get("exp")
    if not isinstance(token, str) or not isinstance(login, str) or not isinstance(exp, (int, float)):
        return None

    session = ViewerSession(
        token=token,
        login=login,
        avatar_url=data.get("avatar_url") if isinstance(data.get("avatar_url"), str) else None,
        exp=float(exp),
    )
    if session.expired:
        return None
    return session


def create_oauth_state(settings: Settings) -> tuple[str, str]:
    """Return (raw_state, signed_cookie_value)."""
    raw = secrets.token_urlsafe(24)
    secret = (settings.session_secret or settings.github_oauth_client_secret or "prism-dev").encode(
        "utf-8"
    )
    exp = int(time.time()) + STATE_TTL_SECONDS
    payload = f"{raw}.{exp}"
    sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return raw, f"{payload}.{sig}"


def verify_oauth_state(settings: Settings, cookie_value: str | None, provided: str | None) -> bool:
    if not cookie_value or not provided:
        return False
    parts = cookie_value.split(".")
    if len(parts) != 3:
        return False
    raw, exp_str, sig = parts
    if raw != provided:
        return False
    try:
        exp = int(exp_str)
    except ValueError:
        return False
    if time.time() > exp:
        return False
    secret = (settings.session_secret or settings.github_oauth_client_secret or "prism-dev").encode(
        "utf-8"
    )
    expected = hmac.new(secret, f"{raw}.{exp_str}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def set_session_cookie(response: Response, settings: Settings, value: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=value,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_ttl_seconds,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")


def set_state_cookie(response: Response, settings: Settings, value: str) -> None:
    response.set_cookie(
        key=STATE_COOKIE,
        value=value,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=STATE_TTL_SECONDS,
        path="/",
    )


def clear_state_cookie(response: Response) -> None:
    response.delete_cookie(key=STATE_COOKIE, path="/")

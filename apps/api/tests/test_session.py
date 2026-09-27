import time

import pytest

from app.core.config import Settings
from app.core.session import (
    create_oauth_state,
    decrypt_session,
    encrypt_session,
    verify_oauth_state,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        github_oauth_client_id="client",
        github_oauth_client_secret="secret",
        session_secret="unit-test-session-secret-value",
        session_ttl_seconds=3600,
    )


def test_session_round_trip(settings: Settings):
    cookie = encrypt_session(
        settings, token="gho_test", login="alice", avatar_url="https://example.com/a.png"
    )
    assert cookie
    session = decrypt_session(settings, cookie)
    assert session is not None
    assert session.login == "alice"
    assert session.token == "gho_test"
    assert session.avatar_url == "https://example.com/a.png"


def test_tampered_session_rejected(settings: Settings):
    cookie = encrypt_session(settings, token="gho_test", login="alice", avatar_url=None)
    assert cookie
    tampered = cookie[:-4] + ("AAAA" if not cookie.endswith("AAAA") else "BBBB")
    assert decrypt_session(settings, tampered) is None


def test_expired_session_rejected(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    now = time.time()
    monkeypatch.setattr("app.core.session.time.time", lambda: now)
    cookie = encrypt_session(settings, token="gho_test", login="alice", avatar_url=None)
    assert cookie
    monkeypatch.setattr("app.core.session.time.time", lambda: now + 10_000)
    assert decrypt_session(settings, cookie) is None


def test_oauth_state_round_trip(settings: Settings):
    raw, signed = create_oauth_state(settings)
    assert verify_oauth_state(settings, signed, raw)
    assert not verify_oauth_state(settings, signed, "wrong")
    assert not verify_oauth_state(settings, "bad.1.sig", raw)

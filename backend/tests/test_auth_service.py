"""
Tests for services/auth_service.py

Coverage
--------
- verify_jwt: valid token → UserClaims returned
- verify_jwt: expired token → AuthServiceError
- verify_jwt: tampered/invalid token → AuthServiceError
- verify_jwt: missing SUPABASE_JWT_SECRET → AuthServiceError
- verify_jwt: token missing 'sub' claim → AuthServiceError
- get_user_plan: user row exists → plan returned
- get_user_plan: user row not found → 'trial' returned
- get_user_plan: DB error → AuthServiceError
- create_user_if_not_exists: success (upsert called)
- create_user_if_not_exists: DB error → AuthServiceError
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

import services.auth_service as auth_module
from services.auth_service import (
    AuthServiceError,
    UserClaims,
    create_user_if_not_exists,
    get_user_plan,
    verify_jwt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECRET = "test-secret-key-at-least-32-chars-long"
_ALGORITHM = "HS256"


def _make_token(
    user_id: str = "user-123",
    email: str = "test@example.com",
    exp_offset: int = 3600,  # seconds from now; negative → expired
) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": int(time.time()) + exp_offset,
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


# ---------------------------------------------------------------------------
# verify_jwt
# ---------------------------------------------------------------------------


async def test_verify_jwt_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid JWT → UserClaims with correct user_id, email, and plan from DB."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", _SECRET)

    # Stub out get_user_plan so we don't need a real DB
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "niche")

    token = _make_token(user_id="abc-123", email="user@test.com")
    claims = verify_jwt(token)

    assert claims["user_id"] == "abc-123"
    assert claims["email"] == "user@test.com"
    assert claims["plan"] == "niche"


async def test_verify_jwt_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expired JWT → AuthServiceError."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", _SECRET)
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "trial")

    token = _make_token(exp_offset=-1)  # expired 1 second ago

    with pytest.raises(AuthServiceError, match="süresi dolmuş|Geçersiz"):
        verify_jwt(token)


async def test_verify_jwt_tampered_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token signed with wrong key → AuthServiceError."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", _SECRET)
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "trial")

    token = _make_token()
    tampered = token[:-4] + "XXXX"  # corrupt the signature

    with pytest.raises(AuthServiceError):
        verify_jwt(tampered)


async def test_verify_jwt_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing SUPABASE_JWT_SECRET → AuthServiceError (wraps EnvironmentError)."""
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

    with pytest.raises(AuthServiceError, match="SUPABASE_JWT_SECRET"):
        verify_jwt("any.token.value")


async def test_verify_jwt_missing_sub(monkeypatch: pytest.MonkeyPatch) -> None:
    """JWT without 'sub' claim → AuthServiceError."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", _SECRET)
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "trial")

    # Build token without 'sub'
    payload = {"email": "user@test.com", "exp": int(time.time()) + 3600}
    token = jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)

    with pytest.raises(AuthServiceError, match="kullanıcı kimliği"):
        verify_jwt(token)


# ---------------------------------------------------------------------------
# get_user_plan
# ---------------------------------------------------------------------------


async def test_get_user_plan_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """User row exists in DB → plan string returned."""
    mock_resp = MagicMock()
    mock_resp.data = {"plan": "full"}

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_resp
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(auth_module, "get_service_client", lambda: mock_client)

    plan = get_user_plan("user-456")
    assert plan == "full"


async def test_get_user_plan_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """No user row → 'trial' returned (default plan for new users)."""
    mock_resp = MagicMock()
    mock_resp.data = None  # .maybe_single() returns None when not found

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_resp
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(auth_module, "get_service_client", lambda: mock_client)

    plan = get_user_plan("new-user")
    assert plan == "trial"


async def test_get_user_plan_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """DB raises unexpected exception → AuthServiceError."""
    mock_chain = MagicMock()
    mock_chain.execute.side_effect = RuntimeError("connection refused")
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(auth_module, "get_service_client", lambda: mock_client)

    with pytest.raises(AuthServiceError, match="hata"):
        get_user_plan("user-error")


# ---------------------------------------------------------------------------
# create_user_if_not_exists
# ---------------------------------------------------------------------------


async def test_create_user_if_not_exists_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: upsert called with correct data."""
    mock_chain = MagicMock()
    mock_chain.execute.return_value = MagicMock()
    mock_chain.upsert.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(auth_module, "get_service_client", lambda: mock_client)

    create_user_if_not_exists("user-new", "new@example.com")  # should not raise

    mock_client.table.assert_called_once_with("users")
    mock_chain.upsert.assert_called_once()
    upsert_kwargs = mock_chain.upsert.call_args
    inserted_data = upsert_kwargs.args[0]
    assert inserted_data["id"] == "user-new"
    assert inserted_data["email"] == "new@example.com"
    assert inserted_data["plan"] == "trial"


async def test_create_user_if_not_exists_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """DB raises on upsert → AuthServiceError."""
    mock_chain = MagicMock()
    mock_chain.execute.side_effect = RuntimeError("DB down")
    mock_chain.upsert.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(auth_module, "get_service_client", lambda: mock_client)

    with pytest.raises(AuthServiceError, match="hata"):
        create_user_if_not_exists("user-fail", "fail@example.com")

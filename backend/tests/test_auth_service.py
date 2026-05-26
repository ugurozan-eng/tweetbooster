"""
Tests for services/auth_service.py

Coverage
--------
- verify_jwt: valid ES256 token → UserClaims returned
- verify_jwt: expired token → AuthServiceError
- verify_jwt: tampered/invalid token → AuthServiceError
- verify_jwt: JWKS fetch fails (SUPABASE_URL missing) → EnvironmentError / AuthServiceError
- verify_jwt: token missing 'sub' claim → AuthServiceError
- verify_jwt: kid not found in JWKS → falls back to first key, still verifies
- get_user_plan: user row exists → plan returned
- get_user_plan: user row not found → 'trial' returned
- get_user_plan: DB error → AuthServiceError
- create_user_if_not_exists: success (upsert called with correct data)
- create_user_if_not_exists: DB error → AuthServiceError

Key strategy
------------
Tests use a module-level EC P-256 key pair (generated once at import time).
_fetch_jwks is monkeypatched to return the test public key as a JWK dict.
Tokens are signed with the test private key via jose's ES256 support.
"""

from __future__ import annotations

import base64
import time
from unittest.mock import MagicMock

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1, generate_private_key
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from jose import jwt as jose_jwt

import services.auth_service as auth_module
from services.auth_service import (
    AuthServiceError,
    UserClaims,
    create_user_if_not_exists,
    get_user_plan,
    verify_jwt,
)

# ---------------------------------------------------------------------------
# Module-level EC P-256 key pair — generated once, reused by all tests
# ---------------------------------------------------------------------------

_EC_PRIVATE_KEY = generate_private_key(SECP256R1(), default_backend())
_EC_PRIVATE_PEM = _EC_PRIVATE_KEY.private_bytes(
    Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
)


def _int_to_base64url(n: int, byte_length: int = 32) -> str:
    """Encode an EC coordinate integer as a base64url string."""
    return base64.urlsafe_b64encode(
        n.to_bytes(byte_length, "big")
    ).decode().rstrip("=")


def _make_test_jwks() -> dict:
    """Return the test public key as a JWKS dict (same shape as Supabase returns)."""
    pub = _EC_PRIVATE_KEY.public_key().public_numbers()
    return {
        "keys": [
            {
                "kty": "EC",
                "crv": "P-256",
                "x": _int_to_base64url(pub.x),
                "y": _int_to_base64url(pub.y),
                "alg": "ES256",
                "use": "sig",
                "kid": "test-key-id",
            }
        ]
    }


def _make_token(
    user_id: str = "user-123",
    email: str = "test@example.com",
    exp_offset: int = 3600,
    kid: str = "test-key-id",
) -> str:
    """Sign a test JWT with the module-level EC private key."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": int(time.time()) + exp_offset,
    }
    headers = {"kid": kid}
    return jose_jwt.encode(
        payload, _EC_PRIVATE_PEM, algorithm="ES256", headers=headers
    )


# ---------------------------------------------------------------------------
# verify_jwt
# ---------------------------------------------------------------------------


async def test_verify_jwt_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid ES256 JWT → UserClaims with correct user_id, email, and plan from DB."""
    monkeypatch.setattr(auth_module, "_fetch_jwks", lambda: _make_test_jwks())
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "niche")

    token = _make_token(user_id="abc-123", email="user@test.com")
    claims = verify_jwt(token)

    assert claims["user_id"] == "abc-123"
    assert claims["email"] == "user@test.com"
    assert claims["plan"] == "niche"


async def test_verify_jwt_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expired JWT → AuthServiceError."""
    monkeypatch.setattr(auth_module, "_fetch_jwks", lambda: _make_test_jwks())
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "trial")

    token = _make_token(exp_offset=-1)  # expired 1 second ago

    with pytest.raises(AuthServiceError, match="süresi dolmuş|Geçersiz"):
        verify_jwt(token)


async def test_verify_jwt_tampered_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token with corrupted signature → AuthServiceError."""
    monkeypatch.setattr(auth_module, "_fetch_jwks", lambda: _make_test_jwks())
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "trial")

    token = _make_token()
    tampered = token[:-6] + "XXXXXX"  # corrupt the signature

    with pytest.raises(AuthServiceError):
        verify_jwt(tampered)


async def test_verify_jwt_supabase_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """SUPABASE_URL not set → _fetch_jwks raises EnvironmentError, propagated."""
    # Remove cache so _fetch_jwks is actually called
    monkeypatch.setattr(auth_module, "_jwks_cache", None)
    monkeypatch.setattr(auth_module, "_jwks_cache_expiry", 0.0)
    monkeypatch.delenv("SUPABASE_URL", raising=False)

    token = _make_token()
    with pytest.raises((EnvironmentError, AuthServiceError)):
        verify_jwt(token)


async def test_verify_jwt_missing_sub(monkeypatch: pytest.MonkeyPatch) -> None:
    """JWT without 'sub' claim → AuthServiceError."""
    monkeypatch.setattr(auth_module, "_fetch_jwks", lambda: _make_test_jwks())
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "trial")

    # Build token without 'sub'
    payload = {
        "email": "user@test.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jose_jwt.encode(
        payload, _EC_PRIVATE_PEM, algorithm="ES256", headers={"kid": "test-key-id"}
    )

    with pytest.raises(AuthServiceError, match="kullanıcı kimliği"):
        verify_jwt(token)


async def test_verify_jwt_kid_not_in_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token kid not in JWKS → falls back to first key → still verifies."""
    monkeypatch.setattr(auth_module, "_fetch_jwks", lambda: _make_test_jwks())
    monkeypatch.setattr(auth_module, "get_user_plan", lambda uid: "full")

    # Sign with a different kid header — JWKS has "test-key-id" but token claims "other"
    token = _make_token(kid="other-key-id")
    # Falls back to first key in JWKS — which IS our test key, so verification succeeds
    claims = verify_jwt(token)
    assert claims["plan"] == "full"


# ---------------------------------------------------------------------------
# get_user_plan
# ---------------------------------------------------------------------------


async def test_get_user_plan_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """User row exists in DB → plan string returned.

    get_user_plan() now delegates to subscription_service.get_active_plan(),
    so we patch the Supabase client on that module instead.
    """
    import services.subscription_service as sub_module

    mock_resp = MagicMock()
    mock_resp.data = {"plan": "full", "plan_expires_at": None}

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_resp
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(sub_module, "get_service_client", lambda: mock_client)

    plan = get_user_plan("user-456")
    assert plan == "full"


async def test_get_user_plan_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """No user row → 'trial' returned (default plan for new users)."""
    import services.subscription_service as sub_module

    mock_resp = MagicMock()
    mock_resp.data = None

    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_resp
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(sub_module, "get_service_client", lambda: mock_client)

    plan = get_user_plan("new-user")
    assert plan == "trial"


async def test_get_user_plan_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """DB raises unexpected exception → AuthServiceError."""
    import services.subscription_service as sub_module

    mock_chain = MagicMock()
    mock_chain.execute.side_effect = RuntimeError("connection refused")
    mock_chain.eq.return_value = mock_chain
    mock_chain.maybe_single.return_value = mock_chain
    mock_chain.select.return_value = mock_chain

    mock_client = MagicMock()
    mock_client.table.return_value = mock_chain

    monkeypatch.setattr(sub_module, "get_service_client", lambda: mock_client)

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

    create_user_if_not_exists("user-new", "new@example.com")  # must not raise

    mock_client.table.assert_called_once_with("users")
    mock_chain.upsert.assert_called_once()
    inserted_data = mock_chain.upsert.call_args.args[0]
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

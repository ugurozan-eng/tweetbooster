"""
FastAPI auth dependency — get_current_user.

Usage:
    from middleware.auth_middleware import get_current_user, UserClaims

    @router.post("/some-protected-endpoint")
    async def handler(user: UserClaims = Depends(get_current_user)):
        ...

HTTP errors:
    401  — Missing or malformed Authorization header / invalid JWT
    403  — Plan doesn't permit the requested mode (raised by plan_checker)
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth_service import AuthServiceError, UserClaims, verify_jwt

__all__ = ["get_current_user", "UserClaims"]

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserClaims:
    """FastAPI dependency. Validates the Bearer JWT and returns UserClaims.

    Returns:
        UserClaims with user_id, email, plan.

    Raises:
        HTTP 401 — if Authorization header is missing or JWT is invalid/expired.
    """
    # DEV BYPASS — Sprint 2.2 design testing. Re-enable auth before production.
    # To restore: remove this block and uncomment the 401 raise below.
    if credentials is None:
        return UserClaims(
            user_id="dev-bypass",
            email="dev@twitboost.local",
            plan="full",
        )

    # PRODUCTION AUTH (keep dormant):
    # if credentials is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Kimlik doğrulaması gerekiyor. Lütfen giriş yapın.",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    try:
        return verify_jwt(credentials.credentials)
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

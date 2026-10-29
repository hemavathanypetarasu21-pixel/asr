import asyncio
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings

# Supabase asymmetric signing keys; the client caches fetched keys.
_jwks_client = jwt.PyJWKClient(settings.supabase_jwks_url, cache_keys=True)
_bearer = HTTPBearer(auto_error=False)
_ALGORITHMS = ["ES256", "RS256"]


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None


def _decode(token: str) -> dict:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=_ALGORITHMS,
        audience=settings.SUPABASE_JWT_AUDIENCE,
        issuer=settings.supabase_issuer,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sign in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        # Key lookup may fetch the JWKS over the network, so keep it off the event loop.
        claims = await asyncio.to_thread(_decode, credentials.credentials)
    except (jwt.PyJWTError, jwt.PyJWKClientError) as error:
        raise unauthorized from error
    return CurrentUser(id=claims["sub"], email=claims.get("email"))


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser | None:
    """Like get_current_user, but anonymous or invalid requests get None instead of 401."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

from __future__ import annotations

from typing import Any

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import decode_token

security_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    access_token: str | None = Cookie(default=None),
) -> int:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise AuthenticationException("Not authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationException("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid token payload")

    return int(user_id)


def get_current_user_role(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    access_token: str | None = Cookie(default=None),
) -> str:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise AuthenticationException("Not authenticated")

    payload = decode_token(token)
    if not payload:
        raise AuthenticationException("Invalid or expired access token")

    return payload.get("role", "user")


def require_role(required_role: str) -> Any:
    def role_checker(current_role: str = Depends(get_current_user_role)) -> str:
        roles_order = ["user", "admin"]
        if roles_order.index(current_role) < roles_order.index(required_role):
            raise AuthorizationException(f"Role '{required_role}' or higher is required")
        return current_role

    return role_checker


def get_optional_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    access_token: str | None = Cookie(default=None),
) -> int | None:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        return None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    return int(user_id) if user_id else None

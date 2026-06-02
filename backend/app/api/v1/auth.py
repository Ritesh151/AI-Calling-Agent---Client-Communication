from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.common import SuccessResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _cookie_kwargs(max_age: int) -> dict:
    return {
        "httponly": True,
        "secure": settings.ENVIRONMENT.lower() in ("production", "prod", "staging"),
        "samesite": "lax",
        "max_age": max_age,
        "path": "/",
    }


@router.post("/register", response_model=SuccessResponse[UserRead])
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> SuccessResponse[UserRead]:
    service = AuthService(db)
    user = service.register(request)
    return SuccessResponse(message="Registration successful", data=user)


@router.post("/login", response_model=SuccessResponse[TokenResponse])
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    service = AuthService(db)
    access_token, refresh_token = service.login(request)

    response.set_cookie(key="access_token", value=access_token, **_cookie_kwargs(1800))
    response.set_cookie(key="refresh_token", value=refresh_token, **_cookie_kwargs(604800))

    return SuccessResponse(
        message="Login successful",
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token),
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
def refresh_token(
    request: RefreshRequest | None = None,
    response: Response = None,
    db: Session = Depends(get_db),
    refresh_cookie: str | None = None,
) -> SuccessResponse[TokenResponse]:
    token = refresh_cookie or (request.refresh_token if request else None)
    if not token:
        from app.core.exceptions import AuthenticationException

        raise AuthenticationException("Refresh token is required")

    service = AuthService(db)
    access_token, new_refresh = service.refresh_token(token)

    if response:
        response.set_cookie(key="access_token", value=access_token, **_cookie_kwargs(1800))
        response.set_cookie(key="refresh_token", value=new_refresh, **_cookie_kwargs(604800))

    return SuccessResponse(
        message="Token refreshed",
        data=TokenResponse(access_token=access_token, refresh_token=new_refresh),
    )


@router.post("/logout", response_model=SuccessResponse[None])
def logout(response: Response, user_id: int = Depends(get_current_user_id)) -> SuccessResponse[None]:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return SuccessResponse(message="Logout successful")


@router.get("/me", response_model=SuccessResponse[UserRead])
def get_me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> SuccessResponse[UserRead]:
    service = AuthService(db)
    user = service.get_current_user(user_id)
    return SuccessResponse(data=user)

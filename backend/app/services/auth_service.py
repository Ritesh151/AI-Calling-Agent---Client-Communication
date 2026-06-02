from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserRead


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def register(self, request: RegisterRequest) -> UserRead:
        if request.password != request.confirm_password:
            raise ValidationException("Passwords do not match")

        if self.user_repo.get_by_email(request.email):
            raise ConflictException("Email already registered")

        if self.user_repo.get_by_username(request.username):
            raise ConflictException("Username already taken")

        user = self.user_repo.create(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
            role="user",
            is_active=True,
        )

        return UserRead.model_validate(user)

    def login(self, request: LoginRequest) -> tuple[str, str]:
        user = self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise AuthenticationException("Invalid email or password")
        if not user.is_active:
            raise AuthenticationException("Account is deactivated")

        access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role, "email": user.email})
        refresh_token = create_refresh_token(subject=str(user.id))

        return access_token, refresh_token

    def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationException("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException("Invalid token payload")

        db_user = self.user_repo.get_by_id(int(user_id))
        if not db_user or not db_user.is_active:
            raise AuthenticationException("User not found or inactive")

        new_access = create_access_token(subject=str(db_user.id), extra_claims={"role": db_user.role, "email": db_user.email})
        new_refresh = create_refresh_token(subject=str(db_user.id))

        return new_access, new_refresh

    def get_current_user(self, user_id: int) -> UserRead:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationException("User not found")
        if not user.is_active:
            raise AuthenticationException("User is deactivated")
        return UserRead.model_validate(user)

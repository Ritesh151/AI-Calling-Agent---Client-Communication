from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def create_user(self, request: UserCreate) -> UserRead:
        if self.user_repo.get_by_email(request.email):
            raise ConflictException("Email already registered")
        if self.user_repo.get_by_username(request.username):
            raise ConflictException("Username already taken")

        user = self.user_repo.create(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
            role=request.role,
            is_active=True,
        )
        return UserRead.model_validate(user)

    def get_user(self, user_id: int) -> UserRead:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return UserRead.model_validate(user)

    def get_all_users(self, skip: int = 0, limit: int = 100) -> list[UserRead]:
        users = self.user_repo.get_all(skip=skip, limit=limit, order_by="created_at", order_desc=True)
        return [UserRead.model_validate(u) for u in users]

    def update_user(self, user_id: int, request: UserUpdate) -> UserRead:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        update_data = request.model_dump(exclude_unset=True)
        if "email" in update_data and update_data["email"]:
            existing = self.user_repo.get_by_email(update_data["email"])
            if existing and existing.id != user_id:
                raise ConflictException("Email already in use")

        updated = self.user_repo.update(user_id, **update_data)
        return UserRead.model_validate(updated)

    def delete_user(self, user_id: int) -> None:
        if not self.user_repo.delete(user_id):
            raise NotFoundException("User not found")

    def get_user_count(self) -> int:
        return self.user_repo.count()

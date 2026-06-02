from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, require_role
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=SuccessResponse[list[UserRead]])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[list[UserRead]]:
    service = UserService(db)
    users = service.get_all_users(skip=skip, limit=limit)
    return SuccessResponse(data=users)


@router.get("/{user_id}", response_model=SuccessResponse[UserRead])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[UserRead]:
    service = UserService(db)
    user = service.get_user(user_id)
    return SuccessResponse(data=user)


@router.post("/", response_model=SuccessResponse[UserRead])
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[UserRead]:
    service = UserService(db)
    user = service.create_user(request)
    return SuccessResponse(message="User created", data=user)


@router.put("/{user_id}", response_model=SuccessResponse[UserRead])
def update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[UserRead]:
    service = UserService(db)
    user = service.update_user(user_id, request)
    return SuccessResponse(message="User updated", data=user)


@router.delete("/{user_id}", response_model=SuccessResponse[None])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[None]:
    service = UserService(db)
    service.delete_user(user_id)
    return SuccessResponse(message="User deleted")

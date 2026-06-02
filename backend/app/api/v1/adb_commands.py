from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, require_role
from app.core.database import get_db
from app.db.models.adb_command import ADBCommand
from app.schemas.common import SuccessResponse
from app.schemas.adb_command import ADBCommandRead

router = APIRouter(prefix="/adb-commands", tags=["ADB Commands"])


@router.get("/", response_model=SuccessResponse[list[ADBCommandRead]])
def list_commands(
    device_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[list[ADBCommandRead]]:
    query = db.query(ADBCommand)
    if device_id:
        query = query.filter(ADBCommand.device_id == device_id)
    commands = query.order_by(ADBCommand.executed_at.desc().nullslast()).limit(limit).all()
    return SuccessResponse(
        data=[ADBCommandRead.model_validate(c) for c in commands]
    )


@router.get("/{command_id}", response_model=SuccessResponse[ADBCommandRead])
def get_command(
    command_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[ADBCommandRead]:
    command = db.query(ADBCommand).filter(ADBCommand.id == command_id).first()
    if not command:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("ADB command not found")
    return SuccessResponse(data=ADBCommandRead.model_validate(command))

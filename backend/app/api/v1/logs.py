from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.system_log import SystemLogRead
from app.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["System Logs"])


@router.get("/", response_model=SuccessResponse[list[SystemLogRead]])
def list_logs(
    level: str | None = Query(None),
    module: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[list[SystemLogRead]]:
    service = LogService(db)
    if level:
        logs = service.get_logs_by_level(level, limit=limit)
    elif module:
        logs = service.get_logs_by_module(module, limit=limit)
    else:
        logs = service.get_recent_logs(limit=limit)
    return SuccessResponse(data=logs)


@router.get("/{log_id}", response_model=SuccessResponse[SystemLogRead])
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[SystemLogRead]:
    service = LogService(db)
    log = service.get_log(log_id)
    return SuccessResponse(data=log)

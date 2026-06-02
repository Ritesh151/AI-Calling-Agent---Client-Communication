from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.services.call_archive import ArchiveService

router = APIRouter()


@router.get("/stats", response_model=SuccessResponse[dict])
def get_archive_stats(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = ArchiveService(db)
    stats = service.get_storage_stats()
    return SuccessResponse(data=stats)


@router.post("/cleanup", response_model=SuccessResponse[dict])
def run_cleanup(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = ArchiveService(db)
    archived = service.archive_expired_recordings()
    deleted = service.delete_expired_recordings()
    return SuccessResponse(
        message="Cleanup completed",
        data={"archived": archived, "deleted": deleted},
    )

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.services.reporting import ReportService

router = APIRouter()


@router.post("/generate", response_model=SuccessResponse[dict])
def generate_report(
    report_type: str = Query(...),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    fmt: str = Query("csv"),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = ReportService(db)
    result = service.generate_report(
        report_type=report_type,
        date_from=date_from,
        date_to=date_to,
        fmt=fmt,
    )
    return SuccessResponse(message="Report generated", data=result)


@router.get("/download/{file_path:path}")
def download_report(
    file_path: str,
    _: int = Depends(get_current_user_id),
) -> FileResponse:
    from app.core.config import settings
    from pathlib import Path
    full_path = Path(settings.REPORT_DIR) / file_path
    if not full_path.exists():
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Report file not found")
    return FileResponse(str(full_path), filename=full_path.name)

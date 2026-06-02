"""
Call Data Export API endpoints
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends
from starlette.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.schemas.common import SuccessResponse
from app.services.call_data_export import CallDataExporter
from app.core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/call-export", tags=["export"])


@router.post("/greeting/{call_session_id}")
def export_greeting_data(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    """
    Export greeting and call data for a specific call to Excel
    
    Includes:
    - Call information (ID, number, date/time)
    - Greeting status
    - Language selection
    - Greeting messages
    - Timestamps
    """
    try:
        exporter = CallDataExporter(db)
        file_path = exporter.export_greeting_data(call_session_id)
        
        if not file_path:
            raise ValidationException("Excel export not available. openpyxl not installed.")
        
        return SuccessResponse(
            data={
                "status": "exported",
                "call_id": call_session_id,
                "file_path": str(file_path),
                "filename": file_path.name,
            },
            message="Greeting data exported successfully"
        )
    except NotFoundException as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error("Error exporting greeting data: %s", e)
        raise ValidationException(str(e))


@router.get("/greeting/{call_session_id}/download")
def download_greeting_data(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> FileResponse:
    """
    Download greeting and call data Excel file for a specific call
    """
    try:
        exporter = CallDataExporter(db)
        file_path = exporter.export_greeting_data(call_session_id)
        
        if not file_path or not file_path.exists():
            raise NotFoundException("Export file not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error("Error downloading greeting data: %s", e)
        raise ValidationException(str(e))


@router.post("/all-calls")
def export_all_calls(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    """
    Export all calls with greeting data to Excel
    """
    try:
        exporter = CallDataExporter(db)
        file_path = exporter.export_all_calls()
        
        if not file_path:
            raise ValidationException("No calls to export or openpyxl not installed")
        
        return SuccessResponse(
            data={
                "status": "exported",
                "file_path": str(file_path),
                "filename": file_path.name,
            },
            message="All calls data exported successfully"
        )
    except Exception as e:
        logger.error("Error exporting all calls: %s", e)
        raise ValidationException(str(e))


@router.get("/all-calls/download")
def download_all_calls(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> FileResponse:
    """
    Download all calls Excel file
    """
    try:
        exporter = CallDataExporter(db)
        file_path = exporter.export_all_calls()
        
        if not file_path or not file_path.exists():
            raise NotFoundException("Export file not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error("Error downloading all calls: %s", e)
        raise ValidationException(str(e))

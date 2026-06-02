from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.db.models.device_metric import DeviceMetric
from app.schemas.common import SuccessResponse
from app.schemas.device_metric import DeviceMetricRead

router = APIRouter(prefix="/metrics", tags=["Device Metrics"])


@router.get("/", response_model=SuccessResponse[list[DeviceMetricRead]])
def list_metrics(
    device_id: int = Query(..., description="Device ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[DeviceMetricRead]]:
    metrics = (
        db.query(DeviceMetric)
        .filter(DeviceMetric.device_id == device_id)
        .order_by(DeviceMetric.captured_at.desc())
        .limit(limit)
        .all()
    )
    return SuccessResponse(
        data=[DeviceMetricRead.model_validate(m) for m in metrics]
    )


@router.get("/latest/{device_id}", response_model=SuccessResponse[DeviceMetricRead | None])
def get_latest_metric(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[DeviceMetricRead | None]:
    metric = (
        db.query(DeviceMetric)
        .filter(DeviceMetric.device_id == device_id)
        .order_by(DeviceMetric.captured_at.desc())
        .first()
    )
    if metric:
        return SuccessResponse(data=DeviceMetricRead.model_validate(metric))
    return SuccessResponse(data=None, message="No metrics found")

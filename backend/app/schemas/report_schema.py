from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReportRequest(BaseModel):
    report_type: str
    date_from: str | None = None
    date_to: str | None = None
    format: str = "csv"


class ReportRead(BaseModel):
    id: int
    report_type: str
    format: str
    file_path: str | None
    generated_at: datetime | None
    status: str

    model_config = {"from_attributes": True}


class InsightRead(BaseModel):
    id: int
    insight_type: str
    content: str
    metric_value: float | None
    generated_at: datetime | None

    model_config = {"from_attributes": True}

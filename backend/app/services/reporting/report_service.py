from __future__ import annotations

import csv
import io
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.call_classification_model import CallClassification
from app.db.models.call_session import CallSession
from app.db.models.call_summary import CallSummary
from app.db.models.extracted_entity import ExtractedEntity
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_report(self, report_type: str, date_from: str | None = None,
                        date_to: str | None = None, fmt: str = "csv") -> dict[str, Any]:
        dfrom = self._parse_date(date_from) if date_from else datetime.now(timezone.utc) - timedelta(days=30)
        dto = self._parse_date(date_to) if date_to else datetime.now(timezone.utc)

        if report_type == "call_summary":
            data = self._call_summary_data(dfrom, dto)
        elif report_type == "transcript":
            data = self._transcript_data(dfrom, dto)
        elif report_type == "entity":
            data = self._entity_data(dfrom, dto)
        elif report_type == "classification":
            data = self._classification_data(dfrom, dto)
        elif report_type == "recording":
            data = self._recording_data(dfrom, dto)
        elif report_type == "analytics":
            data = self._analytics_data(dfrom, dto)
        else:
            data = self._call_summary_data(dfrom, dto)

        report_dir = Path(settings.REPORT_DIR)
        report_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        filepath = report_dir / filename

        if fmt == "csv":
            self._write_csv(filepath, data)
        elif fmt == "excel":
            self._write_excel(filepath, data)
        else:
            self._write_csv(filepath, data)

        return {
            "report_type": report_type,
            "format": fmt,
            "file_path": str(filepath),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(data.get("rows", [])),
            "status": "completed",
        }

    def export_csv(self, data: list[dict], filename: str) -> str:
        report_dir = Path(settings.REPORT_DIR)
        report_dir.mkdir(parents=True, exist_ok=True)
        filepath = report_dir / filename
        self._write_csv(filepath, {"columns": list(data[0].keys()) if data else [], "rows": data})
        return str(filepath)

    def _call_summary_data(self, dfrom: datetime, dto: datetime) -> dict[str, Any]:
        summaries = self.db.query(
            CallSession.id, CallSession.caller_number, CallSession.caller_name,
            CallSession.duration, CallSession.created_at,
            CallSummary.short_summary, CallSummary.urgency_level,
            CallSummary.sentiment, CallSummary.callback_required,
        ).outerjoin(CallSummary, CallSummary.call_session_id == CallSession.id
        ).filter(CallSession.created_at.between(dfrom, dto)).all()

        rows = []
        for r in summaries:
            rows.append({
                "call_id": r.id,
                "caller_number": r.caller_number or "",
                "caller_name": r.caller_name or "",
                "duration_seconds": r.duration or 0,
                "date": str(r.created_at) if r.created_at else "",
                "summary": r.short_summary or "",
                "urgency": r.urgency_level or "",
                "sentiment": r.sentiment or "",
                "callback_required": r.callback_required or "",
            })
        return {"columns": [
            "call_id", "caller_number", "caller_name", "duration_seconds",
            "date", "summary", "urgency", "sentiment", "callback_required",
        ], "rows": rows}

    def _transcript_data(self, dfrom: datetime, dto: datetime) -> dict[str, Any]:
        transcripts = self.db.query(
            CallSession.id, CallSession.caller_number,
            Transcript.transcript_text, Transcript.confidence_score,
            Transcript.language, Transcript.created_at,
        ).join(Transcript, Transcript.recording_id == CallSession.id
        ).filter(CallSession.created_at.between(dfrom, dto)).all()

        rows = []
        for r in transcripts:
            rows.append({
                "call_id": r.id,
                "caller_number": r.caller_number or "",
                "transcript": r.transcript_text or "",
                "confidence": r.confidence_score or 0,
                "language": r.language or "",
                "date": str(r.created_at) if r.created_at else "",
            })
        return {"columns": [
            "call_id", "caller_number", "transcript", "confidence", "language", "date",
        ], "rows": rows}

    def _entity_data(self, dfrom: datetime, dto: datetime) -> dict[str, Any]:
        entities = self.db.query(
            ExtractedEntity.call_session_id, ExtractedEntity.entity_type,
            ExtractedEntity.entity_value, ExtractedEntity.confidence_score,
            ExtractedEntity.created_at,
        ).filter(ExtractedEntity.created_at.between(dfrom, dto)).all()

        rows = []
        for r in entities:
            rows.append({
                "call_id": r.call_session_id,
                "entity_type": r.entity_type,
                "entity_value": r.entity_value,
                "confidence": r.confidence_score,
                "date": str(r.created_at) if r.created_at else "",
            })
        return {"columns": [
            "call_id", "entity_type", "entity_value", "confidence", "date",
        ], "rows": rows}

    def _classification_data(self, dfrom: datetime, dto: datetime) -> dict[str, Any]:
        classifications = self.db.query(
            CallClassification.call_session_id, CallClassification.category,
            CallClassification.subcategory, CallClassification.confidence_score,
            CallClassification.created_at,
        ).filter(CallClassification.created_at.between(dfrom, dto)).all()

        rows = []
        for r in classifications:
            rows.append({
                "call_id": r.call_session_id,
                "category": r.category,
                "subcategory": r.subcategory or "",
                "confidence": r.confidence_score,
                "date": str(r.created_at) if r.created_at else "",
            })
        return {"columns": [
            "call_id", "category", "subcategory", "confidence", "date",
        ], "rows": rows}

    def _recording_data(self, dfrom: datetime, dto: datetime) -> dict[str, Any]:
        recordings = self.db.query(
            Recording.id, Recording.call_session_id, Recording.filename,
            Recording.file_size, Recording.duration_seconds, Recording.recording_status,
            Recording.created_at,
        ).filter(Recording.created_at.between(dfrom, dto)).all()

        rows = []
        for r in recordings:
            rows.append({
                "recording_id": r.id,
                "call_id": r.call_session_id,
                "filename": r.filename or "",
                "file_size_bytes": r.file_size or 0,
                "duration_seconds": r.duration_seconds or 0,
                "status": r.recording_status or "",
                "date": str(r.created_at) if r.created_at else "",
            })
        return {"columns": [
            "recording_id", "call_id", "filename", "file_size_bytes",
            "duration_seconds", "status", "date",
        ], "rows": rows}

    def _analytics_data(self, dfrom: datetime, dto: datetime) -> dict[str, Any]:
        total = self.db.query(CallSession).filter(
            CallSession.created_at.between(dfrom, dto)
        ).count()
        answered = self.db.query(CallSession).filter(
            CallSession.created_at.between(dfrom, dto),
            CallSession.call_status == "ended",
        ).count()
        missed = self.db.query(CallSession).filter(
            CallSession.created_at.between(dfrom, dto),
            CallSession.call_status.in_(["missed", "failed"]),
        ).count()
        return {"columns": ["metric", "value"], "rows": [
            {"metric": "total_calls", "value": total},
            {"metric": "answered_calls", "value": answered},
            {"metric": "missed_calls", "value": missed},
        ]}

    def _write_csv(self, filepath: Path, data: dict[str, Any]) -> None:
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(data.get("columns", []))
            for row in data.get("rows", []):
                writer.writerow([row.get(col, "") for col in data.get("columns", [])])

    def _write_excel(self, filepath: Path, data: dict[str, Any]) -> None:
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(data.get("columns", []))
            for row in data.get("rows", []):
                ws.append([row.get(col, "") for col in data.get("columns", [])])
            wb.save(str(filepath))
        except ImportError:
            self._write_csv(filepath.with_suffix(".csv"), data)

    def _parse_date(self, date_str: str) -> datetime:
        from dateutil import parser
        return parser.parse(date_str).replace(tzinfo=timezone.utc)

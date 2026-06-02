from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.call_classification_model import CallClassification
from app.db.models.call_session import CallSession
from app.db.models.call_summary import CallSummary
from app.db.models.device import Device
from app.db.models.recording import Recording
from app.db.models.transcript import Transcript

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_dashboard(self, days: int = 30) -> dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        base = self.db.query(CallSession).filter(CallSession.created_at >= cutoff)

        total = base.count()
        answered = base.filter(CallSession.call_status == "ended").count()
        missed = base.filter(CallSession.call_status.in_(["missed", "failed"])).count()
        avg_duration = base.with_entities(func.avg(CallSession.duration)).scalar() or 0

        recordings = self.db.query(Recording).filter(Recording.created_at >= cutoff)
        recording_total = recordings.count()
        recording_success = recordings.filter(Recording.recording_status == "completed").count()

        transcripts = self.db.query(Transcript).filter(Transcript.created_at >= cutoff)
        transcript_total = transcripts.count()
        transcript_success = transcripts.filter(Transcript.confidence_score.isnot(None)).count()

        callbacks = self.db.query(CallSummary).filter(
            CallSummary.created_at >= cutoff,
            CallSummary.callback_required.in_(["yes", "recommended"]),
        ).count()

        return {
            "metrics": {
                "total_calls": total,
                "answered_calls": answered,
                "missed_calls": missed,
                "average_duration": round(float(avg_duration or 0), 2),
                "recording_success_rate": round(recording_success / recording_total * 100, 1) if recording_total else 0,
                "transcription_success_rate": round(transcript_success / transcript_total * 100, 1) if transcript_total else 0,
                "callback_rate": round(callbacks / total * 100, 1) if total else 0,
            },
            "urgency_distribution": self._urgency_distribution(cutoff),
            "sentiment_distribution": self._sentiment_distribution(cutoff),
            "category_distribution": self._category_distribution(cutoff),
            "daily_trends": self._daily_trends(cutoff),
            "weekly_trends": self._weekly_trends(cutoff),
            "monthly_trends": self._monthly_trends(cutoff),
            "peak_hours": self._peak_hours(cutoff),
            "top_devices": self._top_devices(cutoff),
        }

    def _urgency_distribution(self, cutoff: datetime) -> dict[str, int]:
        dist = {"low": 0, "medium": 0, "high": 0, "critical": 0, "unknown": 0}
        results = self.db.query(
            CallSummary.urgency_level, func.count(CallSummary.id)
        ).filter(CallSummary.created_at >= cutoff).group_by(CallSummary.urgency_level).all()
        for level, count in results:
            dist[level] = count
        return dist

    def _sentiment_distribution(self, cutoff: datetime) -> dict[str, int]:
        dist = {"positive": 0, "neutral": 0, "negative": 0, "mixed": 0, "unknown": 0}
        results = self.db.query(
            CallSummary.sentiment, func.count(CallSummary.id)
        ).filter(CallSummary.created_at >= cutoff).group_by(CallSummary.sentiment).all()
        for sentiment, count in results:
            dist[sentiment] = count
        return dist

    def _category_distribution(self, cutoff: datetime) -> dict[str, int]:
        dist = {cat: 0 for cat in [
            "sales_inquiry", "support", "complaint", "quotation",
            "partnership", "vendor", "recruitment", "personal", "spam", "unknown",
        ]}
        results = self.db.query(
            CallClassification.category, func.count(CallClassification.id)
        ).filter(CallClassification.created_at >= cutoff).group_by(CallClassification.category).all()
        for cat, count in results:
            dist[cat] = count
        return dist

    def _daily_trends(self, cutoff: datetime) -> list[dict[str, Any]]:
        results = []
        for i in range(30):
            day = cutoff + timedelta(days=i)
            next_day = day + timedelta(days=1)
            calls = self.db.query(CallSession).filter(
                CallSession.created_at >= day,
                CallSession.created_at < next_day,
            )
            total = calls.count()
            answered = calls.filter(CallSession.call_status == "ended").count()
            missed = calls.filter(CallSession.call_status.in_(["missed", "failed"])).count()
            if total > 0:
                results.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "total_calls": total,
                    "answered_calls": answered,
                    "missed_calls": missed,
                })
        return results

    def _weekly_trends(self, cutoff: datetime) -> list[dict[str, Any]]:
        results = []
        for i in range(0, 30, 7):
            week_start = cutoff + timedelta(days=i)
            week_end = week_start + timedelta(days=7)
            calls = self.db.query(CallSession).filter(
                CallSession.created_at >= week_start,
                CallSession.created_at < week_end,
            )
            total = calls.count()
            avg_dur = calls.with_entities(func.avg(CallSession.duration)).scalar() or 0
            if total > 0:
                results.append({
                    "week": week_start.strftime("%Y-W%V"),
                    "total_calls": total,
                    "average_duration": round(float(avg_dur), 2),
                })
        return results

    def _monthly_trends(self, cutoff: datetime) -> list[dict[str, Any]]:
        results = []
        for i in range(0, 30, 30):
            month_start = cutoff + timedelta(days=i)
            month_end = month_start + timedelta(days=30)
            calls = self.db.query(CallSession).filter(
                CallSession.created_at >= month_start,
                CallSession.created_at < month_end,
            )
            total = calls.count()
            top_cat = "N/A"
            if total:
                cat_result = self.db.query(
                    CallClassification.category, func.count(CallClassification.id).label("cnt")
                ).filter(
                    CallClassification.created_at >= month_start,
                    CallClassification.created_at < month_end,
                ).group_by(CallClassification.category).order_by(func.count(CallClassification.id).desc()).first()
                top_cat = cat_result[0] if cat_result else "N/A"
            if total > 0:
                results.append({
                    "month": month_start.strftime("%Y-%m"),
                    "total_calls": total,
                    "top_category": top_cat,
                })
        return results

    def _peak_hours(self, cutoff: datetime) -> dict[str, int]:
        hours = {str(h).zfill(2): 0 for h in range(24)}
        results = self.db.query(
            func.extract("hour", CallSession.created_at).label("hour"),
            func.count(CallSession.id),
        ).filter(CallSession.created_at >= cutoff).group_by("hour").all()
        for hour, count in results:
            hours[str(int(hour)).zfill(2)] = count
        return hours

    def _top_devices(self, cutoff: datetime) -> list[dict[str, Any]]:
        results = self.db.query(
            Device.id, Device.model, func.count(CallSession.id).label("cnt")
        ).join(CallSession, CallSession.device_id == Device.id
        ).filter(CallSession.created_at >= cutoff
        ).group_by(Device.id, Device.model
        ).order_by(func.count(CallSession.id).desc()).limit(10).all()
        return [{"device_id": r.id, "model": r.model, "calls": r.cnt} for r in results]

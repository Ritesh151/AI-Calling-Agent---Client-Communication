from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.call_classification_model import CallClassification
from app.db.models.call_session import CallSession
from app.db.models.call_summary import CallSummary
from app.services.event_bus import event_bus
from app.services.event_bus import Event, EventPriority

logger = logging.getLogger(__name__)


class InsightService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_insights(self) -> list[dict[str, Any]]:
        insights = []
        insights.extend(self._category_trend_insights())
        insights.extend(self._urgency_peak_insights())
        insights.extend(self._sentiment_shift_insights())
        insights.extend(self._callback_overdue_insights())
        insights.extend(self._volume_trend_insights())
        insights.extend(self._entity_based_insights())
        for insight in insights:
            event_bus.publish_nowait(Event(
                type="insight_generated",
                data=insight,
                priority=EventPriority.NORMAL,
            ))

        return insights

    def _category_trend_insights(self) -> list[dict[str, Any]]:
        insights = []
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        current = self.db.query(
            CallClassification.category, func.count(CallClassification.id)
        ).filter(CallClassification.created_at >= week_ago
        ).group_by(CallClassification.category).all()
        previous = self.db.query(
            CallClassification.category, func.count(CallClassification.id)
        ).filter(
            CallClassification.created_at >= two_weeks_ago,
            CallClassification.created_at < week_ago,
        ).group_by(CallClassification.category).all()

        prev_counts = {cat: cnt for cat, cnt in previous}
        for cat, cur_cnt in current:
            prev_cnt = prev_counts.get(cat, 0)
            if prev_cnt > 0:
                change = ((cur_cnt - prev_cnt) / prev_cnt) * 100
                if abs(change) >= 20:
                    direction = "increased" if change > 0 else "decreased"
                    insights.append({
                        "insight_type": "category_trend",
                        "content": f"'{cat.replace('_', ' ').title()}' calls {direction} by {abs(round(change))}% this week.",
                        "metric_value": round(change, 1),
                        "category": cat,
                    })
        return insights

    def _urgency_peak_insights(self) -> list[dict[str, Any]]:
        insights = []
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        urgent = self.db.query(CallSummary).filter(
            CallSummary.created_at >= week_ago,
            CallSummary.urgency_level.in_(["high", "critical"]),
        ).all()

        if urgent:
            hours = Counter()
            for s in urgent:
                if s.created_at:
                    hours[s.created_at.hour] += 1
            if hours:
                peak_hour = hours.most_common(1)[0]
                period = "AM" if peak_hour[0] < 12 else "PM"
                hour_12 = peak_hour[0] if peak_hour[0] <= 12 else peak_hour[0] - 12
                insights.append({
                    "insight_type": "urgency_peak",
                    "content": f"Most urgent calls occurred between {hour_12}{period} this week.",
                    "metric_value": float(peak_hour[0]),
                })
        return insights

    def _sentiment_shift_insights(self) -> list[dict[str, Any]]:
        insights = []
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        current_neg = self.db.query(CallSummary).filter(
            CallSummary.created_at >= week_ago,
            CallSummary.sentiment == "negative",
        ).count()
        prev_neg = self.db.query(CallSummary).filter(
            CallSummary.created_at >= two_weeks_ago,
            CallSummary.created_at < week_ago,
            CallSummary.sentiment == "negative",
        ).count()

        if prev_neg > 0:
            change = ((current_neg - prev_neg) / prev_neg) * 100
            if abs(change) >= 15:
                direction = "increased" if change > 0 else "decreased"
                insights.append({
                    "insight_type": "sentiment_shift",
                    "content": f"Negative sentiment calls {direction} by {abs(round(change))}% compared to previous week.",
                    "metric_value": round(change, 1),
                })
        return insights

    def _callback_overdue_insights(self) -> list[dict[str, Any]]:
        insights = []
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        pending_callbacks = self.db.query(CallSummary).filter(
            CallSummary.created_at >= week_ago,
            CallSummary.callback_required == "yes",
        ).count()

        if pending_callbacks > 0:
            insights.append({
                "insight_type": "callback_overdue",
                "content": f"Callbacks are overdue for {pending_callbacks} conversation{'s' if pending_callbacks > 1 else ''}.",
                "metric_value": float(pending_callbacks),
            })
        return insights

    def _volume_trend_insights(self) -> list[dict[str, Any]]:
        insights = []
        now = datetime.now(timezone.utc)
        today = now - timedelta(days=1)
        yesterday = now - timedelta(days=2)

        today_count = self.db.query(CallSession).filter(
            CallSession.created_at >= today
        ).count()
        yesterday_count = self.db.query(CallSession).filter(
            CallSession.created_at >= yesterday,
            CallSession.created_at < today,
        ).count()

        if yesterday_count > 0:
            change = ((today_count - yesterday_count) / yesterday_count) * 100
            if abs(change) >= 10:
                direction = "increased" if change > 0 else "decreased"
                insights.append({
                    "insight_type": "volume_trend",
                    "content": f"Call volume {direction} by {abs(round(change))}% compared to yesterday.",
                    "metric_value": round(change, 1),
                })
        return insights

    def _entity_based_insights(self) -> list[dict[str, Any]]:
        insights = []
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        from app.db.models.extracted_entity import ExtractedEntity
        top_products = self.db.query(
            ExtractedEntity.entity_value, func.count(ExtractedEntity.id).label("cnt")
        ).filter(
            ExtractedEntity.created_at >= week_ago,
            ExtractedEntity.entity_type.in_(["product_name", "service_name"]),
        ).group_by(ExtractedEntity.entity_value
        ).order_by(func.count(ExtractedEntity.id).desc()).limit(3).all()

        if top_products:
            products_str = ", ".join(f"'{p[0]}'" for p in top_products)
            insights.append({
                "insight_type": "top_mentions",
                "content": f"Most mentioned products/services this week: {products_str}.",
                "metric_value": float(top_products[0][1]),
            })
        return insights

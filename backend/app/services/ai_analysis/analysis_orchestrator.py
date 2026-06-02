from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.ai_processing_job_model import AIProcessingJob
from app.db.models.call_classification_model import CallClassification
from app.db.models.call_summary import CallSummary
from app.db.models.extracted_entity import ExtractedEntity
from app.repositories.ai_processing_job_repository import AIProcessingJobRepository
from app.repositories.call_classification_repository import CallClassificationRepository
from app.repositories.call_summary_repository import CallSummaryRepository
from app.repositories.extracted_entity_repository import ExtractedEntityRepository
from app.services.ai_analysis.callback.callback_service import CallbackService
from app.services.ai_analysis.classification.classification_service import (
    ClassificationService,
)
from app.services.ai_analysis.entity_extraction.entity_extraction_service import (
    EntityExtractionService,
)
from app.services.ai_analysis.sentiment.sentiment_service import SentimentService
from app.services.ai_analysis.summarization.summarization_service import (
    SummarizationService,
)
from app.services.ai_analysis.urgency.urgency_service import UrgencyService
from app.services.event_bus import event_bus
from app.services.event_bus import Event, EventPriority

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.summarization = SummarizationService()
        self.entity_extraction = EntityExtractionService()
        self.classification = ClassificationService()
        self.sentiment = SentimentService()
        self.urgency = UrgencyService()
        self.callback = CallbackService()

    def analyze_call(self, call_session_id: int, transcript_text: str) -> dict[str, Any]:
        results: dict[str, Any] = {}
        job_repo = AIProcessingJobRepository(self.db)
        job = job_repo.create(
            call_session_id=call_session_id,
            job_type="full_analysis",
            status="processing",
            started_at=datetime.now(timezone.utc),
        )

        try:
            summary_result = self.summarization.generate_summary(transcript_text)
            results["summary"] = summary_result
            self._save_summary(call_session_id, summary_result)
            event_bus.publish_nowait(Event(
                type="summary_generated",
                data={"call_session_id": call_session_id},
                priority=EventPriority.NORMAL,
            ))

            entities = self.entity_extraction.extract_entities(transcript_text)
            results["entities"] = entities
            self._save_entities(call_session_id, entities)

            classification_result = self.classification.classify(transcript_text)
            results["classification"] = classification_result
            self._save_classification(call_session_id, classification_result)
            event_bus.publish_nowait(Event(
                type="classification_completed",
                data={"call_session_id": call_session_id, "category": classification_result.get("primary_category")},
                priority=EventPriority.NORMAL,
            ))

            sentiment_result = self.sentiment.analyze_sentiment(transcript_text)
            results["sentiment"] = sentiment_result
            self._update_summary_sentiment(call_session_id, sentiment_result)
            event_bus.publish_nowait(Event(
                type="sentiment_completed",
                data={"call_session_id": call_session_id, "sentiment": sentiment_result.get("sentiment")},
                priority=EventPriority.NORMAL,
            ))

            urgency_result = self.urgency.detect_urgency(transcript_text)
            results["urgency"] = urgency_result
            self._update_summary_urgency(call_session_id, urgency_result)
            event_bus.publish_nowait(Event(
                type="urgency_detected",
                data={"call_session_id": call_session_id, "urgency": urgency_result.get("urgency")},
                priority=EventPriority.NORMAL,
            ))

            callback_result = self.callback.detect_callback(transcript_text)
            results["callback"] = callback_result
            self._update_summary_callback(call_session_id, callback_result)
            event_bus.publish_nowait(Event(
                type="callback_detected",
                data={"call_session_id": call_session_id, "callback_required": callback_result.get("callback_required")},
                priority=EventPriority.NORMAL,
            ))

            job_repo.mark_completed(job.id)
            logger.info("Full analysis completed for call %d", call_session_id)

        except Exception as e:
            job_repo.mark_failed(job.id, str(e))
            logger.error("Analysis failed for call %d: %s", call_session_id, e)

        return results

    def _save_summary(self, call_session_id: int, data: dict) -> None:
        repo = CallSummaryRepository(self.db)
        existing = repo.get_by_session(call_session_id)
        action_items_str = json.dumps(data.get("action_items", []))
        if existing:
            existing.summary = data.get("summary")
            existing.short_summary = data.get("short_summary")
            existing.action_items = action_items_str
            existing.callback_required = data.get("callback_required", "unknown")
            existing.urgency_level = data.get("urgency_level", "unknown")
            existing.sentiment = data.get("sentiment", "unknown")
            existing.generated_at = datetime.now(timezone.utc)
        else:
            self.db.add(CallSummary(
                call_session_id=call_session_id,
                summary=data.get("summary"),
                short_summary=data.get("short_summary"),
                action_items=action_items_str,
                callback_required=data.get("callback_required", "unknown"),
                urgency_level=data.get("urgency_level", "unknown"),
                sentiment=data.get("sentiment", "unknown"),
                generated_at=datetime.now(timezone.utc),
            ))
        self.db.commit()

    def _save_entities(self, call_session_id: int, entities: list[dict]) -> None:
        for entity in entities:
            self.db.add(ExtractedEntity(
                call_session_id=call_session_id,
                entity_type=entity.get("entity_type", "unknown"),
                entity_value=entity.get("entity_value", ""),
                confidence_score=entity.get("confidence_score", 0.0),
            ))
        self.db.commit()

    def _save_classification(self, call_session_id: int, data: dict) -> None:
        repo = CallClassificationRepository(self.db)
        repo.create(
            call_session_id=call_session_id,
            category=data.get("primary_category", "unknown"),
            confidence_score=data.get("primary_confidence", 0.0),
        )
        for sec in data.get("secondary_categories", []):
            self.db.add(CallClassification(
                call_session_id=call_session_id,
                category=sec.get("category", "unknown"),
                subcategory="secondary",
                confidence_score=sec.get("confidence", 0.0),
            ))
        self.db.commit()

    def _update_summary_sentiment(self, call_session_id: int, data: dict) -> None:
        repo = CallSummaryRepository(self.db)
        summary = repo.get_by_session(call_session_id)
        if summary:
            summary.sentiment = data.get("sentiment", "unknown")
            summary.sentiment_confidence = data.get("confidence")
            summary.sentiment_reasoning = data.get("reasoning")
            self.db.commit()

    def _update_summary_urgency(self, call_session_id: int, data: dict) -> None:
        repo = CallSummaryRepository(self.db)
        summary = repo.get_by_session(call_session_id)
        if summary:
            summary.urgency_level = data.get("urgency", "unknown")
            self.db.commit()

    def _update_summary_callback(self, call_session_id: int, data: dict) -> None:
        repo = CallSummaryRepository(self.db)
        summary = repo.get_by_session(call_session_id)
        if summary:
            summary.callback_required = data.get("callback_required", "unknown")
            self.db.commit()

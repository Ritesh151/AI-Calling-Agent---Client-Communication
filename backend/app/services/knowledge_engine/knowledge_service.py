from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.call_classification_model import CallClassification
from app.db.models.call_session import CallSession
from app.db.models.call_summary import CallSummary
from app.db.models.extracted_entity import ExtractedEntity
from app.db.models.transcript import Transcript
from app.repositories.call_classification_repository import CallClassificationRepository
from app.repositories.extracted_entity_repository import ExtractedEntityRepository
from app.repositories.transcript_repository import TranscriptRepository

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.entity_repo = ExtractedEntityRepository(db)
        self.classification_repo = CallClassificationRepository(db)
        self.transcript_repo = TranscriptRepository(db)

    def get_call_knowledge(self, call_session_id: int) -> dict[str, Any]:
        from app.db.models.recording import Recording
        recording = self.db.query(Recording).filter(
            Recording.call_session_id == call_session_id
        ).first()
        transcript = self.transcript_repo.get_by_recording(recording.id) if recording else None
        entities = self.entity_repo.get_by_session(call_session_id)
        classifications = self.classification_repo.get_by_session(call_session_id)
        summary = self.db.query(CallSummary).filter(
            CallSummary.call_session_id == call_session_id
        ).first()
        session = self.db.query(CallSession).filter(
            CallSession.id == call_session_id
        ).first()

        return {
            "call_session_id": call_session_id,
            "caller": {
                "number": session.caller_number if session else None,
                "name": session.caller_name if session else None,
            } if session else None,
            "transcript": transcript.transcript_text if transcript else None,
            "summary": {
                "text": summary.summary,
                "short": summary.short_summary,
                "action_items": summary.action_items,
                "urgency": summary.urgency_level,
                "sentiment": summary.sentiment,
                "callback_required": summary.callback_required,
            } if summary else None,
            "entities": [
                {"type": e.entity_type, "value": e.entity_value, "confidence": e.confidence_score}
                for e in entities
            ],
            "classifications": [
                {"category": c.category, "confidence": c.confidence_score}
                for c in classifications
            ],
        }

    def search_knowledge(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        results = []
        entities = self.entity_repo.get_by_value(query)
        seen_sessions = set()
        for entity in entities:
            if entity.call_session_id not in seen_sessions:
                seen_sessions.add(entity.call_session_id)
                knowledge = self.get_call_knowledge(entity.call_session_id)
                knowledge["match_type"] = "entity"
                knowledge["match_value"] = entity.entity_value
                results.append(knowledge)
        if len(results) >= limit:
            return results[:limit]

        summaries = self.db.query(CallSummary).filter(
            CallSummary.short_summary.ilike(f"%{query}%")
        ).limit(limit - len(results)).all()
        for s in summaries:
            if s.call_session_id not in seen_sessions:
                seen_sessions.add(s.call_session_id)
                knowledge = self.get_call_knowledge(s.call_session_id)
                knowledge["match_type"] = "summary"
                results.append(knowledge)

        return results[:limit]

    def get_topic_discovery(self) -> list[dict[str, Any]]:
        categories = self.classification_repo.get_distinct_categories()
        topics = []
        for cat in categories:
            count = self.classification_repo.get_by_category(cat).__len__()
            topics.append({"topic": cat, "count": count})
        return sorted(topics, key=lambda x: x["count"], reverse=True)

    def get_entity_types(self) -> list[dict[str, Any]]:
        types = self.entity_repo.get_distinct_types()
        result = []
        for t in types:
            entities = self.entity_repo.get_by_type(t)
            result.append({
                "entity_type": t,
                "count": len(entities),
                "examples": list(set(e.entity_value for e in entities[:5])),
            })
        return result

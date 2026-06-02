from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.call_classification_model import CallClassification
from app.db.models.call_session import CallSession
from app.db.models.call_summary import CallSummary
from app.db.models.transcript import Transcript
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.event_bus import event_bus
from app.services.event_bus import Event, EventPriority

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService(db)

    def search(self, query: str, search_type: str = "hybrid", limit: int | None = None,
               filters: dict | None = None) -> dict[str, Any]:
        start = time.monotonic()
        limit = limit or settings.SEARCH_DEFAULT_LIMIT
        if limit > settings.SEARCH_MAX_LIMIT:
            limit = settings.SEARCH_MAX_LIMIT

        results = []
        total = 0

        if search_type in ("keyword", "hybrid"):
            keyword_results = self._keyword_search(query, limit, filters)
            results.extend(keyword_results)
            total += len(keyword_results)

        if search_type in ("semantic", "hybrid"):
            semantic_results = self._semantic_search(query, limit, filters)
            if search_type == "semantic":
                results = semantic_results
            else:
                seen = {r["call_session_id"] for r in results}
                for r in semantic_results:
                    if r["call_session_id"] not in seen:
                        results.append(r)
                        seen.add(r["call_session_id"])
                results = results[:limit]

        took_ms = (time.monotonic() - start) * 1000

        return {
            "results": results,
            "total": len(results),
            "query": query,
            "search_type": search_type,
            "took_ms": round(took_ms, 2),
        }

    def _keyword_search(self, query: str, limit: int, filters: dict | None = None) -> list[dict]:
        from app.db.models.recording import Recording
        search_term = f"%{query}%"
        q = self.db.query(
            CallSession.id.label("call_session_id"),
            Transcript.transcript_text,
            CallSummary.short_summary,
            CallSummary.summary,
            CallSummary.urgency_level,
            CallSummary.sentiment,
            CallSummary.callback_required,
            CallSession.caller_number,
            CallSession.caller_name,
            CallSession.duration,
            CallSession.created_at,
        ).join(Recording, Recording.call_session_id == CallSession.id
        ).outerjoin(Transcript, Transcript.recording_id == Recording.id
        ).outerjoin(CallSummary, CallSummary.call_session_id == CallSession.id)

        conditions = [
            Transcript.transcript_text.ilike(search_term),
            CallSummary.short_summary.ilike(search_term),
            CallSummary.summary.ilike(search_term),
        ]
        if filters:
            if filters.get("category"):
                q = q.outerjoin(CallClassification, CallClassification.call_session_id == CallSession.id)
                conditions.append(CallClassification.category == filters["category"])
            if filters.get("sentiment"):
                conditions.append(CallSummary.sentiment == filters["sentiment"])
            if filters.get("urgency"):
                conditions.append(CallSummary.urgency_level == filters["urgency"])
            if filters.get("callback_required"):
                conditions.append(CallSummary.callback_required == filters["callback_required"])
            if filters.get("phone_number"):
                conditions.append(CallSession.caller_number.ilike(f"%{filters['phone_number']}%"))
            if filters.get("caller_name"):
                conditions.append(CallSession.caller_name.ilike(f"%{filters['caller_name']}%"))

        q = q.filter(or_(*conditions)).limit(limit)
        results = []
        for row in q.all():
            results.append({
                "call_session_id": row.call_session_id,
                "transcript_text": row.transcript_text,
                "short_summary": row.short_summary,
                "summary": row.summary,
                "urgency": row.urgency_level,
                "sentiment": row.sentiment,
                "callback_required": row.callback_required,
                "caller_number": row.caller_number,
                "caller_name": row.caller_name,
                "duration": row.duration,
                "created_at": str(row.created_at) if row.created_at else None,
                "score": 0.5,
            })
        return results

    def _semantic_search(self, query: str, limit: int, filters: dict | None = None) -> list[dict]:
        try:
            vector_filters = {}
            if filters:
                for key in ("category", "sentiment", "urgency", "callback_required"):
                    if filters.get(key):
                        vector_filters[key] = filters[key]
            vresults = self.embedding_service.search(query, limit=limit, filters=vector_filters)
            session_ids = [r.get("call_session_id") for r in vresults if r.get("call_session_id")]
            if not session_ids:
                return []
            sessions = self.db.query(CallSession).filter(CallSession.id.in_(session_ids)).all()
            session_map = {s.id: s for s in sessions}
            output = []
            for vr in vresults:
                csid = vr.get("call_session_id")
                s = session_map.get(csid)
                if s:
                    output.append({
                        "call_session_id": csid,
                        "transcript_text": vr.get("chunk_text", ""),
                        "short_summary": None,
                        "summary": None,
                        "urgency": None,
                        "sentiment": None,
                        "callback_required": None,
                        "caller_number": s.caller_number,
                        "caller_name": s.caller_name,
                        "duration": s.duration,
                        "created_at": str(s.created_at) if s.created_at else None,
                        "score": vr.get("score", 0),
                    })
            return output
        except Exception as e:
            logger.error("Semantic search failed: %s", e)
            return []

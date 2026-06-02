from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.models.call_session import CallSession
from app.repositories.call_session_repository import CallSessionRepository
from app.repositories.device_repository import DeviceRepository
from app.services.adb_watcher import adb_engine
from app.services.call_conversation import ConversationOrchestrator
from app.services.call_detector.auto_answer import AutoAnswerService
from app.services.event_bus import event_bus
from app.services.event_bus.event_types import (
    IncomingCallEvent,
    CallAnsweredEvent,
    CallEndedEvent,
    CallMissedEvent,
)

logger = logging.getLogger(__name__)


class CallLifecycleWorker:
    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None
        self._active_sessions: dict[str, int] = {}
        self._conversation = ConversationOrchestrator()
        self._conversation_started: set[int] = set()

    async def start(self) -> None:
        self._running = True
        event_bus.subscribe("incoming_call", self._on_incoming_call)
        event_bus.subscribe("call_answered", self._on_call_answered)
        event_bus.subscribe("call_missed", self._on_call_missed)
        event_bus.subscribe("call_ended", self._on_call_ended)
        logger.info("Call lifecycle worker started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Call lifecycle worker stopped")

    async def _on_incoming_call(self, event: IncomingCallEvent) -> None:
        db = SessionLocal()
        try:
            device_repo = DeviceRepository(db)
            session_repo = CallSessionRepository(db)

            device = device_repo.get_by_serial(event.data.get("serial", ""))
            if not device:
                logger.warning("Device not found for serial: %s", event.data.get("serial"))
                return

            serial = event.data.get("serial", "")
            caller_info = event.data.get("caller_info", {})

            session = session_repo.create(
                device_id=device.id,
                caller_name=caller_info.get("name", "Unknown"),
                caller_number=caller_info.get("number", ""),
                call_status="ringing",
                start_time=datetime.now(UTC),
                incoming_detected_at=datetime.now(UTC),
                caller_type=caller_info.get("type", "unknown"),
                raw_call_data=event.data.get("raw_data", ""),
            )

            self._active_sessions[serial] = session.id
            logger.info(
                "Call session created: %d for device %s",
                session.id,
                serial,
            )

            asyncio.create_task(self._trigger_auto_answer(serial, device.id, event))
        except Exception as e:
            logger.error("Error handling incoming call: %s", e)
            db.rollback()
        finally:
            db.close()

    async def _trigger_auto_answer(self, serial: str, device_id: int, event: IncomingCallEvent) -> None:
        try:
            answer_service = AutoAnswerService(adb_engine, event_bus)
            call_data = {
                "device_id": device_id,
                "serial": serial,
                "call_session_id": self._active_sessions.get(serial),
                "caller_info": {
                    "number": event.caller_number,
                    "name": event.caller_name,
                    "type": event.caller_type,
                },
            }
            result = await answer_service.attempt_answer(serial, call_data)
            if result["success"]:
                logger.info("Auto-answer succeeded for %s", serial)
                session_id = self._active_sessions.get(serial)
                if session_id:
                    db = SessionLocal()
                    try:
                        CallSessionRepository(db).update(
                            session_id,
                            call_status="active",
                            answered_at=datetime.now(UTC),
                        )
                    finally:
                        db.close()
                if session_id and session_id not in self._conversation_started:
                    self._conversation_started.add(session_id)
                    await self._conversation.on_call_active(
                        call_session_id=session_id,
                        device_id=device_id,
                        serial=serial,
                        caller_number=event.caller_number,
                        auto_answered=True,
                    )
            else:
                logger.warning("Auto-answer failed for %s: %s", serial, result.get("error"))
        except Exception as e:
            logger.error("Auto-answer error for %s: %s", serial, e)

    async def _on_call_answered(self, event: CallAnsweredEvent) -> None:
        serial = event.data.get("serial", "") if event.data else ""
        db = SessionLocal()
        try:
            session_repo = CallSessionRepository(db)
            device_repo = DeviceRepository(db)
            session_id = self._get_session_id(serial)
            if session_id:
                session_repo.update(
                    session_id,
                    call_status="active",
                    answered_at=datetime.now(UTC),
                )
                if session_id not in self._conversation_started:
                    device = device_repo.get_by_serial(serial)
                    if device:
                        self._conversation_started.add(session_id)
                        await self._conversation.on_call_active(
                            call_session_id=session_id,
                            device_id=device.id,
                            serial=serial,
                            caller_number=event.caller_number or "",
                            auto_answered=bool(
                                event.data.get("auto_answered") if event.data else False
                            ),
                        )
        except Exception as e:
            logger.error("Error handling call answered: %s", e)
        finally:
            db.close()

    async def _on_call_missed(self, event: CallMissedEvent) -> None:
        serial = event.data.get("serial") if hasattr(event, "data") else ""
        db = SessionLocal()
        try:
            session_repo = CallSessionRepository(db)
            session_id = self._get_session_id(serial)
            if session_id:
                session_repo.update(
                    session_id,
                    call_status="missed",
                    end_time=datetime.now(UTC),
                )
            self._active_sessions.pop(serial, None)
        except Exception as e:
            logger.error("Error handling call missed: %s", e)
        finally:
            db.close()

    async def _on_call_ended(self, event: CallEndedEvent) -> None:
        serial = event.data.get("serial") if hasattr(event, "data") else ""
        db = SessionLocal()
        try:
            session_repo = CallSessionRepository(db)
            session_id = self._get_session_id(serial)
            if session_id:
                session = session_repo.get_by_id(session_id)
                if session and session.call_status in ("active", "ringing"):
                    duration = None
                    if session.start_time:
                        duration = (datetime.now(UTC) - session.start_time).total_seconds()
                    session_repo.update(
                        session_id,
                        call_status="ended",
                        end_time=datetime.now(UTC),
                        duration=duration,
                    )
            self._active_sessions.pop(serial, None)
        except Exception as e:
            logger.error("Error handling call ended: %s", e)
        finally:
            db.close()

    def _get_session_id(self, serial: str) -> int | None:
        return self._active_sessions.get(serial)

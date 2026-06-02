from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.device import Device
from app.db.models.device_capability import DeviceCapability
from app.repositories.device_capability_repository import DeviceCapabilityRepository
from app.services.compatibility.manufacturer_handlers.handler_registry import (
    HandlerRegistry,
)
from app.services.event_bus import event_bus
from app.services.event_bus import Event, EventPriority

logger = logging.getLogger(__name__)


class CapabilityDetectionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DeviceCapabilityRepository(db)

    async def detect_device_capabilities(self, device_id: int) -> DeviceCapability:
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")

        handler = HandlerRegistry.resolve_for_device(str(device_id), device.manufacturer or "")
        capabilities = await handler.detect_capabilities(str(device_id))

        score = self._compute_score(capabilities)

        existing = self.repo.get_by_device(device_id)
        if existing:
            existing.supports_auto_answer = capabilities.get("supports_auto_answer", False)
            existing.supports_call_detection = capabilities.get("supports_call_detection", False)
            existing.supports_audio_capture = capabilities.get("supports_audio_capture", False)
            existing.supports_speaker_recording = capabilities.get("supports_speaker_recording", False)
            existing.supports_mic_recording = capabilities.get("supports_mic_recording", False)
            existing.supports_tts_playback = capabilities.get("supports_tts_playback", False)
            existing.supports_background_execution = capabilities.get("supports_background_execution", False)
            existing.capability_score = score
            existing.tested_at = datetime.now(timezone.utc)
            result = existing
        else:
            result = DeviceCapability(
                device_id=device_id,
                manufacturer=device.manufacturer or "",
                model=device.model or "",
                android_version=device.android_version,
                supports_auto_answer=capabilities.get("supports_auto_answer", False),
                supports_call_detection=capabilities.get("supports_call_detection", False),
                supports_audio_capture=capabilities.get("supports_audio_capture", False),
                supports_speaker_recording=capabilities.get("supports_speaker_recording", False),
                supports_mic_recording=capabilities.get("supports_mic_recording", False),
                supports_tts_playback=capabilities.get("supports_tts_playback", False),
                supports_background_execution=capabilities.get("supports_background_execution", False),
                capability_score=score,
                tested_at=datetime.now(timezone.utc),
            )
            self.db.add(result)

        self.db.commit()
        self.db.refresh(result)

        await event_bus.publish(Event(
            type="capability_detected",
            data={"device_id": device_id, "score": score, "capabilities": capabilities},
            priority=EventPriority.NORMAL,
        ))

        logger.info("Capabilities detected for device %d: score=%.1f", device_id, score)
        return result

    def _compute_score(self, caps: dict[str, bool]) -> float:
        weights = {
            "supports_auto_answer": 20,
            "supports_call_detection": 20,
            "supports_audio_capture": 15,
            "supports_speaker_recording": 15,
            "supports_mic_recording": 10,
            "supports_tts_playback": 10,
            "supports_background_execution": 10,
        }
        score = 0.0
        for key, weight in weights.items():
            if caps.get(key, False):
                score += weight
        return score

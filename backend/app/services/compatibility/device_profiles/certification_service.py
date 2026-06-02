from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.device_capability import DeviceCapability
from app.repositories.device_capability_repository import DeviceCapabilityRepository

logger = logging.getLogger(__name__)


class CertificationLevel(str, Enum):
    CERTIFIED = "CERTIFIED"
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    LIMITED = "LIMITED"
    UNSUPPORTED = "UNSUPPORTED"


class CertificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DeviceCapabilityRepository(db)

    def certify_device(self, device_id: int) -> tuple[CertificationLevel, float]:
        capability = self.repo.get_by_device(device_id)
        if not capability:
            logger.warning("No capability record for device %d, cannot certify", device_id)
            return CertificationLevel.UNSUPPORTED, 0.0

        score = capability.capability_score
        level = self._level_from_score(capability)
        logger.info("Device %d certified as %s (score=%.1f)", device_id, level.value, score)

        capability.certification_level = level.value
        self.db.commit()

        return level, score

    def _level_from_score(self, capability: DeviceCapability) -> CertificationLevel:
        mandatory = ["supports_call_detection", "supports_auto_answer"]
        for m in mandatory:
            if not getattr(capability, m, False):
                break
        else:
            if capability.capability_score >= 90:
                return CertificationLevel.CERTIFIED
            if capability.capability_score >= 70:
                return CertificationLevel.SUPPORTED
            if capability.capability_score >= 50:
                return CertificationLevel.PARTIAL
            if capability.capability_score >= 30:
                return CertificationLevel.LIMITED
            return CertificationLevel.UNSUPPORTED

        if capability.supports_call_detection and capability.supports_audio_capture:
            if capability.capability_score >= 60:
                return CertificationLevel.SUPPORTED
            return CertificationLevel.PARTIAL

        if capability.supports_call_detection:
            return CertificationLevel.LIMITED

        return CertificationLevel.UNSUPPORTED

    def recertify_all(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        capabilities = self.repo.get_all(skip=skip, limit=limit)
        results = []
        for cap in capabilities:
            level, score = self.certify_device(cap.device_id)
            lv = level.value if hasattr(level, "value") else level
            results.append({"device_id": cap.device_id, "level": lv, "score": score})
        return results

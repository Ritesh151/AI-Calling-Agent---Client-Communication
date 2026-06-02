from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.device import Device
from app.db.models.device_profile_model import DeviceProfile
from app.repositories.device_profile_repository import DeviceProfileRepository

logger = logging.getLogger(__name__)


class DeviceProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DeviceProfileRepository(db)

    def get_or_create_profile(self, device_id: int) -> DeviceProfile:
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")

        manufacturer = (device.manufacturer or "unknown").lower()
        model = device.model or "unknown"

        profile = self.repo.get_by_manufacturer_model(manufacturer, model)
        if profile:
            return profile

        return self._generate_profile(manufacturer, model, device.android_version)

    def _generate_profile(self, manufacturer: str, model: str, android_version: str | None) -> DeviceProfile:
        known = self._get_known_features(manufacturer, model)
        profile = DeviceProfile(
            manufacturer=manufacturer,
            model=model,
            android_version=android_version,
            profile_name=f"{manufacturer.title()} {model}",
            supported_features=known.get("features", "generic"),
            known_limitations=known.get("limitations", "unknown"),
            recommended_strategy=known.get("strategy", "generic"),
            certification_level=known.get("certification", "UNSUPPORTED"),
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        logger.info("Generated profile for %s %s: %s", manufacturer, model, profile.certification_level)
        return profile

    def _get_known_features(self, manufacturer: str, model: str) -> dict[str, str]:
        m = manufacturer.lower()
        profiles = {
            "samsung": {"features": "call_detection,screenrecord", "limitations": "oneui_background_limits", "strategy": "hybrid", "certification": "SUPPORTED"},
            "google": {"features": "call_detection,screenrecord,media_recorder", "limitations": "none", "strategy": "hybrid", "certification": "CERTIFIED"},
            "oneplus": {"features": "call_detection,screenrecord", "limitations": "none", "strategy": "microphone", "certification": "SUPPORTED"},
            "xiaomi": {"features": "call_detection,screenrecord", "limitations": "miui_background_limits", "strategy": "microphone", "certification": "PARTIAL"},
            "motorola": {"features": "call_detection,screenrecord", "limitations": "none", "strategy": "microphone", "certification": "SUPPORTED"},
            "oppo": {"features": "call_detection", "limitations": "coloros_background_limits", "strategy": "microphone", "certification": "PARTIAL"},
            "vivo": {"features": "call_detection", "limitations": "funtouch_background_limits,auto_answer_issues", "strategy": "microphone", "certification": "LIMITED"},
            "realme": {"features": "call_detection", "limitations": "realmeui_background_limits", "strategy": "microphone", "certification": "PARTIAL"},
        }
        return profiles.get(m, {"features": "basic", "limitations": "unknown", "strategy": "generic", "certification": "UNSUPPORTED"})

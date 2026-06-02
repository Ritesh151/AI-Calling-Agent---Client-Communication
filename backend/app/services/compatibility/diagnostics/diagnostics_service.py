from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.device import Device
from app.db.models.device_capability import DeviceCapability
from app.repositories.device_capability_repository import DeviceCapabilityRepository
from app.repositories.recovery_log_repository import RecoveryLogRepository
from app.services.compatibility.adb_reliability.adb_reliability_service import (
    ADBReliabilityService,
)
from app.services.compatibility.device_profiles.certification_service import (
    CertificationService,
)

logger = logging.getLogger(__name__)


class DiagnosticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cap_repo = DeviceCapabilityRepository(db)
        self.recovery_repo = RecoveryLogRepository(db)
        self.reliability = ADBReliabilityService(db)
        self.certification = CertificationService(db)

    async def run_diagnostics(self, device_id: int) -> dict[str, Any]:
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")

        capability = self.cap_repo.get_by_device(device_id)
        recovery_logs = self.recovery_repo.get_by_device(device_id, limit=50)

        cert_level, cert_score = self.certification.certify_device(device_id)

        health = await self.reliability.check_device_health(str(device_id))
        stability = await self.reliability.check_stability(str(device_id))
        consecutive_failures = self.reliability.get_consecutive_failures(device_id)
        total_failures = self.reliability.get_failure_count(device_id)

        recovery_rate = self._compute_recovery_rate(recovery_logs) if recovery_logs is not None else 1.0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_failures = [
            r for r in recovery_logs
            if r.created_at and r.created_at.replace(tzinfo=timezone.utc) > cutoff
        ]

        recommendations = self._generate_recommendations(capability, health, recovery_rate, consecutive_failures)

        result = {
            "device_id": device_id,
            "device_name": f"{device.manufacturer} {device.model}" if device.manufacturer else "Unknown",
            "adb_health": health,
            "adb_stability": stability,
            "capability_score": capability.capability_score if capability else 0,
            "certification_level": cert_level.value if hasattr(cert_level, "value") else cert_level,
            "certification_score": cert_score,
            "consecutive_failures": consecutive_failures,
            "total_failures_recorded": total_failures,
            "failures_last_24h": len(recent_failures),
            "recovery_success_rate": round(recovery_rate * 100, 1),
            "recommendations": recommendations,
            "diagnosed_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "Diagnostics for device %d: cert=%s score=%.1f recovery=%.1f%% failures=%d",
            device_id, result["certification_level"], cert_score, recovery_rate * 100, total_failures,
        )
        return result

    def _compute_recovery_rate(self, logs: list) -> float:
        if not logs:
            return 1.0
        recovered = sum(1 for log in logs if log.status == "completed")
        return recovered / len(logs)

    def _generate_recommendations(
        self,
        capability: DeviceCapability | None,
        health: dict[str, Any],
        recovery_rate: float,
        consecutive_failures: int,
    ) -> list[str]:
        recs: list[str] = []

        if not capability:
            recs.append("Run capability detection to assess device compatibility")
            return recs

        if not health.get("healthy", False):
            recs.append("ADB connection is unstable. Verify USB cable and enable USB debugging")
            recs.append("Try a different USB port or cable")

        if capability.capability_score and capability.capability_score < 50:
            recs.append("Low capability score. Consider using a device with better Android call API support")

        if recovery_rate < 0.5:
            recs.append("Low recovery success rate. Manual intervention may be required for failures")

        if consecutive_failures > 5:
            recs.append(f"High consecutive failure count ({consecutive_failures}). Device may need reconnection")

        if not capability.supports_call_detection:
            recs.append("Call detection not supported on this device")
        if not capability.supports_auto_answer:
            recs.append("Auto answer not supported. Calls will not be answered automatically")
        if not capability.supports_audio_capture:
            recs.append("Audio capture not supported. Call recording will not function")

        return recs if recs else ["Device appears to be fully compatible"]

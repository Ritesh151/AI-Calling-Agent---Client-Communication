from __future__ import annotations

import asyncio
import json
import logging
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.recovery_log_model import RecoveryLog
from app.repositories.recovery_log_repository import RecoveryLogRepository
from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.event_bus import Event, EventPriority, event_bus

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    ADB_FREEZE = "adb_freeze"
    DEVICE_DISCONNECT = "device_disconnect"
    COMMAND_TIMEOUT = "command_timeout"
    SHELL_CRASH = "shell_crash"
    RECORDING_FAILURE = "recording_failure"
    AUTO_ANSWER_FAILURE = "auto_answer_failure"
    CALL_DETECTION_FAILURE = "call_detection_failure"


class ADBReliabilityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RecoveryLogRepository(db)
        self._failure_counts: dict[str, dict[str, int]] = {}
        self._consecutive_failures: dict[str, int] = {}
        self._stability_cache: dict[str, dict[str, Any]] = {}

    async def check_device_health(self, device_id: str) -> dict[str, Any]:
        check_cmds = [
            ("devices", f"devices | grep -w {device_id}"),
            ("shell_basic", "echo ok"),
            ("shell_props", "getprop ro.build.version.sdk"),
        ]
        results: dict[str, bool] = {}
        details: dict[str, str] = {}
        for name, cmd in check_cmds:
            try:
                res = await adb_engine.shell(device_id, cmd)
                if name == "devices":
                    results[name] = res.status == ADBCommandStatus.SUCCESS and device_id in res.stdout
                else:
                    results[name] = res.status == ADBCommandStatus.SUCCESS and bool(res.stdout.strip())
                details[name] = "ok" if results[name] else f"failed: {res.stderr[:100] if res.stderr else 'no output'}"
            except Exception as e:
                results[name] = False
                details[name] = f"exception: {e}"

        healthy = all(results.values())
        if not healthy:
            failures = [k for k, v in results.items() if not v]
            logger.warning("Device %s health check failed: %s", device_id, failures)
            await self._record_failure(
                device_id=int(device_id) if device_id.isdigit() else -1,
                failure_type=FailureType.ADB_FREEZE.value,
                error=f"health_check_failed:{','.join(failures)}",
            )

        return {"healthy": healthy, "checks": results, "details": details}

    async def check_stability(self, device_id: str, sample_count: int = 5) -> dict[str, Any]:
        if device_id in self._stability_cache:
            return self._stability_cache[device_id]

        success_count = 0
        latencies = []
        for _ in range(sample_count):
            start = asyncio.get_event_loop().time()
            try:
                res = await adb_engine.shell(device_id, "echo stability_check")
                elapsed = asyncio.get_event_loop().time() - start
                latencies.append(elapsed)
                if res.status == ADBCommandStatus.SUCCESS:
                    success_count += 1
            except Exception:
                latencies.append(999.0)

        avg_latency = sum(latencies) / len(latencies) if latencies else 999.0
        success_rate = success_count / sample_count if sample_count else 0

        result: dict[str, Any] = {
            "average_latency_ms": round(avg_latency * 1000, 2),
            "success_rate": round(success_rate, 2),
            "sample_count": sample_count,
            "stable": success_rate >= 0.8 and avg_latency < 5.0,
        }
        self._stability_cache[device_id] = result
        return result

    async def _record_failure(self, device_id: int, failure_type: str, error: str | None = None) -> None:
        str_id = str(device_id)
        if str_id not in self._failure_counts:
            self._failure_counts[str_id] = {}
        self._failure_counts[str_id][failure_type] = self._failure_counts[str_id].get(failure_type, 0) + 1

        self._consecutive_failures[str_id] = self._consecutive_failures.get(str_id, 0) + 1

        log = RecoveryLog(
            device_id=device_id,
            failure_type=failure_type,
            recovery_action="none",
            status="failed",
            error_message=error or "no details",
        )
        self.db.add(log)
        self.db.commit()

        await event_bus.publish(Event(
            type="adb_failure_detected",
            data={"device_id": device_id, "failure_type": failure_type, "consecutive": self._consecutive_failures[str_id]},
            priority=EventPriority.HIGH,
        ))

    async def report_recovery(self, device_id: int, action: str, success: bool) -> None:
        str_id = str(device_id)
        self._consecutive_failures[str_id] = 0
        self._stability_cache.pop(str_id, None)

        log = RecoveryLog(
            device_id=device_id,
            failure_type="manual_recovery",
            recovery_action=action,
            status="completed" if success else "failed",
            error_message=None if success else "recovery_action_failed",
        )
        self.db.add(log)
        self.db.commit()

    def get_failure_count(self, device_id: int, failure_type: str | None = None) -> int:
        str_id = str(device_id)
        if str_id not in self._failure_counts:
            return 0
        if failure_type:
            return self._failure_counts[str_id].get(failure_type, 0)
        return sum(self._failure_counts[str_id].values())

    def get_consecutive_failures(self, device_id: int) -> int:
        return self._consecutive_failures.get(str(device_id), 0)

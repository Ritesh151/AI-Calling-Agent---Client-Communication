from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.device import Device
from app.db.models.recovery_log_model import RecoveryLog
from app.repositories.recovery_log_repository import RecoveryLogRepository
from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.compatibility.adb_reliability.adb_reliability_service import (
    ADBReliabilityService,
)
from app.services.event_bus import Event, EventPriority, event_bus

logger = logging.getLogger(__name__)


class RecoveryAction:
    RESTART_ADB = "restart_adb"
    RECONNECT_DEVICE = "reconnect_device"
    RESTART_WORKER = "restart_worker"
    RESET_SESSION = "reset_session"
    RECOVER_RECORDING = "recover_recording"
    RECOVER_CALL = "recover_call"


class RecoveryEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RecoveryLogRepository(db)
        self.reliability = ADBReliabilityService(db)
        self._recovery_in_progress: set[str] = set()

    async def attempt_recovery(self, device_id: int, failure_type: str) -> dict[str, Any]:
        str_id = str(device_id)
        if str_id in self._recovery_in_progress:
            return {"success": False, "error": "recovery_already_in_progress", "action_taken": None}
        self._recovery_in_progress.add(str_id)
        try:
            return await self._execute_recovery(device_id, failure_type)
        finally:
            self._recovery_in_progress.discard(str_id)

    async def _execute_recovery(self, device_id: int, failure_type: str) -> dict[str, Any]:
        actions: list[str] = []
        recovered = False

        logger.info("Starting recovery for device %d (failure: %s)", device_id, failure_type)

        action = RecoveryAction.RECONNECT_DEVICE
        if failure_type in ("adb_freeze", "shell_crash"):
            action = RecoveryAction.RESTART_ADB
        elif failure_type == "device_disconnect":
            action = RecoveryAction.RECONNECT_DEVICE
        elif failure_type in ("recording_failure", "auto_answer_failure"):
            action = RecoveryAction.RECOVER_RECORDING
        elif failure_type == "call_detection_failure":
            action = RecoveryAction.RECOVER_CALL

        actions.append(action)
        result = await self._execute_action(action, str(device_id))
        recovered = result.get("success", False)

        if not recovered and action != RecoveryAction.RESTART_ADB:
            result = await self._execute_action(RecoveryAction.RESTART_ADB, str(device_id))
            actions.append(RecoveryAction.RESTART_ADB)
            recovered = result.get("success", False)

        if not recovered:
            result = await self._execute_action(RecoveryAction.RESET_SESSION, str(device_id))
            actions.append(RecoveryAction.RESET_SESSION)
            recovered = result.get("success", False)

        await self._log_recovery(device_id, failure_type, actions, recovered)

        await event_bus.publish(Event(
            type="recovery_completed" if recovered else "recovery_failed",
            data={"device_id": device_id, "failure_type": failure_type, "actions": actions, "recovered": recovered},
            priority=EventPriority.HIGH,
        ))

        return {"success": recovered, "actions_taken": actions, "recovered": recovered}

    async def _execute_action(self, action_type: str, device_id_str: str) -> dict[str, Any]:
        try:
            match action_type:
                case RecoveryAction.RESTART_ADB:
                    result = await adb_engine.raw_command("kill-server")
                    if result.status != ADBCommandStatus.SUCCESS:
                        return {"success": False, "error": "adb_kill_failed"}
                    await asyncio.sleep(2)
                    result = await adb_engine.raw_command("start-server")
                    if result.status != ADBCommandStatus.SUCCESS:
                        return {"success": False, "error": "adb_start_failed"}
                    await asyncio.sleep(1)
                    await event_bus.publish(Event(type="adb_restarted", data={}, priority=EventPriority.HIGH))
                    return {"success": True, "message": "adb_restarted"}

                case RecoveryAction.RECONNECT_DEVICE:
                    for cmd in ["usb", "connect 127.0.0.1", "wait-for-device"]:
                        await adb_engine.raw_command(cmd)
                        await asyncio.sleep(1)
                    return {"success": True, "message": "device_reconnected"}

                case RecoveryAction.RESTART_WORKER:
                    return {"success": True, "message": "worker_restart_scheduled"}

                case RecoveryAction.RESET_SESSION:
                    await adb_engine.raw_command(f"-s {device_id_str} shell am force-stop com.android.incallui")
                    await asyncio.sleep(1)
                    return {"success": True, "message": "call_session_reset"}

                case RecoveryAction.RECOVER_RECORDING:
                    await adb_engine.raw_command(f"-s {device_id_str} shell pkill -l SIGINT screenrecord")
                    return {"success": True, "message": "recording_recovered"}

                case RecoveryAction.RECOVER_CALL:
                    await adb_engine.raw_command(f"-s {device_id_str} shell am broadcast -a android.intent.action.PHONE_STATE")
                    return {"success": True, "message": "call_recovery_attempted"}

                case _:
                    return {"success": False, "error": f"unknown_action:{action_type}"}
        except Exception as e:
            logger.error("Recovery action %s failed: %s", action_type, e)
            return {"success": False, "error": str(e)}

    async def _log_recovery(self, device_id: int, failure_type: str, actions: list[str], recovered: bool) -> None:
        log = RecoveryLog(
            device_id=device_id,
            failure_type=failure_type,
            recovery_action=",".join(actions),
            status="completed" if recovered else "failed",
            error_message=None if recovered else "all_recovery_actions_failed",
        )
        self.db.add(log)
        self.db.commit()

        await self.reliability.report_recovery(device_id, ",".join(actions), recovered)

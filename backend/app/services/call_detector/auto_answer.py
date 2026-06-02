from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.setting_repository import SettingRepository
from app.services.adb_watcher import ADBEngine, ADBCommandStatus
from app.services.event_bus import EventBus, event_bus
from app.services.event_bus.event_types import CallAnsweredEvent

logger = logging.getLogger(__name__)


class AutoAnswerService:
    ANSWER_COMMANDS = [
        "shell:input keyevent KEYCODE_CALL",
        "shell:input keyevent 5",
        "shell:service call phone 0 s16 call",
    ]

    def __init__(self, adb_engine: ADBEngine, event_bus: EventBus) -> None:
        self.adb = adb_engine
        self.event_bus = event_bus
        self._answer_lock = asyncio.Lock()

    def _is_auto_answer_enabled(self) -> bool:
        try:
            db = SessionLocal()
            try:
                repo = SettingRepository(db)
                value = repo.get_value("auto_answer_enabled", "")
                if value:
                    return value.lower() in ("true", "1", "yes", "on")
            finally:
                db.close()
        except Exception:
            pass
        return settings.AUTO_ANSWER_ENABLED

    async def can_auto_answer(self, serial: str) -> bool:
        if not self._is_auto_answer_enabled():
            logger.debug("Auto answer disabled in settings")
            return False

        try:
            is_online = await self.adb.is_online(serial)
            if not is_online:
                logger.debug("Device %s not online, cannot auto-answer", serial)
                return False
            return True
        except Exception as e:
            logger.error("Error checking auto-answer capability: %s", e)
            return False

    async def attempt_answer(self, serial: str, call_data: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self._answer_lock:
            result: dict[str, Any] = {
                "serial": serial,
                "success": False,
                "attempts": 0,
                "command_used": "",
                "error": None,
                "answered_at": None,
            }

            if not await self.can_auto_answer(serial):
                result["error"] = "Cannot auto-answer: device not ready"
                return result

            await asyncio.sleep(settings.AUTO_ANSWER_DELAY_SECONDS)

            for attempt in range(settings.AUTO_ANSWER_RETRY_COUNT):
                result["attempts"] = attempt + 1
                try:
                    answer_result = await self._try_answer(serial)
                    if answer_result:
                        result["success"] = True
                        result["command_used"] = answer_result["command"]
                        result["answered_at"] = datetime.now(UTC).isoformat()

                        await self.event_bus.publish(
                            CallAnsweredEvent(
                                device_id=hash(serial),
                                caller_number=(
                                    call_data.get("caller_info", {}).get("number", "")
                                    if call_data else ""
                                ),
                                data={
                                    "serial": serial,
                                    "auto_answered": True,
                                    "attempts": attempt + 1,
                                    "call_session_id": call_data.get("call_session_id")
                                    if call_data else None,
                                    "verified_offhook": True,
                                },
                            )
                        )

                        logger.info(
                            "Auto-answer succeeded on %s after %d attempt(s)",
                            serial,
                            attempt + 1,
                        )
                        return result

                except Exception as e:
                    result["error"] = str(e)
                    logger.warning(
                        "Auto-answer attempt %d failed for %s: %s",
                        attempt + 1,
                        serial,
                        e,
                    )

                if attempt < settings.AUTO_ANSWER_RETRY_COUNT - 1:
                    await asyncio.sleep(1.0)

            result["error"] = result.get("error") or "All auto-answer attempts failed"
            logger.warning(
                "Auto-answer failed for %s after %d attempts",
                serial,
                settings.AUTO_ANSWER_RETRY_COUNT,
            )
            return result

    async def _try_answer(self, serial: str) -> dict[str, Any] | None:
        for command in self.ANSWER_COMMANDS:
            try:
                cmd_result = await self.adb.execute(serial, command)
                if cmd_result.status == ADBCommandStatus.SUCCESS:
                    await asyncio.sleep(0.75)
                    if await self.verify_answer(serial):
                        return {"command": command, "result": cmd_result}
                    logger.info("Auto-answer command sent on %s; OFFHOOK not verified yet", serial)
            except Exception as e:
                logger.debug("Answer command %s failed: %s", command, e)
        return None

    async def verify_answer(self, serial: str) -> bool:
        try:
            result = await self.adb.shell(serial, "dumpsys telephony.registry")
            if result.status == ADBCommandStatus.SUCCESS and result.stdout:
                import re
                match = re.search(r"mCallState\s*[=:]\s*(\d)", result.stdout)
                if match:
                    return match.group(1) == "2"
            return False
        except Exception:
            return False

    async def end_call(self, serial: str) -> bool:
        try:
            result = await self.adb.execute(
                serial, "shell:input keyevent KEYCODE_ENDCALL"
            )
            if result.status != ADBCommandStatus.SUCCESS:
                result = await self.adb.execute(
                    serial, "shell:input keyevent 6"
                )
            return result.status == ADBCommandStatus.SUCCESS
        except Exception as e:
            logger.error("Failed to end call on %s: %s", serial, e)
            return False

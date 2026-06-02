from __future__ import annotations

import logging
from typing import Any

from app.services.adb_watcher import ADBCommandStatus, adb_engine

logger = logging.getLogger(__name__)


class AutoAnswerCompatibilityService:
    def __init__(self) -> None:
        self._success_cache: dict[str, dict[str, Any]] = {}

    async def validate_answer_support(self, device_id: str) -> dict[str, Any]:
        if device_id in self._success_cache:
            return self._success_cache[device_id]

        results = {
            "supports_auto_answer": False,
            "best_command": None,
            "all_commands_tested": [],
            "success_rate": 0.0,
        }

        commands = [
            "input keyevent KEYCODE_CALL",
            "input keyevent 5",
            "service call phone 5",
            "am start -a android.intent.action.CALL_BUTTON",
        ]

        success_count = 0
        for cmd in commands:
            try:
                result = await adb_engine.shell(device_id, cmd)
                cmd_result = {"command": cmd[:40], "success": result.status == ADBCommandStatus.SUCCESS}
                results["all_commands_tested"].append(cmd_result)
                if result.status == ADBCommandStatus.SUCCESS:
                    success_count += 1
                    if results["best_command"] is None:
                        results["best_command"] = cmd[:40]
                        results["supports_auto_answer"] = True
            except Exception as e:
                results["all_commands_tested"].append({"command": cmd[:40], "success": False, "error": str(e)})

        results["success_rate"] = success_count / len(commands) if commands else 0
        self._success_cache[device_id] = results
        return results

    async def track_answer_attempt(self, device_id: str, success: bool) -> None:
        if device_id not in self._success_cache:
            return
        cache = self._success_cache[device_id]
        cache["last_attempt_success"] = success

    def clear_cache(self, device_id: str) -> None:
        self._success_cache.pop(device_id, None)

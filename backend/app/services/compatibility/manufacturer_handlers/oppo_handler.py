from __future__ import annotations

import logging

from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.compatibility.manufacturer_handlers.generic_handler import (
    GenericAndroidHandler,
)
from app.services.compatibility.manufacturer_handlers.manufacturer_handler import (
    HandlerResult,
)

logger = logging.getLogger(__name__)


class OppoHandler(GenericAndroidHandler):
    @property
    def manufacturer_name(self) -> str:
        return "oppo"

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        base = await super().detect_capabilities(device_id)
        coloros = await adb_engine.shell(device_id, "getprop ro.build.version.opporom")
        has_coloros = coloros.status == ADBCommandStatus.SUCCESS and bool(coloros.stdout.strip())
        if has_coloros:
            base["supports_background_execution"] = False
        return base

    async def answer_call(self, device_id: str) -> HandlerResult:
        commands = ["input keyevent KEYCODE_CALL", "input keyevent 5"]
        for cmd in commands:
            result = await adb_engine.shell(device_id, cmd)
            if result.status == ADBCommandStatus.SUCCESS:
                return HandlerResult(success=True, action_taken=f"oppo_answer:{cmd[:30]}")
        return HandlerResult(success=False, error="Oppo answer failed", action_taken="oppo_answer")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, f"screenrecord {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="oppo_record:screenrecord")
        return HandlerResult(success=False, error="Oppo recording failed", action_taken="oppo_record")

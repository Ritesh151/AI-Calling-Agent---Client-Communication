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


class XiaomiHandler(GenericAndroidHandler):
    @property
    def manufacturer_name(self) -> str:
        return "xiaomi"

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        base = await super().detect_capabilities(device_id)
        miui = await adb_engine.shell(device_id, "getprop ro.miui.ui.version.name")
        has_miui = miui.status == ADBCommandStatus.SUCCESS and bool(miui.stdout.strip())
        if has_miui:
            base["supports_background_execution"] = False
            base["supports_auto_answer"] = False
        return base

    async def answer_call(self, device_id: str) -> HandlerResult:
        commands = [
            "input keyevent KEYCODE_CALL",
            "input keyevent 5",
            "am start -a android.intent.action.CALL_BUTTON",
        ]
        for cmd in commands:
            result = await adb_engine.shell(device_id, cmd)
            if result.status == ADBCommandStatus.SUCCESS:
                return HandlerResult(success=True, action_taken=f"xiaomi_answer:{cmd[:30]}")
        return HandlerResult(success=False, error="Xiaomi answer failed", action_taken="xiaomi_answer")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, f"screenrecord {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="xiaomi_record:screenrecord")
        return HandlerResult(success=False, error="Xiaomi recording failed", action_taken="xiaomi_record")

    async def recover(self, device_id: str, failure: str) -> HandlerResult:
        logger.info("Xiaomi recovery for %s after %s", device_id, failure)
        if "answer" in failure.lower() or "call" in failure.lower():
            await adb_engine.shell(device_id, "am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS")
            return HandlerResult(success=True, action_taken="xiaomi_recover:close_dialogs")
        return await super().recover(device_id, failure)

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


class SamsungHandler(GenericAndroidHandler):
    @property
    def manufacturer_name(self) -> str:
        return "samsung"

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        base = await super().detect_capabilities(device_id)
        one_ui = await adb_engine.shell(device_id, "getprop ro.build.PDA")
        has_one_ui = one_ui.status == ADBCommandStatus.SUCCESS and bool(one_ui.stdout.strip())
        base["supports_background_execution"] = not has_one_ui
        if has_one_ui:
            base["supports_auto_answer"] = False
        return base

    async def answer_call(self, device_id: str) -> HandlerResult:
        commands = [
            "input keyevent KEYCODE_CALL",
            "input keyevent 5",
            "service call phone 5",
            "am start -a android.intent.action.CALL_BUTTON",
        ]
        for cmd in commands:
            result = await adb_engine.shell(device_id, cmd)
            if result.status == ADBCommandStatus.SUCCESS:
                return HandlerResult(success=True, action_taken=f"samsung_answer:{cmd[:30]}")
        return HandlerResult(success=False, error="Samsung answer failed", action_taken="samsung_answer")

    async def detect_call(self, device_id: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, "dumpsys telephony.registry")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, data=result.stdout, action_taken="samsung_detect_call")
        alt = await adb_engine.shell(device_id, "dumpsys telecom")
        if alt.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, data=alt.stdout, action_taken="samsung_detect_call:telecom")
        return HandlerResult(success=False, error="Samsung call detection failed", action_taken="samsung_detect_call")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        cmd = f"cmd media recorder start {output_path}"
        result = await adb_engine.shell(device_id, cmd)
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="samsung_record:mediarecorder")
        scr = f"screenrecord --time-limit 0 {output_path}"
        result = await adb_engine.shell(device_id, scr)
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="samsung_record:screenrecord")
        return HandlerResult(success=False, error="Samsung recording failed", action_taken="samsung_record")

    async def recover(self, device_id: str, failure: str) -> HandlerResult:
        logger.info("Samsung recovery for %s after %s", device_id, failure)
        if "record" in failure.lower():
            await adb_engine.shell(device_id, "pkill -f screenrecord")
            await adb_engine.shell(device_id, "pkill -f media")
            return HandlerResult(success=True, action_taken="samsung_recover:killed_media")
        return await super().recover(device_id, failure)

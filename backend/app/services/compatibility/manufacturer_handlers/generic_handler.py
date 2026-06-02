from __future__ import annotations

import logging
from typing import Any

from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.compatibility.manufacturer_handlers.manufacturer_handler import (
    HandlerResult,
    ManufacturerHandler,
)

logger = logging.getLogger(__name__)


class GenericAndroidHandler(ManufacturerHandler):
    @property
    def manufacturer_name(self) -> str:
        return "generic"

    async def initialize(self, device_id: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, "echo initialized")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="initialize")
        return HandlerResult(success=False, error=result.error_message, action_taken="initialize")

    async def validate_device(self, device_id: str) -> bool:
        result = await adb_engine.is_online(device_id)
        return result

    async def detect_capabilities(self, device_id: str) -> dict[str, bool]:
        # Test basic capabilities
        call_test = await adb_engine.shell(device_id, "dumpsys telephony.registry")
        has_telephony = call_test.status == ADBCommandStatus.SUCCESS

        audio_test = await adb_engine.shell(device_id, "dumpsys media.audio_flinger")
        has_audio = audio_test.status == ADBCommandStatus.SUCCESS

        scr_test = await adb_engine.shell(device_id, "which screenrecord")
        has_screenrecord = scr_test.status == ADBCommandStatus.SUCCESS and "screenrecord" in scr_test.stdout

        cmd_test = await adb_engine.shell(device_id, "cmd media recorder --help")
        has_media_recorder = cmd_test.status == ADBCommandStatus.SUCCESS

        bg_test = await adb_engine.shell(device_id, "dumpsys deviceidle")
        has_bg = bg_test.status == ADBCommandStatus.SUCCESS

        return {
            "supports_auto_answer": has_telephony,
            "supports_call_detection": has_telephony,
            "supports_audio_capture": has_audio,
            "supports_speaker_recording": has_screenrecord,
            "supports_mic_recording": has_screenrecord,
            "supports_tts_playback": has_audio,
            "supports_background_execution": has_bg,
        }

    async def detect_call(self, device_id: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, "dumpsys telephony.registry")
        if result.status != ADBCommandStatus.SUCCESS:
            return HandlerResult(success=False, error=result.error_message, action_taken="detect_call")
        return HandlerResult(success=True, data=result.stdout, action_taken="detect_call")

    async def answer_call(self, device_id: str) -> HandlerResult:
        commands = ["input keyevent KEYCODE_CALL", "input keyevent 5", "service call phone 5"]
        for cmd in commands:
            result = await adb_engine.shell(device_id, cmd)
            if result.status == ADBCommandStatus.SUCCESS:
                return HandlerResult(success=True, action_taken=f"answer_call:{cmd[:30]}")
        return HandlerResult(
            success=False, error="All answer commands failed", action_taken="answer_call"
        )

    async def play_greeting(self, device_id: str, audio_path: str) -> HandlerResult:
        cmd = f"play {audio_path}"
        result = await adb_engine.shell(device_id, cmd)
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="play_greeting")
        alt = f"mediaplayer {audio_path}"
        result = await adb_engine.shell(device_id, alt)
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="play_greeting:alt")
        return HandlerResult(success=False, error="Play greeting failed", action_taken="play_greeting")

    async def start_recording(self, device_id: str, output_path: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, f"screenrecord --time-limit 0 {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="start_recording:screenrecord")
        result = await adb_engine.shell(device_id, f"cmd media recorder start {output_path}")
        if result.status == ADBCommandStatus.SUCCESS:
            return HandlerResult(success=True, action_taken="start_recording:mediarecorder")
        return HandlerResult(success=False, error="All recording strategies failed", action_taken="start_recording")

    async def stop_recording(self, device_id: str) -> HandlerResult:
        result = await adb_engine.shell(device_id, "pkill -f screenrecord")
        await adb_engine.shell(device_id, "cmd media recorder stop")
        return HandlerResult(success=True, action_taken="stop_recording")

    async def recover(self, device_id: str, failure: str) -> HandlerResult:
        logger.info("Generic recovery for %s after %s", device_id, failure)
        if "adb" in failure.lower() or "timeout" in failure.lower():
            await adb_engine.reconnect()
            return HandlerResult(success=True, action_taken="recover:adb_restart")
        if "call" in failure.lower() or "answer" in failure.lower():
            return HandlerResult(success=True, action_taken="recover:call_retry")
        if "record" in failure.lower():
            await adb_engine.shell(device_id, "pkill -f screenrecord")
            return HandlerResult(success=True, action_taken="recover:recording_reset")
        return HandlerResult(success=True, action_taken="recover:generic")

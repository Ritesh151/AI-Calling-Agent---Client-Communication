from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppException
from app.services.adb_watcher import ADBEngine, ADBCommandStatus
from app.services.call_state.state_machine import CallState, CallStateMachine
from app.services.call_detector.caller_identifier import CallerIdentifier, CallerInfo
from app.services.event_bus import EventBus, event_bus
from app.services.event_bus.event_types import (
    IncomingCallEvent,
    CallAnsweredEvent,
    CallEndedEvent,
    CallMissedEvent,
    CallStateChangedEvent,
)

logger = logging.getLogger(__name__)


class CallDetectionEngine:
    CALL_STATE_MAP = {
        "0": CallState.IDLE,
        "1": CallState.RINGING,
        "2": CallState.ACTIVE,
    }

    def __init__(self, adb_engine: ADBEngine, event_bus: EventBus) -> None:
        self.adb = adb_engine
        self.event_bus = event_bus
        self._state_machines: dict[str, CallStateMachine] = {}
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_states: dict[str, str] = {}
        self._active_calls: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._polling_loop())
        logger.info("Call detection engine started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Call detection engine stopped")

    async def _polling_loop(self) -> None:
        while self._running:
            try:
                if not self.adb.is_server_running:
                    await self.adb.start_server()
                devices = await self.adb.list_devices()
                for device in devices:
                    if device.state == "device":
                        await self._check_call_state(device.serial)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Call detection poll error: %s", e)
            await asyncio.sleep(settings.CALL_POLL_INTERVAL_SECONDS)

    async def _check_call_state(self, serial: str) -> None:
        try:
            result = await self.adb.shell(serial, "dumpsys telephony.registry")
            if result.status != ADBCommandStatus.SUCCESS or not result.stdout:
                return

            call_state_code = self._parse_call_state(result.stdout)
            if call_state_code is None:
                return

            current_state = self.CALL_STATE_MAP.get(call_state_code, CallState.IDLE)
            last_state_str = self._last_states.get(serial)

            if last_state_str == call_state_code:
                return

            self._last_states[serial] = call_state_code
            machine = self._get_or_create_machine(serial)

            try:
                transition = machine.transition(current_state)
                await self.event_bus.publish(
                    CallStateChangedEvent(
                        device_id=hash(serial),
                        data={
                            "serial": serial,
                            "old_state": transition["from"],
                            "new_state": transition["to"],
                        },
                    )
                )
            except AppException:
                pass

            if current_state == CallState.RINGING:
                await self._handle_incoming_call(serial, result.stdout)
            elif current_state == CallState.ACTIVE and last_state_str == "1":
                await self._handle_call_answered(serial)
            elif current_state == CallState.IDLE and last_state_str in ("1", "2"):
                await self._handle_call_ended(serial, last_state_str)

        except Exception as e:
            logger.debug("Error checking call state for %s: %s", serial, e)

    async def _handle_incoming_call(self, serial: str, raw_data: str) -> None:
        number = self._extract_caller_number(raw_data)
        caller_info = CallerIdentifier.identify(number, raw_data)

        call_data = {
            "serial": serial,
            "caller_info": {
                "number": caller_info.caller_number,
                "name": caller_info.caller_name,
                "type": caller_info.caller_type,
                "country_code": caller_info.country_code,
                "normalized_number": caller_info.normalized_number,
            },
            "raw_data": raw_data,
            "detected_at": datetime.now(UTC).isoformat(),
        }

        self._active_calls[serial] = call_data

        await self.event_bus.publish(
            IncomingCallEvent(
                device_id=hash(serial),
                caller_number=caller_info.caller_number,
                caller_name=caller_info.caller_name,
                caller_type=caller_info.caller_type,
                raw_data=raw_data,
                data=call_data,
            )
        )

        logger.info(
            "Incoming call detected on %s from %s (%s)",
            serial,
            caller_info.caller_number,
            caller_info.caller_type,
        )

    async def _handle_call_answered(self, serial: str) -> None:
        call_data = self._active_calls.get(serial, {})
        caller_info = call_data.get("caller_info", {})
        call_data["answered_at"] = datetime.now(UTC).isoformat()

        await self.event_bus.publish(
            CallAnsweredEvent(
                device_id=hash(serial),
                caller_number=caller_info.get("number", ""),
                data=call_data,
            )
        )

        logger.info(
            "Call answered on %s from %s",
            serial,
            caller_info.get("number", "unknown"),
        )

    async def _handle_call_ended(self, serial: str, last_state: str) -> None:
        call_data = self._active_calls.pop(serial, {})
        caller_info = call_data.get("caller_info", {})

        ended_event = CallEndedEvent(
            device_id=hash(serial),
            caller_number=caller_info.get("number", ""),
            data=call_data,
        )

        if last_state == "1":
            await self.event_bus.publish(
                CallMissedEvent(
                    device_id=hash(serial),
                    caller_number=caller_info.get("number", ""),
                    data=call_data,
                )
            )
            logger.info(
                "Call missed on %s from %s",
                serial,
                caller_info.get("number", "unknown"),
            )

        await self.event_bus.publish(ended_event)
        machine = self._state_machines.get(serial)
        if machine:
            machine.reset()

        logger.info("Call ended on %s", serial)

    def _parse_call_state(self, dumpsys_output: str) -> str | None:
        patterns = [
            r"mCallState\s*[=:]\s*(\d)",
            r"callState\s*[=:]\s*(\d)",
            r"mCallState\s+(\d)",
            r"call_state\s*[=:]\s*(\d)",
        ]
        for pattern in patterns:
            match = re.search(pattern, dumpsys_output)
            if match:
                return match.group(1)
        return None

    def _extract_caller_number(self, dumpsys_output: str) -> str:
        patterns = [
            r"mCallerNumber\s*[=:]\s*([^\r\n]+)",
            r"callerNumber\s*[=:]\s*([^\r\n]+)",
            r"mCallerNumber\s+([^\r\n]+)",
            r"incomingNumber\s*[=:]\s*([^\r\n]+)",
            r"mIncomingNumber\s*[=:]\s*([^\r\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, dumpsys_output)
            if match:
                return match.group(1).strip()

        lines = dumpsys_output.split("\n")
        for i, line in enumerate(lines):
            if "number" in line.lower() and ("call" in line.lower() or "incoming" in line.lower()):
                parts = line.split(":")
                if len(parts) > 1:
                    return parts[-1].strip()
        return ""

    def _get_or_create_machine(self, serial: str) -> CallStateMachine:
        if serial not in self._state_machines:
            self._state_machines[serial] = CallStateMachine(hash(serial))
        return self._state_machines[serial]

    def get_call_state(self, serial: str) -> str:
        machine = self._state_machines.get(serial)
        if machine:
            return machine.state_value
        return CallState.IDLE.value

    def get_active_call(self, serial: str) -> dict[str, Any] | None:
        return self._active_calls.get(serial)

    def get_all_active_calls(self) -> dict[str, dict[str, Any]]:
        return dict(self._active_calls)

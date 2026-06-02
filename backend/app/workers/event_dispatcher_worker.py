from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.services.event_bus import event_bus
from app.services.event_bus.event_types import (
    BaseEvent,
    DeviceConnectedEvent,
    DeviceDisconnectedEvent,
    DeviceHeartbeatEvent,
    DeviceMetricsUpdatedEvent,
    DevicesSyncedEvent,
    SettingsUpdatedEvent,
    IncomingCallEvent,
    CallAnsweredEvent,
    CallMissedEvent,
    CallEndedEvent,
    CallStateChangedEvent,
    ADBStatusChangedEvent,
)
from app.services.websocket import ws_manager

logger = logging.getLogger(__name__)


class EventDispatcherWorker:
    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        self._running = True
        event_bus.subscribe("*", self._dispatch_event)
        logger.info("Event dispatcher worker started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Event dispatcher worker stopped")

    async def _dispatch_event(self, event: BaseEvent) -> None:
        if not self._running:
            return

        try:
            event_data: dict[str, Any] = {
                "event_type": event.event_type,
                "device_id": event.device_id,
                "timestamp": event.timestamp,
                "data": event.data,
            }

            if isinstance(event, DeviceConnectedEvent):
                event_data["serial"] = event.serial
                event_data["manufacturer"] = event.manufacturer
                event_data["model"] = event.model
            elif isinstance(event, DeviceDisconnectedEvent):
                event_data["serial"] = event.serial
            elif isinstance(event, DeviceHeartbeatEvent):
                event_data["battery_level"] = event.battery_level
                event_data["charging"] = event.charging
                event_data["screen_state"] = event.screen_state
                event_data["is_online"] = event.is_online
            elif isinstance(event, IncomingCallEvent):
                event_data["caller_number"] = event.caller_number
                event_data["caller_name"] = event.caller_name
                event_data["caller_type"] = event.caller_type
            elif isinstance(event, CallAnsweredEvent):
                event_data["caller_number"] = event.caller_number
                event_data["call_session_id"] = event.call_session_id
            elif isinstance(event, CallMissedEvent):
                event_data["caller_number"] = event.caller_number
                event_data["call_session_id"] = event.call_session_id
            elif isinstance(event, CallEndedEvent):
                event_data["caller_number"] = event.caller_number
                event_data["duration"] = event.duration
                event_data["call_session_id"] = event.call_session_id
            elif isinstance(event, CallStateChangedEvent):
                event_data["old_state"] = event.old_state
                event_data["new_state"] = event.new_state
                event_data["call_session_id"] = event.call_session_id
            elif isinstance(event, ADBStatusChangedEvent):
                event_data["old_status"] = event.old_status
                event_data["new_status"] = event.new_status
            elif isinstance(event, DeviceMetricsUpdatedEvent):
                event_data["battery_level"] = event.battery_level
                event_data["charging"] = event.charging
                event_data["screen_state"] = event.screen_state
            elif isinstance(event, DevicesSyncedEvent):
                pass
            elif isinstance(event, SettingsUpdatedEvent):
                event_data["key"] = event.key
                event_data["value"] = event.value

            await ws_manager.broadcast(event.event_type, event_data)

        except Exception as e:
            logger.error("Event dispatch error: %s", e)

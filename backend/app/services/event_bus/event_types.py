from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class BaseEvent:
    device_id: int | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceConnectedEvent(BaseEvent):
    event_type: str = "device_connected"
    serial: str = ""
    manufacturer: str = ""
    model: str = ""


@dataclass
class DeviceDisconnectedEvent(BaseEvent):
    event_type: str = "device_disconnected"
    serial: str = ""


@dataclass
class DevicesSyncedEvent(BaseEvent):
    event_type: str = "devices_synced"


@dataclass
class SettingsUpdatedEvent(BaseEvent):
    event_type: str = "settings_updated"
    key: str = ""
    value: str = ""


@dataclass
class DeviceHeartbeatEvent(BaseEvent):
    event_type: str = "heartbeat"
    battery_level: int | None = None
    charging: bool | None = None
    screen_state: str | None = None
    is_online: bool = True


@dataclass
class IncomingCallEvent(BaseEvent):
    event_type: str = "incoming_call"
    caller_number: str = ""
    caller_name: str = ""
    caller_type: str = "unknown"
    raw_data: str = ""


@dataclass
class CallAnsweredEvent(BaseEvent):
    event_type: str = "call_answered"
    caller_number: str = ""
    call_session_id: int | None = None


@dataclass
class CallMissedEvent(BaseEvent):
    event_type: str = "call_missed"
    caller_number: str = ""
    call_session_id: int | None = None


@dataclass
class CallEndedEvent(BaseEvent):
    event_type: str = "call_ended"
    caller_number: str = ""
    duration: float | None = None
    call_session_id: int | None = None


@dataclass
class CallStateChangedEvent(BaseEvent):
    event_type: str = "call_state_changed"
    old_state: str = ""
    new_state: str = ""
    call_session_id: int | None = None


@dataclass
class ADBStatusChangedEvent(BaseEvent):
    event_type: str = "adb_status_changed"
    old_status: str = ""
    new_status: str = ""


@dataclass
class DeviceMetricsUpdatedEvent(BaseEvent):
    event_type: str = "device_metrics_updated"
    battery_level: int | None = None
    charging: bool | None = None
    screen_state: str | None = None

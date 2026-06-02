from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class CallState(Enum):
    IDLE = "idle"
    RINGING = "ringing"
    ANSWERING = "answering"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"
    FAILED = "failed"


class CallStateTransition:
    _transitions: dict[CallState, set[CallState]] = {
        CallState.IDLE: {CallState.RINGING},
        CallState.RINGING: {CallState.ANSWERING, CallState.ENDED, CallState.MISSED},
        CallState.ANSWERING: {CallState.ACTIVE, CallState.FAILED, CallState.MISSED},
        CallState.ACTIVE: {CallState.ENDED, CallState.FAILED},
        CallState.ENDED: set(),
        CallState.MISSED: set(),
        CallState.FAILED: set(),
    }

    @classmethod
    def is_valid(cls, from_state: CallState, to_state: CallState) -> bool:
        return to_state in cls._transitions.get(from_state, set())

    @classmethod
    def get_allowed_transitions(cls, state: CallState) -> list[str]:
        return [s.value for s in cls._transitions.get(state, set())]


class CallStateMachine:
    def __init__(self, device_id: int) -> None:
        self.device_id = device_id
        self._current_state: CallState = CallState.IDLE
        self._previous_state: CallState | None = None
        self._history: list[dict[str, Any]] = []
        self._started_at: datetime | None = None
        self._locked = False

    @property
    def current_state(self) -> CallState:
        return self._current_state

    @property
    def previous_state(self) -> CallState | None:
        return self._previous_state

    @property
    def state_value(self) -> str:
        return self._current_state.value

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def transition(self, to_state: CallState) -> dict[str, Any]:
        from_state = self._current_state

        if not CallStateTransition.is_valid(from_state, to_state):
            raise AppException(
                message=f"Invalid state transition: {from_state.value} -> {to_state.value}",
                error_code="INVALID_STATE_TRANSITION",
            )

        self._previous_state = from_state
        self._current_state = to_state

        transition_record = {
            "from": from_state.value,
            "to": to_state.value,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._history.append(transition_record)

        if to_state == CallState.RINGING and self._started_at is None:
            self._started_at = datetime.now(UTC)
        elif to_state in (CallState.ENDED, CallState.MISSED, CallState.FAILED):
            self._started_at = None

        logger.info(
            "Device %s call state: %s -> %s",
            self.device_id,
            from_state.value,
            to_state.value,
        )

        return transition_record

    def can_transition_to(self, state: CallState) -> bool:
        return CallStateTransition.is_valid(self._current_state, state)

    def reset(self) -> None:
        self._current_state = CallState.IDLE
        self._previous_state = None
        self._started_at = None

    def get_duration(self) -> float | None:
        if self._started_at and self._current_state in (CallState.ACTIVE, CallState.ENDED):
            return (datetime.now(UTC) - self._started_at).total_seconds()
        return None

    def get_state_info(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "current_state": self._current_state.value,
            "previous_state": self._previous_state.value if self._previous_state else None,
            "allowed_transitions": CallStateTransition.get_allowed_transitions(self._current_state),
            "duration": self.get_duration(),
            "history_count": len(self._history),
        }

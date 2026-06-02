from __future__ import annotations

from app.services.call_state.state_machine import CallState, CallStateMachine, CallStateTransition


def test_state_machine_initial_state() -> None:
    machine = CallStateMachine(device_id=1)
    assert machine.state_value == "idle"


def test_valid_transition_idle_to_ringing() -> None:
    machine = CallStateMachine(device_id=1)
    transition = machine.transition(CallState.RINGING)
    assert transition["from"] == "idle"
    assert transition["to"] == "ringing"


def test_invalid_transition_idle_to_active() -> None:
    machine = CallStateMachine(device_id=1)
    from app.core.exceptions import AppException
    try:
        machine.transition(CallState.ACTIVE)
        assert False, "Should have raised exception"
    except AppException:
        pass


def test_full_call_lifecycle() -> None:
    machine = CallStateMachine(device_id=1)
    assert machine.state_value == "idle"

    machine.transition(CallState.RINGING)
    assert machine.state_value == "ringing"

    machine.transition(CallState.ANSWERING)
    assert machine.state_value == "answering"

    machine.transition(CallState.ACTIVE)
    assert machine.state_value == "active"

    machine.transition(CallState.ENDED)
    assert machine.state_value == "ended"


def test_missed_call() -> None:
    machine = CallStateMachine(device_id=1)
    machine.transition(CallState.RINGING)
    machine.transition(CallState.MISSED)
    assert machine.state_value == "missed"


def test_state_history() -> None:
    machine = CallStateMachine(device_id=1)
    machine.transition(CallState.RINGING)
    machine.transition(CallState.MISSED)
    assert len(machine.history) == 2


def test_can_transition_to() -> None:
    machine = CallStateMachine(device_id=1)
    assert machine.can_transition_to(CallState.RINGING)
    assert not machine.can_transition_to(CallState.ACTIVE)


def test_get_allowed_transitions() -> None:
    allowed = CallStateTransition.get_allowed_transitions(CallState.IDLE)
    assert "ringing" in allowed
    assert "active" not in allowed


def test_reset() -> None:
    machine = CallStateMachine(device_id=1)
    machine.transition(CallState.RINGING)
    machine.reset()
    assert machine.state_value == "idle"
    assert machine.history == []

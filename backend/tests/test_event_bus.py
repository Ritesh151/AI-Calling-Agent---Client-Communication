from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app.services.event_bus import EventBus, EventPriority, event_bus
from app.services.event_bus.event_types import (
    DeviceConnectedEvent,
    IncomingCallEvent,
    BaseEvent,
)


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    received: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("test_event", handler)
    await bus.start()

    test_event = BaseEvent(device_id=1, data={"key": "value"})
    test_event.event_type = "test_event"
    await bus.publish(test_event)
    await asyncio.sleep(0.1)

    assert len(received) == 1
    assert received[0].device_id == 1
    assert received[0].data["key"] == "value"

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_wildcard() -> None:
    bus = EventBus()
    received: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("*", handler)
    await bus.start()

    e1 = BaseEvent(device_id=1)
    e1.event_type = "type_a"
    e2 = BaseEvent(device_id=2)
    e2.event_type = "type_b"

    await bus.publish(e1)
    await bus.publish(e2)
    await asyncio.sleep(0.1)

    assert len(received) == 2


@pytest.mark.asyncio
async def test_event_bus_priority() -> None:
    bus = EventBus()
    execution_order: list[str] = []

    async def high_handler(event: BaseEvent) -> None:
        execution_order.append("high")

    async def low_handler(event: BaseEvent) -> None:
        execution_order.append("low")

    bus.subscribe("priority_test", high_handler, EventPriority.HIGH)
    bus.subscribe("priority_test", low_handler, EventPriority.LOW)
    await bus.start()

    event = BaseEvent()
    event.event_type = "priority_test"
    await bus.publish(event)
    await asyncio.sleep(0.1)

    assert execution_order == ["high", "low"]
    await bus.stop()

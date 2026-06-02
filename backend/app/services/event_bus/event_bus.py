from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from enum import IntEnum
from typing import Any, Awaitable, Callable

from app.services.event_bus.event_types import BaseEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[BaseEvent], Awaitable[None]]


class EventPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Event:
    def __init__(self, name: str = "", data: dict[str, Any] | None = None, priority: EventPriority = EventPriority.NORMAL, type: str = "") -> None:
        self.name = type if type else name
        self.data = data or {}
        self.priority = priority


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[tuple[EventHandler, EventPriority]]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: str, handler: EventHandler, priority: EventPriority = EventPriority.NORMAL) -> None:
        self._subscribers[event_type].append((handler, priority))
        logger.debug("Subscribed handler for event type: %s", event_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type] = [
            (h, p) for h, p in self._subscribers[event_type] if h != handler
        ]

    async def publish(self, event: BaseEvent | Event) -> None:
        if isinstance(event, Event):
            base = BaseEvent(
                device_id=event.data.get("device_id"),
                data=event.data,
            )
            base.event_type = event.name
            await self._event_queue.put(base)
        else:
            await self._event_queue.put(event)
        logger.debug("Event queued")

    def publish_nowait(self, event: BaseEvent | Event) -> None:
        if isinstance(event, Event):
            base = BaseEvent(
                device_id=event.data.get("device_id"),
                data=event.data,
            )
            base.event_type = event.name
            self._event_queue.put_nowait(base)
        else:
            self._event_queue.put_nowait(event)
        logger.debug("Event queued")

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus stopped")

    async def _process_events(self) -> None:
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(), timeout=1.0
                )
                await self._dispatch(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Event processing error: %s", e)

    async def _dispatch(self, event: BaseEvent) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        wildcard_handlers = self._subscribers.get("*", [])

        all_handlers = handlers + wildcard_handlers
        if not all_handlers:
            return

        sorted_handlers = sorted(all_handlers, key=lambda x: x[1].value, reverse=True)

        for handler, _ in sorted_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(
                    "Handler failed for event %s: %s", event.event_type, e
                )


event_bus = EventBus()

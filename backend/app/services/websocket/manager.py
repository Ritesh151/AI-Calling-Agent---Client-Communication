from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[int, WebSocket] = {}
        self._connection_lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket, client_id: int = 0) -> None:
        await websocket.accept()
        async with self._connection_lock:
            self._connections[client_id] = websocket
        logger.info("WebSocket client %d connected (%d total)", client_id, len(self._connections))
        self._ensure_heartbeat()

    async def disconnect(self, client_id: int) -> None:
        async with self._connection_lock:
            self._connections.pop(client_id, None)
        logger.info("WebSocket client %d disconnected (%d remaining)", client_id, len(self._connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        async with self._connection_lock:
            disconnected: list[int] = []
            for client_id, ws in self._connections.items():
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(client_id)
            for client_id in disconnected:
                self._connections.pop(client_id, None)

    async def send_to(self, client_id: int, event_type: str, data: dict[str, Any]) -> bool:
        async with self._connection_lock:
            ws = self._connections.get(client_id)
            if not ws:
                return False
            try:
                message = json.dumps({
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                await ws.send_text(message)
                return True
            except Exception:
                self._connections.pop(client_id, None)
                return False

    def _ensure_heartbeat(self) -> None:
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_INTERVAL)
            try:
                async with self._connection_lock:
                    disconnected: list[int] = []
                    for client_id, ws in self._connections.items():
                        try:
                            await ws.send_json({"type": "ping"})
                        except Exception:
                            disconnected.append(client_id)
                    for client_id in disconnected:
                        self._connections.pop(client_id, None)
            except Exception:
                pass

    @property
    def active_connections(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()

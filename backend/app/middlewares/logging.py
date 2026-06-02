from __future__ import annotations

import logging
import time
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Pure ASGI middleware — safe for WebSocket connections.

    Starlette's BaseHTTPMiddleware breaks WebSocket upgrade handshakes; this
    implementation only logs HTTP scopes.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        method = scope.get("method", "")
        path = scope.get("path", "")

        await self.app(scope, receive, send_wrapper)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_line = f"{method} {path} {status_code} {duration_ms}ms"
        if status_code >= 400:
            logger.warning("Request failed: %s", log_line)
        else:
            logger.info("Request completed: %s", log_line)

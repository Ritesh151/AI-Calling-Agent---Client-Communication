from __future__ import annotations

import time
from collections import defaultdict

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.exceptions import RateLimitException

class RateLimitMiddleware:
    """Pure ASGI rate limiter — skips WebSocket scopes."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._rate_limit_store: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        now = time.time()
        window = 60.0
        max_requests = settings.RATE_LIMIT_REQUESTS_PER_MINUTE

        self._rate_limit_store[client_ip] = [
            t for t in self._rate_limit_store[client_ip] if now - t < window
        ]


        if len(self._rate_limit_store[client_ip]) >= max_requests:
            exc = RateLimitException(
                message=f"Rate limit exceeded. Max {max_requests} requests per minute."
            )
            await self._send_json_error(send, exc.status_code, exc.message, scope)
            return

        self._rate_limit_store[client_ip].append(now)
        await self.app(scope, receive, send)

    async def _send_json_error(self, send: Send, status: int, message: str, scope: Scope | None = None) -> None:
        body = (
            f'{{"success":false,"message":"{message}","error_code":"RATE_LIMIT_EXCEEDED"}}'
        ).encode()
        headers = [
            [b"content-type", b"application/json"],
        ]
        if scope:
            for h_name, h_value in scope.get("headers", []):
                if h_name == b"origin":
                    allowed = settings.CORS_ORIGINS
                    origin_str = h_value.decode()
                    if origin_str in allowed:
                        headers.append([b"access-control-allow-origin", origin_str.encode()])
                        headers.append([b"access-control-allow-credentials", b"true"])
                    break
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            }
        )
        await send({"type": "http.response.body", "body": body})

"""ASGI middleware that binds request/trace/task IDs for the whole request."""

from __future__ import annotations

import logging
import re
import time

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.metrics import observe_http_request
from core.request_context import (
    REQUEST_ID_HEADER,
    TASK_ID_HEADER,
    TRACE_ID_HEADER,
    RequestContext,
    bind_request_context,
    generate_id,
    normalize_id,
    reset_request_context,
)

logger = logging.getLogger(__name__)

_SKIP_ACCESS_LOG = {
    "/api/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
}
_ID_SEGMENT = re.compile(r"/[0-9]+|/GS[0-9]+|/PKG[0-9]+|/RT[0-9]+|/DB[0-9]+")


def normalize_path(path: str, scope: Scope | None = None) -> str:
    route = None if scope is None else scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str) and template:
        return template[:128]
    collapsed = _ID_SEGMENT.sub("/{id}", path)
    return collapsed[:128]


class RequestContextMiddleware:
    """Outermost ASGI wrapper: IDs, access log, HTTP counters, response headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = normalize_id(headers.get(REQUEST_ID_HEADER.lower())) or generate_id()
        trace_id = normalize_id(headers.get(TRACE_ID_HEADER.lower())) or request_id
        task_id = normalize_id(headers.get(TASK_ID_HEADER.lower()))
        idempotency_key = normalize_id(headers.get("x-idempotency-key"))
        context = RequestContext(
            request_id=request_id,
            trace_id=trace_id,
            task_id=task_id,
            idempotency_key=idempotency_key,
        )
        token = bind_request_context(context)
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id
        scope["state"]["trace_id"] = trace_id
        scope["state"]["task_id"] = task_id
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
                raw_headers = MutableHeaders(scope=message)
                raw_headers[REQUEST_ID_HEADER] = request_id
                raw_headers[TRACE_ID_HEADER] = trace_id
                if task_id:
                    raw_headers[TASK_ID_HEADER] = task_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            path = scope.get("path") or ""
            observe_http_request(
                method=scope.get("method") or "GET",
                path=normalize_path(str(path), scope),
                status=status_code,
            )
            if str(path) not in _SKIP_ACCESS_LOG:
                logger.info(
                    "http_request",
                    extra={
                        "method": scope.get("method"),
                        "path": str(path)[:256],
                        "status": status_code,
                        "duration_ms": duration_ms,
                    },
                )
            reset_request_context(token)

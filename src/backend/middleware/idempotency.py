"""Database-backed idempotency middleware for write requests."""
from __future__ import annotations

import hashlib
import asyncio
import json
import logging
from dataclasses import dataclass

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.error_codes import (
    CODE_SUCCESS,
    CODE_DATABASE_ERROR,
    CODE_IDEMPOTENCY_IN_PROGRESS,
    CODE_IDEMPOTENCY_KEY_INVALID,
    CODE_IDEMPOTENCY_PAYLOAD_MISMATCH,
    CODE_REQUEST_BODY_TOO_LARGE,
    get_error_definition,
)
from core.exception_mapping import safe_response_headers
from core.validators import validate_idempotency_key
from utils.idempotency_store import (
    StoredResponse,
    cache_succeeded_response,
    claim_request,
    mark_failed,
    mark_succeeded,
)
from utils.response import error_response


logger = logging.getLogger(__name__)

IDEMPOTENCY_HEADER = "X-Idempotency-Key"
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
MAX_REQUEST_BODY_BYTES = 1024 * 1024
RETRY_AFTER_SECONDS = 1


def is_replayable_success(status_code: int, body: bytes) -> bool:
    """Persist only 2xx responses that are not JSON error envelopes."""
    if not (200 <= status_code < 300):
        return False
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return True
    if not isinstance(payload, dict):
        return True
    code = payload.get("code")
    return not (isinstance(code, int) and code != CODE_SUCCESS)


@dataclass(frozen=True, slots=True)
class IdempotencyContext:
    durable_key: str
    payload_hash: str
    claim_token: str


class IdempotencyReplay(Exception):
    """Internal signal emitted only after route authorization succeeds."""

    def __init__(self, response: StoredResponse) -> None:
        self.response = response
        super().__init__("authorized idempotency replay")


class IdempotencyProtocolError(Exception):
    """Internal protocol error rendered by the idempotency finalizer."""

    def __init__(
        self,
        code: int,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.headers = headers
        super().__init__(f"idempotency protocol error {code}")


def build_durable_key(caller_scope: str, key: str) -> str:
    identity = f"{caller_scope}\n{key}".encode()
    return hashlib.sha256(identity).hexdigest()


def build_payload_hash(
    request: Request,
    body: bytes,
    caller_scope: str,
) -> str:
    query = request.url.query
    identity = (
        f"{request.method.upper()}\n"
        f"{request.url.path}\n"
        f"{query}\n"
        f"{caller_scope}\n"
    ).encode()
    return hashlib.sha256(identity + body).hexdigest()



async def claim_idempotency(
    request: Request,
    caller_scope: str,
    processing_lease_seconds: int,
) -> None:
    """Claim an optional key after the caller's authorization has succeeded."""
    if request.method.upper() not in WRITE_METHODS:
        return

    key = request.headers.get(IDEMPOTENCY_HEADER)
    if not key:
        return

    existing = getattr(request.state, "idempotency_context", None)
    if existing is not None:
        return

    valid, _reason = validate_idempotency_key(key)
    if not valid:
        raise IdempotencyProtocolError(CODE_IDEMPOTENCY_KEY_INVALID)

    body = await request.body()
    if len(body) > MAX_REQUEST_BODY_BYTES:
        raise IdempotencyProtocolError(CODE_REQUEST_BODY_TOO_LARGE)

    payload_hash = build_payload_hash(request, body, caller_scope)
    durable_key = build_durable_key(caller_scope, key)
    try:
        claim = claim_request(
            durable_key,
            payload_hash,
            processing_lease_seconds,
        )
    except Exception as exc:
        logger.exception(
            "Idempotency claim failed: exception=%s",
            type(exc).__name__,
        )
        raise IdempotencyProtocolError(CODE_DATABASE_ERROR) from exc

    if claim.kind == "MISMATCH":
        raise IdempotencyProtocolError(CODE_IDEMPOTENCY_PAYLOAD_MISMATCH)
    if claim.kind == "IN_PROGRESS":
        raise IdempotencyProtocolError(
            CODE_IDEMPOTENCY_IN_PROGRESS,
            headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
        )
    if claim.kind == "REPLAY":
        if claim.response is None:
            raise IdempotencyProtocolError(CODE_DATABASE_ERROR)
        raise IdempotencyReplay(claim.response)
    if claim.claim_token is None:
        raise IdempotencyProtocolError(CODE_DATABASE_ERROR)

    request.state.idempotency_context = IdempotencyContext(
        durable_key=durable_key,
        payload_hash=payload_hash,
        claim_token=claim.claim_token,
    )

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Finalize claimed writes after materializing their complete response.

    Keyed responses, including streaming responses, are buffered before delivery so
    the database can replay the exact representation. Background work stays on the
    owner response and is not persisted or repeated during replay.
    """

    def __init__(self, app, ttl_hours: int = 24):
        super().__init__(app)
        self.ttl_hours = ttl_hours

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            response = await call_next(request)
        except asyncio.CancelledError:
            # Cancellation and timeout are ambiguous: the route may have committed
            # before control returned here. Keep PROCESSING so immediate retries stay
            # quarantined until the ownership lease expires.
            raise
        except Exception:
            context = getattr(request.state, "idempotency_context", None)
            if context is not None:
                self._finalize_failed(
                    context.durable_key,
                    context.payload_hash,
                    context.claim_token,
                )
            raise

        context = getattr(request.state, "idempotency_context", None)
        if context is None:
            return response

        body_bytes = await self._read_body(response)
        rebuilt = self._rebuild_response(response, body_bytes)
        if is_replayable_success(response.status_code, body_bytes):
            headers = safe_response_headers(dict(response.headers))
            stored = StoredResponse(
                http_status=response.status_code,
                body=body_bytes,
                media_type=(
                    response.media_type or response.headers.get("content-type")
                ),
                headers=headers,
            )
            try:
                mark_succeeded(
                    context.durable_key,
                    context.payload_hash,
                    context.claim_token,
                    http_status=stored.http_status,
                    body=stored.body,
                    media_type=stored.media_type,
                    headers=stored.headers,
                    retention_hours=self.ttl_hours,
                )
            except Exception as exc:
                logger.exception(
                    "Idempotency success finalization failed: exception=%s",
                    type(exc).__name__,
                )
                # Do not release ownership after a route may have committed side
                # effects. The PROCESSING lease quarantines immediate retries;
                # route and finalization transactions are not jointly atomic.
                return self._error(CODE_DATABASE_ERROR)
            await cache_succeeded_response(
                context.durable_key,
                stored,
                self.ttl_hours,
            )
        else:
            self._finalize_failed(
                context.durable_key,
                context.payload_hash,
                context.claim_token,
            )
        return rebuilt

    @staticmethod
    async def _read_body(response: Response) -> bytes:
        if hasattr(response, "body_iterator"):
            chunks = [chunk async for chunk in response.body_iterator]
            return b"".join(chunks)
        body = response.body
        return body if isinstance(body, bytes) else str(body).encode("utf-8")

    @staticmethod
    def _rebuild_response(response: Response, body: bytes) -> Response:
        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() != "content-length"
        }
        return Response(
            content=body,
            status_code=response.status_code,
            media_type=response.media_type,
            headers=headers,
            background=response.background,
        )

    @staticmethod
    def replay_response(stored: StoredResponse) -> Response:
        return Response(
            content=stored.body,
            status_code=stored.http_status,
            media_type=stored.media_type,
            headers=stored.headers,
        )

    @staticmethod
    def protocol_error_response(
        code: int,
        *,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        return IdempotencyMiddleware._error(code, headers=headers)

    @staticmethod
    def _error(code: int, *, headers: dict[str, str] | None = None) -> JSONResponse:
        definition = get_error_definition(code)
        return JSONResponse(
            status_code=definition.http_status,
            content=error_response(definition.code, definition.message),
            headers=safe_response_headers(headers),
        )

    @staticmethod
    def _finalize_failed(key: str, payload_hash: str, claim_token: str | None) -> None:
        if claim_token is None:
            return
        try:
            mark_failed(key, payload_hash, claim_token)
        except Exception as exc:
            logger.exception(
                "Idempotency failure finalization failed: exception=%s",
                type(exc).__name__,
            )

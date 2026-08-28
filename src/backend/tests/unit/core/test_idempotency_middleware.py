"""Idempotency response lifecycle tests."""

import asyncio

import pytest
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import StreamingResponse

from core.error_codes import CODE_INTERNAL_ERROR
from middleware.idempotency import (
    IdempotencyContext,
    IdempotencyMiddleware,
    is_replayable_success,
)
from utils.idempotency_store import StoredResponse
from utils.response import error_response


@pytest.mark.asyncio
async def test_keyed_stream_is_materialized_and_background_stays_owner_only(
    monkeypatch,
):
    persisted = {}
    background_calls = 0

    async def stream():
        yield b"first-"
        yield b"second"

    async def run_background():
        nonlocal background_calls
        background_calls += 1

    def capture_success(_key, _payload_hash, _claim_token, **kwargs):
        persisted.update(kwargs)

    async def ignore_cache(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        "middleware.idempotency.mark_succeeded",
        capture_success,
    )
    monkeypatch.setattr(
        "middleware.idempotency.cache_succeeded_response",
        ignore_cache,
    )

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/stream",
            "headers": [],
        }
    )
    request.state.idempotency_context = IdempotencyContext(
        durable_key="durable-key",
        payload_hash="payload-hash",
        claim_token="claim-token",
    )

    async def call_next(_request):
        return StreamingResponse(
            stream(),
            media_type="text/plain",
            headers={"X-Request-ID": "stream-request"},
            background=BackgroundTask(run_background),
        )

    middleware = IdempotencyMiddleware(lambda *_args: None)
    response = await middleware.dispatch(request, call_next)

    assert response.body == b"first-second"
    assert persisted["body"] == b"first-second"
    assert persisted["media_type"] == "text/plain"
    assert persisted["headers"] == {"x-request-id": "stream-request"}
    assert response.background is not None
    assert background_calls == 0

    await response.background()
    assert background_calls == 1

    replay = middleware.replay_response(
        StoredResponse(
            http_status=persisted["http_status"],
            body=persisted["body"],
            media_type=persisted["media_type"],
            headers=persisted["headers"],
        )
    )
    assert replay.body == b"first-second"
    assert replay.background is None
    assert background_calls == 1


@pytest.mark.asyncio
async def test_cancellation_keeps_processing_claim_quarantined(monkeypatch):
    failure_finalizations = []
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/cancelled",
            "headers": [],
        }
    )
    request.state.idempotency_context = IdempotencyContext(
        durable_key="durable-key",
        payload_hash="payload-hash",
        claim_token="claim-token",
    )

    def capture_failure(*args):
        failure_finalizations.append(args)

    async def call_next(_request):
        raise asyncio.CancelledError

    monkeypatch.setattr(
        "middleware.idempotency.mark_failed",
        capture_failure,
    )

    middleware = IdempotencyMiddleware(lambda *_args: None)
    with pytest.raises(asyncio.CancelledError):
        await middleware.dispatch(request, call_next)

    assert failure_finalizations == []


@pytest.mark.parametrize(
    ("status_code", "body", "expected"),
    [
        (200, b"{\"code\": 0, \"message\": \"success\"}", True),
        (201, b"{\"code\": 0, \"data\": {\"id\": 1}}", True),
        (200, b"not-json", True),
        (200, b"\x00binary", True),
        (200, b"{\"code\": 50000, \"message\": \"boom\"}", False),
        (200, b"{\"code\": 40001, \"message\": \"not found\"}", False),
        (409, b"{\"code\": 0}", False),
        (500, b"internal", False),
    ],
)
def test_is_replayable_success_rejects_error_envelopes(status_code, body, expected):
    assert is_replayable_success(status_code, body) is expected


@pytest.mark.asyncio
async def test_http_200_error_envelope_is_not_finalized_as_success(monkeypatch):
    successes = []
    failures = []

    def capture_success(*args, **kwargs):
        successes.append((args, kwargs))

    def capture_failure(*args):
        failures.append(args)

    monkeypatch.setattr("middleware.idempotency.mark_succeeded", capture_success)
    monkeypatch.setattr("middleware.idempotency.mark_failed", capture_failure)

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/envelope",
            "headers": [],
        }
    )
    request.state.idempotency_context = IdempotencyContext(
        durable_key="durable-key",
        payload_hash="payload-hash",
        claim_token="claim-token",
    )

    async def call_next(_request):
        return JSONResponse(
            status_code=200,
            content=error_response(CODE_INTERNAL_ERROR, "simulated envelope failure"),
        )

    middleware = IdempotencyMiddleware(lambda *_args: None)
    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    assert response.body.find(str(CODE_INTERNAL_ERROR).encode()) != -1
    assert successes == []
    assert failures == [("durable-key", "payload-hash", "claim-token")]

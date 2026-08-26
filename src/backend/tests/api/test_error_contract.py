import asyncio

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from core.error_codes import CODE_STATE_CONFLICT
from core.errors import DomainError
from main import (
    database_exception_handler,
    domain_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from middleware.timeout import TimeoutMiddleware


class Payload(BaseModel):
    count: int


def build_app(*, timeout: float | None = None) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    if timeout is not None:
        app.add_middleware(TimeoutMiddleware, timeout_seconds=timeout)

    @app.get("/domain")
    async def domain():
        raise DomainError(
            CODE_STATE_CONFLICT,
            meta={"request_id": "req-1", "secret": "hidden"},
        )

    @app.get("/legacy-string")
    async def legacy_string():
        raise HTTPException(
            status_code=401,
            detail="arbitrary postgresql://user:secret@db token",
            headers={"WWW-Authenticate": "Bearer", "X-Unsafe": "hidden"},
        )

    @app.get("/legacy-expired")
    async def legacy_expired():
        raise HTTPException(status_code=401, detail="Token expired")

    @app.get("/legacy-dict")
    async def legacy_dict():
        raise HTTPException(
            status_code=409,
            detail={
                "code": CODE_STATE_CONFLICT,
                "message": "postgresql://user:secret@db",
                "meta": {"request_id": "req-2", "secret": "hidden"},
                "raw": "private-key",
            },
            headers={"Retry-After": "2"},
        )

    @app.get("/legacy-malformed")
    async def legacy_malformed():
        raise HTTPException(
            status_code=403,
            detail={"code": 99999, "message": "jwt-secret", "private": "value"},
        )

    @app.post("/validate")
    async def validate(payload: Payload):
        return payload

    @app.get("/database")
    async def database():
        raise SQLAlchemyError("SELECT password FROM users postgresql://user:secret@db")

    @app.get("/unknown")
    async def unknown():
        raise RuntimeError("jwt.cookie.private-key.third-party-body")

    @app.get("/slow")
    async def slow():
        await asyncio.sleep(0.05)
        return {"ok": True}

    return app


def assert_envelope(response, *, status: int, code: int):
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"code", "message", "data", "meta"}
    assert body["code"] == code
    assert body["data"] is None
    return body


def test_domain_error_contract_and_meta_whitelist():
    with TestClient(build_app()) as client:
        response = client.get("/domain")
    body = assert_envelope(response, status=409, code=40901)
    assert body["meta"] == {"request_id": "req-1"}
    assert "secret" not in response.text


def test_legacy_string_uses_safe_message_and_preserves_auth_header():
    with TestClient(build_app()) as client:
        response = client.get("/legacy-string")
    body = assert_envelope(response, status=401, code=40100)
    assert body["message"] == "未登录或 Token 无效"
    assert response.headers["www-authenticate"] == "Bearer"
    assert "x-unsafe" not in response.headers
    assert "postgresql" not in response.text


def test_expired_token_alias_remains_compatible():
    with TestClient(build_app()) as client:
        response = client.get("/legacy-expired")
    assert_envelope(response, status=401, code=40101)


def test_legacy_dict_requires_registered_status_and_whitelists_meta():
    with TestClient(build_app()) as client:
        response = client.get("/legacy-dict")
    body = assert_envelope(response, status=409, code=40901)
    assert body["message"] == "资源状态已变化，当前操作不能继续"
    assert body["meta"] == {"request_id": "req-2"}
    assert response.headers["retry-after"] == "2"
    assert "secret" not in response.text
    assert "private-key" not in response.text


def test_malformed_detail_fails_closed():
    with TestClient(build_app()) as client:
        response = client.get("/legacy-malformed")
    body = assert_envelope(response, status=403, code=40300)
    assert body["message"] == "权限不足"
    assert "jwt-secret" not in response.text


def test_validation_errors_are_bounded_and_do_not_echo_input():
    sentinel = "postgresql://user:secret@db"
    with TestClient(build_app()) as client:
        response = client.post("/validate", json={"count": sentinel})
    body = assert_envelope(response, status=422, code=40000)
    assert body["meta"]["errors"]
    assert set(body["meta"]["errors"][0]) == {"loc", "type", "msg"}
    assert sentinel not in response.text
    assert "input" not in response.text


@pytest.mark.parametrize(
    ("path", "expected_code", "sentinels"),
    [
        ("/database", 50001, ["SELECT password", "postgresql://", "secret"]),
        ("/unknown", 50000, ["jwt.cookie", "private-key", "third-party-body"]),
    ],
)
def test_internal_errors_are_sanitized(path, expected_code, sentinels):
    with TestClient(build_app(), raise_server_exceptions=False) as client:
        response = client.get(path)
    assert_envelope(response, status=500, code=expected_code)
    for sentinel in sentinels:
        assert sentinel not in response.text


def test_timeout_uses_registered_error_envelope():
    with TestClient(build_app(timeout=0.001)) as client:
        response = client.get("/slow")
    body = assert_envelope(response, status=504, code=50400)
    assert body["message"] == "请求超时，请稍后重试"

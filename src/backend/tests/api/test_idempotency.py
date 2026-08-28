"""数据库幂等中间件 API 契约测试。"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from config.database import settings
from core.error_codes import CODE_INTERNAL_ERROR
from core.errors import DomainError
from utils.response import error_response
from models.idempotency_record import IdempotencyRecord
from services.node_service import NodeService
from utils import cache
from utils.idempotency_store import ClaimResult


@pytest.fixture(autouse=True)
def _clear_cache():
    """每个测试前后清空内存缓存，避免跨测试污染"""
    cache.memory_cache.clear()
    yield
    cache.memory_cache.clear()


def _expired_token(username: str, role: str) -> str:
    return jwt.encode(
        {
            "sub": username,
            "role": role,
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def _idempotency_record_count(db_session) -> int:
    db_session.expire_all()
    return db_session.query(IdempotencyRecord).count()


@pytest.mark.api
class TestIdempotencyMiddleware:
    def _auth_headers(self, client, test_users):
        resp = client.post(
            "/api/auth/login",
            json={"username": "dispatcher", "password": "123456"},
        )
        token = resp.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_duplicate_post_returns_cached_response(self, client, test_users):
        """携带 X-Idempotency-Key 的重复 POST 返回首次缓存响应"""
        headers = self._auth_headers(client, test_users)
        payload = {
            "node_code": "SC099",
            "name": "缓存测试节点",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        }
        idem_headers = {**headers, "X-Idempotency-Key": "test-idem-001"}

        r1 = client.post("/api/nodes/storage-centers", json=payload, headers=idem_headers)
        r2 = client.post("/api/nodes/storage-centers", json=payload, headers=idem_headers)

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()
        # 数据库是正确性来源，幂等协议不得写入进程内存 fallback。
        assert not any(k.startswith("idem:") for k in cache.memory_cache._store)

    def test_without_key_not_deduplicated(self, client, test_users):
        """不携带 X-Idempotency-Key 时不走幂等，重复创建返回业务冲突"""
        headers = self._auth_headers(client, test_users)
        payload = {
            "node_code": "SC098",
            "name": "重复测试节点",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        }
        r1 = client.post("/api/nodes/storage-centers", json=payload, headers=headers)
        r2 = client.post("/api/nodes/storage-centers", json=payload, headers=headers)
        assert r1.json()["code"] == 0
        assert r2.json()["code"] != 0

    @pytest.mark.parametrize(
        ("path", "payload"),
        [
            ("/api/schedule/global", {}),
            ("/api/schedule/confirm/missing-schedule", None),
            ("/api/simulation/confirm-arrival", {}),
            ("/api/simulation/confirm-arrival-batch", {}),
            ("/api/ai/suggestions/1/confirm", None),
            ("/api/ai/suggestions/1/reject", None),
            ("/api/exceptions/missing-event/replan", {}),
            ("/api/exceptions/replan/batch", {}),
        ],
    )
    def test_required_endpoints_reject_missing_key(
        self,
        client,
        test_users,
        path,
        payload,
    ):
        headers = self._auth_headers(client, test_users)

        response = client.post(path, json=payload, headers=headers)

        assert response.status_code == 400
        assert response.json()["code"] == 40021

    @pytest.mark.parametrize(
        ("path", "payload"),
        [
            ("/api/schedule/global", {}),
            ("/api/schedule/confirm/missing-schedule", None),
            ("/api/simulation/confirm-arrival", {}),
            ("/api/simulation/confirm-arrival-batch", {}),
            ("/api/ai/suggestions/1/confirm", None),
            ("/api/ai/suggestions/1/reject", None),
            ("/api/exceptions/missing-event/replan", {}),
            ("/api/exceptions/replan/batch", {}),
        ],
    )
    def test_required_endpoints_preserve_auth_precedence(
        self,
        client,
        path,
        payload,
    ):
        response = client.post(path, json=payload)

        assert response.status_code == 401
        assert response.json()["code"] == 40100

    @pytest.mark.parametrize(
        ("path", "payload"),
        [
            ("/api/schedule/global", {}),
            ("/api/schedule/confirm/missing-schedule", None),
            ("/api/simulation/confirm-arrival", {}),
            ("/api/simulation/confirm-arrival-batch", {}),
            ("/api/ai/suggestions/1/confirm", None),
            ("/api/ai/suggestions/1/reject", None),
            ("/api/exceptions/missing-event/replan", {}),
            ("/api/exceptions/replan/batch", {}),
        ],
    )
    def test_required_endpoints_preserve_authorization_precedence(
        self,
        client,
        test_users,
        path,
        payload,
    ):
        manager_login = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        headers = {
            "Authorization": (
                "Bearer " + manager_login.json()["data"]["access_token"]
            )
        }

        response = client.post(path, json=payload, headers=headers)

        assert response.status_code == 403
        assert response.json()["code"] == 40300

    def test_invalid_key_is_rejected(self, client, test_users):
        headers = {
            **self._auth_headers(client, test_users),
            "X-Idempotency-Key": "bad key",
        }

        response = client.post("/api/nodes/storage-centers", json={}, headers=headers)

        assert response.status_code == 400
        assert response.json()["code"] == 40020

    def test_same_key_different_payload_is_rejected(self, client, test_users):
        headers = {
            **self._auth_headers(client, test_users),
            "X-Idempotency-Key": "test-idem-mismatch",
        }
        payload = {
            "node_code": "SC097",
            "name": "指纹测试节点",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        }
        first = client.post("/api/nodes/storage-centers", json=payload, headers=headers)
        changed = {**payload, "name": "不同请求体"}

        second = client.post("/api/nodes/storage-centers", json=changed, headers=headers)

        assert first.status_code == 200
        assert second.status_code == 409
        assert second.json()["code"] == 40903

    def test_body_larger_than_one_mib_is_rejected(self, client, test_users):
        headers = {
            **self._auth_headers(client, test_users),
            "X-Idempotency-Key": "test-idem-large-body",
            "Content-Type": "application/octet-stream",
        }

        response = client.post(
            "/api/nodes/storage-centers",
            content=b"x" * (1024 * 1024 + 1),
            headers=headers,
        )

        assert response.status_code == 413
        assert response.json()["code"] == 41300  # 第二次创建被业务拒绝


    def test_replay_requires_current_active_user(
        self,
        client,
        db_session,
        test_users,
    ):
        headers = {
            **self._auth_headers(client, test_users),
            "X-Idempotency-Key": "test-idem-inactive-user",
        }
        payload = {
            "node_code": "SC096",
            "name": "停用账号重放测试",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        }

        first = client.post(
            "/api/nodes/storage-centers",
            json=payload,
            headers=headers,
        )
        test_users["dispatcher"].is_active = False
        db_session.commit()

        replay = client.post(
            "/api/nodes/storage-centers",
            json=payload,
            headers=headers,
        )

        assert first.status_code == 200
        assert replay.status_code == 401
        assert replay.json()["code"] == 40100

    def test_replay_requires_current_dispatcher_role(
        self,
        client,
        db_session,
        test_users,
    ):
        headers = {
            **self._auth_headers(client, test_users),
            "X-Idempotency-Key": "test-idem-revoked-role",
        }
        payload = {
            "node_code": "SC095",
            "name": "角色撤销重放测试",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        }

        first = client.post(
            "/api/nodes/storage-centers",
            json=payload,
            headers=headers,
        )
        test_users["dispatcher"].role = "manager"
        db_session.commit()

        replay = client.post(
            "/api/nodes/storage-centers",
            json=payload,
            headers=headers,
        )

        assert first.status_code == 200
        assert replay.status_code == 403
        assert replay.json()["code"] == 40300

    @pytest.mark.parametrize(
        ("case", "authorization", "expected_code"),
        [
            ("missing", None, 40100),
            ("invalid", "Bearer invalid-token", 40100),
            ("expired", "expired", 40101),
        ],
    )
    def test_keyed_write_authenticates_before_claim(
        self,
        client,
        db_session,
        test_users,
        case,
        authorization,
        expected_code,
    ):
        headers = {"X-Idempotency-Key": f"auth-first-{case}"}
        if authorization == "expired":
            headers["Authorization"] = (
                "Bearer "
                + _expired_token("dispatcher", "dispatcher")
            )
        elif authorization is not None:
            headers["Authorization"] = authorization

        before = _idempotency_record_count(db_session)
        response = client.post(
            "/api/nodes/storage-centers",
            json={},
            headers=headers,
        )

        assert response.status_code == 401
        assert response.json()["code"] == expected_code
        assert _idempotency_record_count(db_session) == before

    def test_same_client_key_is_scoped_per_authenticated_user(
        self,
        client,
        db_session,
        test_users,
    ):
        dispatcher_headers = {
            **self._auth_headers(client, test_users),
            "X-Idempotency-Key": "shared-client-key",
        }
        test_users["manager"].role = "admin"
        db_session.commit()
        manager_login = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "123456"},
        )
        manager_headers = {
            "Authorization": (
                "Bearer " + manager_login.json()["data"]["access_token"]
            ),
            "X-Idempotency-Key": "shared-client-key",
        }

        first = client.post(
            "/api/nodes/storage-centers",
            json={
                "node_code": "SC094",
                "name": "调度员命名空间",
                "location": "测试",
                "latitude": 30.5,
                "longitude": 114.3,
                "capacity": 500.0,
            },
            headers=dispatcher_headers,
        )
        second = client.post(
            "/api/nodes/storage-centers",
            json={
                "node_code": "SC093",
                "name": "管理员命名空间",
                "location": "测试",
                "latitude": 30.6,
                "longitude": 114.4,
                "capacity": 600.0,
            },
            headers=manager_headers,
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["data"]["node_code"] == "SC094"
        assert second.json()["data"]["node_code"] == "SC093"
        assert _idempotency_record_count(db_session) == 2

    def test_login_does_not_persist_or_replay_idempotency_key(
        self,
        client,
        db_session,
        test_users,
    ):
        headers = {"X-Idempotency-Key": "public-login-key"}

        first = client.post(
            "/api/auth/login",
            json={"username": "dispatcher", "password": "123456"},
            headers=headers,
        )
        test_users["dispatcher"].is_active = False
        db_session.commit()
        second = client.post(
            "/api/auth/login",
            json={"username": "dispatcher", "password": "123456"},
            headers=headers,
        )

        assert first.json()["code"] == 0
        assert second.json()["code"] == 40100
        assert _idempotency_record_count(db_session) == 0


def test_in_progress_returns_retry_after_without_running_route(
    client,
    monkeypatch,
    test_users,
):
    headers = {
        **TestIdempotencyMiddleware()._auth_headers(client, test_users),
        "X-Idempotency-Key": "test-idem-in-progress",
    }
    route_calls = 0

    async def should_not_run(*_args, **_kwargs):
        nonlocal route_calls
        route_calls += 1
        raise AssertionError("route must not execute for an in-progress claim")

    monkeypatch.setattr(
        "middleware.idempotency.claim_request",
        lambda *_args, **_kwargs: ClaimResult("IN_PROGRESS"),
    )
    monkeypatch.setattr(NodeService, "create_storage_center", should_not_run)

    response = client.post(
        "/api/nodes/storage-centers",
        json={},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == 40902
    assert response.headers["retry-after"] == "1"
    assert route_calls == 0


def test_successful_replay_executes_route_once(
    client,
    monkeypatch,
    test_users,
):
    headers = {
        **TestIdempotencyMiddleware()._auth_headers(client, test_users),
        "X-Idempotency-Key": "test-idem-route-once",
    }
    payload = {
        "node_code": "SC091",
        "name": "单次执行测试",
        "location": "测试",
        "latitude": 30.5,
        "longitude": 114.3,
        "capacity": 500.0,
    }
    original = NodeService.create_storage_center
    route_calls = 0

    async def counted(*args, **kwargs):
        nonlocal route_calls
        route_calls += 1
        return await original(*args, **kwargs)

    monkeypatch.setattr(NodeService, "create_storage_center", counted)

    first = client.post(
        "/api/nodes/storage-centers",
        json=payload,
        headers=headers,
    )
    replay = client.post(
        "/api/nodes/storage-centers",
        json=payload,
        headers=headers,
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.content == replay.content
    assert route_calls == 1


def test_success_finalization_failure_quarantines_immediate_retry(
    client,
    monkeypatch,
    test_users,
):
    headers = {
        **TestIdempotencyMiddleware()._auth_headers(client, test_users),
        "X-Idempotency-Key": "test-idem-finalization-failure",
    }
    payload = {
        "node_code": "SC090",
        "name": "终态写入失败隔离测试",
        "location": "测试",
        "latitude": 30.5,
        "longitude": 114.3,
        "capacity": 500.0,
    }
    original = NodeService.create_storage_center
    route_calls = 0

    async def counted(*args, **kwargs):
        nonlocal route_calls
        route_calls += 1
        return await original(*args, **kwargs)

    def fail_finalization(*_args, **_kwargs):
        raise RuntimeError("simulated finalization failure")

    monkeypatch.setattr(NodeService, "create_storage_center", counted)
    monkeypatch.setattr(
        "middleware.idempotency.mark_succeeded",
        fail_finalization,
    )

    first = client.post(
        "/api/nodes/storage-centers",
        json=payload,
        headers=headers,
    )
    immediate_retry = client.post(
        "/api/nodes/storage-centers",
        json=payload,
        headers=headers,
    )

    assert first.status_code == 500
    assert first.json()["code"] == 50001
    assert immediate_retry.status_code == 409
    assert immediate_retry.json()["code"] == 40902
    assert immediate_retry.headers["retry-after"] == "1"
    assert route_calls == 1


def test_exception_response_releases_claim_for_retry(
    client,
    monkeypatch,
    test_users,
):
    headers = {
        **TestIdempotencyMiddleware()._auth_headers(client, test_users),
        "X-Idempotency-Key": "test-idem-exception-retry",
    }
    route_calls = 0

    async def fail(*_args, **_kwargs):
        nonlocal route_calls
        route_calls += 1
        raise DomainError(CODE_INTERNAL_ERROR)

    monkeypatch.setattr(NodeService, "create_storage_center", fail)

    first = client.post(
        "/api/nodes/storage-centers",
        json={
            "node_code": "SC092",
            "name": "失败重试测试",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        },
        headers=headers,
    )
    second = client.post(
        "/api/nodes/storage-centers",
        json={
            "node_code": "SC092",
            "name": "失败重试测试",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        },
        headers=headers,
    )

    assert first.status_code == 500
    assert second.status_code == 500
    assert first.json()["code"] == CODE_INTERNAL_ERROR
    assert second.json()["code"] == CODE_INTERNAL_ERROR
    assert route_calls == 2


def test_http_200_error_envelope_releases_claim_for_retry(
    client,
    monkeypatch,
    test_users,
):
    headers = {
        **TestIdempotencyMiddleware()._auth_headers(client, test_users),
        "X-Idempotency-Key": "test-idem-http200-envelope-retry",
    }
    route_calls = 0

    async def fail(*_args, **_kwargs):
        nonlocal route_calls
        route_calls += 1
        return error_response(CODE_INTERNAL_ERROR, "simulated envelope failure")

    monkeypatch.setattr(NodeService, "create_storage_center", fail)

    payload = {
        "node_code": "SC089",
        "name": "HTTP200 envelope retry",
        "location": "test",
        "latitude": 30.5,
        "longitude": 114.3,
        "capacity": 500.0,
    }
    first = client.post("/api/nodes/storage-centers", json=payload, headers=headers)
    second = client.post("/api/nodes/storage-centers", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["code"] == CODE_INTERNAL_ERROR
    assert second.json()["code"] == CODE_INTERNAL_ERROR
    assert route_calls == 2

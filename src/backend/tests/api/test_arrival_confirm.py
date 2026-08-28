"""
到货确认 API 鉴权测试（T-02）

原 3 个端点（confirm-arrival / confirm-arrival-batch / arrival-packages）仅依赖
Depends(get_db)，任何人可确认送达/领取包裹。修复后要求 dispatcher/admin 角色：

- 无 token → 401
- viewer（无操作权限角色）→ 403
"""
import pytest

from models.user import User
from services.auth_service import get_password_hash


@pytest.fixture
def viewer_token(client, db_session):
    """创建 viewer 用户并通过登录获取 JWT（login 路线与真实使用一致）"""
    user = User(
        username="viewer",
        password_hash=get_password_hash("123456"),
        role="viewer",
        display_name="访客",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"username": "viewer", "password": "123456"},
    )
    assert login_resp.status_code == 200
    return login_resp.json()["data"]["access_token"]


@pytest.fixture
def dispatcher_token(client, db_session):
    """创建 dispatcher 用户并登录获取 JWT"""
    user = User(
        username="dispatcher",
        password_hash=get_password_hash("123456"),
        role="dispatcher",
        display_name="调度员",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"username": "dispatcher", "password": "123456"},
    )
    assert login_resp.status_code == 200
    return login_resp.json()["data"]["access_token"]


def _confirm_payload():
    return {
        "schedule_code": "GS20260609001",
        "package_code": "PKG001",
        "is_normal": True,
    }


def _batch_payload():
    return {
        "schedule_code": "GS20260609001",
        "confirmations": [
            {"package_code": "PKG001", "is_normal": True},
        ],
    }


@pytest.mark.api
class TestArrivalConfirmAuth:
    """鉴权校验：无 token 401、viewer 403"""

    def test_confirm_arrival_requires_auth(self, client):
        """无 token 调 confirm-arrival → 401"""
        response = client.post("/api/simulation/confirm-arrival", json=_confirm_payload())
        assert response.status_code == 401

    def test_confirm_arrival_rejects_viewer(self, client, viewer_token):
        """viewer 调 confirm-arrival → 403"""
        response = client.post(
            "/api/simulation/confirm-arrival",
            json=_confirm_payload(),
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403

    def test_confirm_arrival_batch_requires_auth(self, client):
        """无 token 调 confirm-arrival-batch → 401"""
        response = client.post("/api/simulation/confirm-arrival-batch", json=_batch_payload())
        assert response.status_code == 401

    def test_confirm_arrival_batch_rejects_viewer(self, client, viewer_token):
        """viewer 调 confirm-arrival-batch → 403"""
        response = client.post(
            "/api/simulation/confirm-arrival-batch",
            json=_batch_payload(),
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403

    def test_arrival_packages_requires_auth(self, client):
        """无 token 调 arrival-packages → 401"""
        response = client.get(
            "/api/simulation/arrival-packages",
            params={"schedule_code": "GS20260609001"},
        )
        assert response.status_code == 401

    def test_arrival_packages_rejects_viewer(self, client, viewer_token):
        """viewer 调 arrival-packages → 403"""
        response = client.get(
            "/api/simulation/arrival-packages",
            params={"schedule_code": "GS20260609001"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403


@pytest.mark.api
class TestArrivalConfirmAuthorized:
    """dispatcher 鉴权通过（业务结果不在此类断言）"""

    def test_confirm_arrival_dispatcher_passes_auth(self, client, dispatcher_token):
        """dispatcher 调 confirm-arrival → 非 401/403（schedule 不存在时业务 code!=0 但仍返回 200 容器）"""
        response = client.post(
            "/api/simulation/confirm-arrival",
            json=_confirm_payload(),
            headers={
                "Authorization": f"Bearer {dispatcher_token}",
                "X-Idempotency-Key": "r2-02a-arrival-key",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert set(body) >= {"code", "message", "data"}
        assert body["code"] == 50000
        assert body["data"] is None
        assert body["message"] == "到货确认失败"
        assert "PKG001" not in response.text
        assert "detail" not in body


@pytest.mark.api
class TestArrivalConfirmErrorSanitization:
    """存量 HTTP 200 业务错误容器保留，但不再回传异常原文。"""

    def test_batch_confirm_hides_exception_text(self, client, dispatcher_token, monkeypatch):
        sentinel = "postgresql://user:secret@db"

        def _boom(*args, **kwargs):
            raise RuntimeError(sentinel)

        monkeypatch.setattr(
            "api.arrival_confirm.ArrivalConfirmService.confirm_arrival_batch",
            _boom,
        )
        response = client.post(
            "/api/simulation/confirm-arrival-batch",
            json=_batch_payload(),
            headers={
                "Authorization": f"Bearer {dispatcher_token}",
                "X-Idempotency-Key": "r2-02a-arrival-key",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 50000
        assert body["data"] is None
        assert body["message"] == "批量到货确认失败"
        assert sentinel not in response.text

    def test_arrival_packages_hides_exception_text(self, client, dispatcher_token, monkeypatch):
        sentinel = "jwt.cookie.private-key"

        def _boom(*args, **kwargs):
            raise RuntimeError(sentinel)

        monkeypatch.setattr(
            "api.arrival_confirm.ArrivalConfirmService.get_arrival_packages",
            _boom,
        )
        response = client.get(
            "/api/simulation/arrival-packages",
            params={"schedule_code": "GS20260609001"},
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 50000
        assert body["data"] is None
        assert body["message"] == "查询到站包裹失败"
        assert sentinel not in response.text

"""
通知 API 测试（T3-2）

测试端点：
- GET  /api/notifications/config - 获取通知配置
- PUT  /api/notifications/config - 运行时切换渠道
- POST /api/notifications/test   - 测试通知
"""
import pytest

from models.notification_config import NotificationConfig


@pytest.fixture
def auth_headers(client, test_users):
    """认证头（调度员）"""
    response = client.post("/api/auth/login", json={
        "username": "dispatcher",
        "password": "123456",
    })
    assert response.status_code == 200, f"登录失败: {response.json()}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(client, test_users):
    """认证头（管理者，无调度权限）"""
    response = client.post("/api/auth/login", json={
        "username": "manager",
        "password": "123456",
    })
    assert response.status_code == 200, f"登录失败: {response.json()}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.api
@pytest.mark.phase3
class TestNotificationConfigAPI:
    """通知配置 API"""

    def test_get_config_default(self, client, auth_headers):
        """默认配置：dev 环境启用 console"""
        response = client.get("/api/notifications/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "console" in data["data"]["enabled_channels"]
        assert data["data"]["environment"] == "dev"

    def test_get_config_requires_auth(self, client):
        """未登录访问返回 401"""
        response = client.get("/api/notifications/config")
        assert response.status_code == 401

    def test_put_config_switch_channels(self, client, auth_headers):
        """运行时切换渠道（验收标准）"""
        response = client.put(
            "/api/notifications/config",
            json={
                "enabled_channels": ["email", "wechat_work"],
                "email_recipients": ["ops@example.com", "ops2@example.com"],
                "wechat_webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["enabled_channels"] == ["email", "wechat_work"]
        assert data["data"]["email_recipients"] == ["ops@example.com", "ops2@example.com"]

        # 落库验证
        cfg = client.app.dependency_overrides
        from config.database import get_db
        # 通过再 GET 一次验证持久化
        resp2 = client.get("/api/notifications/config", headers=auth_headers)
        assert resp2.status_code == 200
        d2 = resp2.json()["data"]
        assert d2["enabled_channels"] == ["email", "wechat_work"]

    def test_put_config_invalid_channel(self, client, auth_headers):
        """无效渠道 → 422"""
        response = client.put(
            "/api/notifications/config",
            json={"enabled_channels": ["sms"]},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_put_config_requires_dispatcher(self, client, manager_headers):
        """管理者无调度权限 → 403"""
        response = client.put(
            "/api/notifications/config",
            json={"enabled_channels": ["console"]},
            headers=manager_headers,
        )
        assert response.status_code == 403

    def test_test_notification(self, client, auth_headers):
        """发送测试通知（console 渠道成功）"""
        response = client.post(
            "/api/notifications/test",
            json={"scenario": "exception_created"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["results"].get("console") == "ok"

    def test_test_notification_invalid_scenario(self, client, auth_headers):
        """无效场景 → 40000"""
        response = client.post(
            "/api/notifications/test",
            json={"scenario": "invalid_scenario"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 40000

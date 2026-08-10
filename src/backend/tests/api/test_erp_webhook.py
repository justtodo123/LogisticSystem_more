"""
ERP 对接 Webhook 测试（T5-1）

测试端点：
- POST /api/erp/orders - ERP 推送订单（返回 201 + 内部订单号）
- 认证：配置 ERP_API_KEY 时走 X-ERP-API-Key；未配置回退 JWT
"""
import pytest

from config.settings import settings


@pytest.fixture
def dispatcher_token():
    from tests.api.conftest import create_jwt_token
    return create_jwt_token("dispatcher", "dispatcher")


def _payload():
    return {
        "erp_order_no": "ERP-20260810-001",
        "destination_node_code": "SO010",
        "storage_center_code": "SC001",
        "time_window": "2026-06-15 全天",
        "goods": [
            {"goods_name": "ERP货物", "goods_type": "普通", "weight": 12.0, "volume": 0.6},
        ],
    }


@pytest.mark.api
@pytest.mark.phase5
class TestErpPushOrders:
    def test_push_order_success(self, client, test_nodes, dispatcher_token):
        """ERP 推送有效订单 → 201 + 内部订单号"""
        response = client.post(
            "/api/erp/orders",
            json=_payload(),
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["order_code"].startswith("O")
        assert body["data"]["erp_order_no"] == "ERP-20260810-001"
        assert body["data"]["status"] == "unassigned"

    def test_push_order_invalid_destination(self, client, test_nodes, dispatcher_token):
        """目的地节点不存在 → 400"""
        payload = _payload()
        payload["destination_node_code"] = "SO_NOT_EXIST"
        response = client.post(
            "/api/erp/orders",
            json=payload,
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )
        assert response.status_code == 400
        assert response.json()["code"] != 0

    def test_push_order_missing_fields(self, client, test_nodes, dispatcher_token):
        """缺少必填字段 → 422"""
        response = client.post(
            "/api/erp/orders",
            json={"erp_order_no": "X", "destination_node_code": "SO010"},
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )
        assert response.status_code == 422

    def test_push_order_requires_auth(self, client, test_nodes):
        """未配置 API Key 且无 JWT → 401"""
        assert settings.ERP_API_KEY == ""
        response = client.post("/api/erp/orders", json=_payload())
        assert response.status_code == 401

    def test_push_order_invalid_token(self, client, test_nodes):
        """无效 JWT → 401"""
        response = client.post(
            "/api/erp/orders",
            json=_payload(),
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_push_order_api_key_mode(self, client, test_nodes, monkeypatch):
        """配置 ERP_API_KEY 后：匹配 X-ERP-API-Key → 201，不匹配/缺失 → 401"""
        monkeypatch.setattr(settings, "ERP_API_KEY", "test-erp-key")

        # 缺少 API Key → 401
        resp = client.post("/api/erp/orders", json=_payload())
        assert resp.status_code == 401

        # 错误 API Key → 401
        resp = client.post(
            "/api/erp/orders",
            json=_payload(),
            headers={"X-ERP-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

        # 正确 API Key → 201（无需 JWT）
        resp = client.post(
            "/api/erp/orders",
            json=_payload(),
            headers={"X-ERP-API-Key": "test-erp-key"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["order_code"].startswith("O")

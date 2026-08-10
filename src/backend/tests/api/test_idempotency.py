"""
T4-3 幂等键存储迁移测试

验证中间件在新存储（Redis → 内存降级）下工作：
- 携带 X-Idempotency-Key 的写请求重复提交返回缓存响应
- 幂等键存储在缓存层（不再依赖 SQLite）
- 不携带键时不做幂等去重（重复创建被业务拒绝）
"""
import pytest

from utils import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """每个测试前后清空内存缓存，避免跨测试污染"""
    cache.memory_cache.clear()
    yield
    cache.memory_cache.clear()


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
        # 幂等键已存入缓存层（内存降级）
        assert any(k.startswith("idem:") for k in cache.memory_cache._store)

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
        assert r2.json()["code"] != 0  # 第二次创建被业务拒绝

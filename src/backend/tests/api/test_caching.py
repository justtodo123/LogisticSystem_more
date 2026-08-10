"""
T4-3 端点缓存测试

验证：
- GET /api/nodes 列表命中缓存（Redis 不可用时内存降级）
- GET /api/vehicles 列表命中缓存
- 写操作（创建节点/车辆）后对应列表缓存失效
"""
import pytest

from utils import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """每个测试前后清空内存缓存，避免跨测试污染"""
    cache.memory_cache.clear()
    yield
    cache.memory_cache.clear()


def _login_headers(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "dispatcher", "password": "123456"},
    )
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.api
class TestNodeListCaching:
    def test_nodes_list_cached(self, client, test_nodes, test_users):
        headers = _login_headers(client)
        r1 = client.get("/api/nodes", headers=headers)
        assert r1.status_code == 200
        assert any(k.startswith("nodes:list:") for k in cache.memory_cache._store), "节点列表未进入缓存"
        r2 = client.get("/api/nodes", headers=headers)
        assert r2.json() == r1.json()

    def test_nodes_create_invalidates_cache(self, client, test_users):
        headers = _login_headers(client)
        client.get("/api/nodes", headers=headers)
        assert any(k.startswith("nodes:list:") for k in cache.memory_cache._store)

        payload = {
            "node_code": "SC199",
            "name": "失效测试节点",
            "location": "测试",
            "latitude": 30.5,
            "longitude": 114.3,
            "capacity": 500.0,
        }
        r = client.post("/api/nodes/storage-centers", json=payload, headers=headers)
        assert r.status_code == 200 and r.json()["code"] == 0
        assert not any(k.startswith("nodes:list:") for k in cache.memory_cache._store), "创建后缓存未失效"


@pytest.mark.api
class TestVehicleListCaching:
    def test_vehicles_list_cached(self, client, test_vehicles, test_users):
        headers = _login_headers(client)
        r1 = client.get("/api/vehicles", headers=headers)
        assert r1.status_code == 200
        assert any(k.startswith("vehicles:list:") for k in cache.memory_cache._store), "车辆列表未进入缓存"
        r2 = client.get("/api/vehicles", headers=headers)
        assert r2.json() == r1.json()

    def test_vehicles_create_invalidates_cache(self, client, test_nodes, test_users):
        headers = _login_headers(client)
        client.get("/api/vehicles", headers=headers)
        assert any(k.startswith("vehicles:list:") for k in cache.memory_cache._store)

        payload = {
            "vehicle_code": "VEH999",
            "model": "测试车型",
            "capacity": 100.0,
            "energy_type": "fuel",
            "last_arrived_node_code": "SC001",
            "node_code": "SC001",
        }
        r = client.post("/api/vehicles", json=payload, headers=headers)
        assert r.status_code == 200 and r.json()["code"] == 0
        assert not any(k.startswith("vehicles:list:") for k in cache.memory_cache._store), "创建后缓存未失效"

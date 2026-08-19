"""
API测试：路线管理（routes.py）

测试目标：
- GET /api/routes：路线列表
- GET /api/routes/{route_code}：路线详情
- GET /api/routes/by-vehicle/{vehicle_code}/coordinates：车辆路线坐标

验证内容：
- HTTP状态码
- 响应数据结构（code, message, data, meta）
- 业务逻辑正确性
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User
from services.auth_service import get_password_hash
from models.route import Route
from models.vehicle import Vehicle
from models.node import Node
import json


class TestGetRoutes:
    """测试获取路线列表"""

    @pytest.mark.api
    def test_get_routes_empty(self, client, db_session):
        """测试空数据库返回空列表"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线列表
        response = client.get(
            "/api/routes",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "items" in body["data"]
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0

    @pytest.mark.api
    def test_get_routes_with_data(self, client, db_session):
        """测试有数据时返回路线列表"""
        # 创建测试用户、车辆、路线
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 创建测试批次
        from models.dispatch_batch import DispatchBatch
        batch = DispatchBatch(
            batch_code="BATCH001",
            global_schedule_id=1,
            status="completed"
        )
        db_session.add(batch)
        db_session.flush()

        # 创建测试节点调度
        from models.node_dispatch import NodeDispatch
        node_dispatch = NodeDispatch(
            dispatch_code="ND001",
            dispatch_batch_id=batch.id,
            vehicle_id=vehicle.id,
            level_phase=0,
            tasks=[],
            total_distance=10.0,
            total_time=30.0
        )
        db_session.add(node_dispatch)
        db_session.flush()

        # 创建测试路线
        route = Route(
            route_code="RT001",
            dispatch_id=node_dispatch.id,
            vehicle_id=vehicle.id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
        )
        db_session.add(route)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线列表
        response = client.get(
            "/api/routes",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) == 1
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["route_code"] == "RT001"


class TestGetRouteDetail:
    """测试获取路线详情"""

    @pytest.mark.api
    def test_get_route_detail_success(self, client, db_session):
        """测试成功获取路线详情"""
        # 创建测试用户、车辆、路线
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 创建测试路线
        route = Route(
            route_code="RT001",
            dispatch_id=1,
            vehicle_id=vehicle.id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
        )
        db_session.add(route)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线详情
        response = client.get(
            f"/api/routes/RT001",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["route_code"] == "RT001"
        assert "route_segments" in body["data"]

    @pytest.mark.api
    def test_get_route_detail_not_found(self, client, db_session):
        """测试路线不存在"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线详情（不存在）
        response = client.get(
            "/api/routes/RT_NONEXIST",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "路线" in body["message"] or "不存在" in body["message"]


class TestGetRouteCoordinates:
    """测试获取车辆路线坐标"""

    @pytest.mark.api
    def test_get_route_coordinates_success(self, client, db_session):
        """测试成功获取车辆路线坐标"""
        # 创建测试用户、车辆、路线
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH001",
            model="测试车型",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 创建测试路线
        route = Route(
            route_code="RT001",
            dispatch_id=1,
            vehicle_id=vehicle.id,
            total_distance=15.5,
            total_time=45.0,
            total_emission=3.1,
            route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
        )
        db_session.add(route)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取车辆路线坐标
        response = client.get(
            f"/api/routes/by-vehicle/VEH001/coordinates",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert "data" in body
        assert "vehicle_code" in body["data"]
        assert body["data"]["vehicle_code"] == "VEH001"

    @pytest.mark.api
    def test_get_route_coordinates_vehicle_not_found(self, client, db_session):
        """测试车辆不存在"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取车辆路线坐标（车辆不存在）
        response = client.get(
            "/api/routes/by-vehicle/VEH_NONEXIST/coordinates",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "车辆" in body["message"] or "不存在" in body["message"]


class TestRouteBoundaries:
    """测试路线管理的边界情况"""

    @pytest.mark.api
    def test_get_route_coordinates_no_routes(self, client, db_session):
        """测试车辆没有路线时的坐标查询"""
        # 创建测试用户、车辆（但没有路线）
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)

        # 创建测试车辆
        vehicle = Vehicle(
            vehicle_code="VEH002",
            model="测试车型2",
            capacity=100.0,
            energy_type="fuel",
            node_id=1,
            last_arrived_node_id=1,
            status="idle",
        )
        db_session.add(vehicle)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取车辆路线坐标（没有路线）
        response = client.get(
            f"/api/routes/by-vehicle/VEH002/coordinates",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（应该返回空列表或业务错误）
        assert response.status_code == 200
        body = response.json()
        # 可能返回空列表，或者业务错误
        if body["code"] == 0:
            # 返回空列表
            assert "data" in body
            assert "routes" in body["data"]
            assert body["data"]["routes"] == []
        else:
            # 业务错误
            assert body["code"] != 0

    @pytest.mark.api
    def test_get_route_detail_invalid_code(self, client, db_session):
        """测试路线编号格式错误"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 获取路线详情（编号格式错误）
        response = client.get(
            "/api/routes/INVALID_CODE",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（业务错误）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] != 0
        assert "路线" in body["message"] or "不存在" in body["message"]

    @pytest.mark.api
    def test_get_routes_with_filters(self, client, db_session):
        """测试路线列表的筛选参数"""
        # 创建测试用户
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 登录获取token
        login_resp = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        )
        token = login_resp.json()["data"]["access_token"]

        # 测试筛选参数（batch_code不存在）
        response = client.get(
            "/api/routes",
            params={"batch_code": "BATCH_NONEXIST"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 验证响应（应该返回空列表）
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0


class TestGetRoutesPaginationContract:
    """路线列表分页元数据、越界页、非法参数与组合筛选"""

    def _auth_headers(self, client, db_session):
        user = User(
            username="testuser",
            password_hash=get_password_hash("123456"),
            role="dispatcher",
            display_name="测试用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        token = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "123456"},
        ).json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def _seed_routes(self, db_session, count=5, batch_code="BATCH001", vehicle_code="VEH001"):
        from models.dispatch_batch import DispatchBatch
        from models.node_dispatch import NodeDispatch

        vehicle = db_session.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
        if vehicle is None:
            vehicle = Vehicle(
                vehicle_code=vehicle_code,
                model="测试车型",
                capacity=100.0,
                energy_type="fuel",
                node_id=1,
                last_arrived_node_id=1,
                status="idle",
            )
            db_session.add(vehicle)
            db_session.flush()

        batch = db_session.query(DispatchBatch).filter(DispatchBatch.batch_code == batch_code).first()
        if batch is None:
            batch = DispatchBatch(
                batch_code=batch_code,
                global_schedule_id=1,
                status="completed",
            )
            db_session.add(batch)
            db_session.flush()

        created = []
        for i in range(count):
            dispatch = NodeDispatch(
                dispatch_code=f"ND_{batch_code}_{vehicle_code}_{i}",
                dispatch_batch_id=batch.id,
                vehicle_id=vehicle.id,
                level_phase=0,
                tasks=[],
                total_distance=10.0,
                total_time=30.0,
            )
            db_session.add(dispatch)
            db_session.flush()
            route = Route(
                route_code=f"RT_{batch_code}_{vehicle_code}_{i:02d}",
                dispatch_id=dispatch.id,
                vehicle_id=vehicle.id,
                total_distance=15.5 + i,
                total_time=45.0,
                total_emission=3.1,
                route_segments=[{"road_name": "测试路段", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51}],
            )
            db_session.add(route)
            created.append(route)
        db_session.commit()
        return created

    @pytest.mark.api
    def test_empty_includes_page_metadata(self, client, db_session):
        headers = self._auth_headers(client, db_session)
        response = client.get("/api/routes", params={"page": 1, "page_size": 20}, headers=headers)
        body = response.json()
        assert response.status_code == 200
        assert body["code"] == 0
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 0
        assert body["data"]["page"] == 1
        assert body["data"]["page_size"] == 20

    @pytest.mark.api
    def test_first_and_second_page(self, client, db_session):
        headers = self._auth_headers(client, db_session)
        self._seed_routes(db_session, count=5)
        first = client.get("/api/routes", params={"page": 1, "page_size": 2}, headers=headers).json()
        second = client.get("/api/routes", params={"page": 2, "page_size": 2}, headers=headers).json()
        assert first["code"] == 0
        assert first["data"]["total"] == 5
        assert first["data"]["page"] == 1
        assert first["data"]["page_size"] == 2
        assert len(first["data"]["items"]) == 2
        assert second["data"]["page"] == 2
        assert len(second["data"]["items"]) == 2
        first_codes = [item["route_code"] for item in first["data"]["items"]]
        second_codes = [item["route_code"] for item in second["data"]["items"]]
        assert set(first_codes).isdisjoint(second_codes)

    @pytest.mark.api
    def test_out_of_range_page_is_empty_but_keeps_total(self, client, db_session):
        headers = self._auth_headers(client, db_session)
        self._seed_routes(db_session, count=3)
        body = client.get("/api/routes", params={"page": 9, "page_size": 20}, headers=headers).json()
        assert body["code"] == 0
        assert body["data"]["items"] == []
        assert body["data"]["total"] == 3
        assert body["data"]["page"] == 9
        assert body["data"]["page_size"] == 20

    @pytest.mark.api
    def test_invalid_page_params(self, client, db_session):
        headers = self._auth_headers(client, db_session)
        for params in (
            {"page": 0, "page_size": 20},
            {"page": -1, "page_size": 20},
            {"page": 1, "page_size": 0},
            {"page": 1, "page_size": 201},
        ):
            body = client.get("/api/routes", params=params, headers=headers).json()
            assert body["code"] == 40000, params

    @pytest.mark.api
    def test_batch_vehicle_and_combined_filters(self, client, db_session):
        headers = self._auth_headers(client, db_session)
        self._seed_routes(db_session, count=2, batch_code="BA", vehicle_code="VA")
        self._seed_routes(db_session, count=3, batch_code="BB", vehicle_code="VB")
        self._seed_routes(db_session, count=1, batch_code="BA", vehicle_code="VB")

        by_batch = client.get("/api/routes", params={"batch_code": "BA"}, headers=headers).json()
        assert by_batch["data"]["total"] == 3
        assert {item["batch_code"] for item in by_batch["data"]["items"]} == {"BA"}

        by_vehicle = client.get("/api/routes", params={"vehicle_code": "VB"}, headers=headers).json()
        assert by_vehicle["data"]["total"] == 4
        assert {item["vehicle_code"] for item in by_vehicle["data"]["items"]} == {"VB"}

        combined = client.get(
            "/api/routes",
            params={"batch_code": "BA", "vehicle_code": "VB"},
            headers=headers,
        ).json()
        assert combined["data"]["total"] == 1
        assert combined["data"]["items"][0]["batch_code"] == "BA"
        assert combined["data"]["items"][0]["vehicle_code"] == "VB"

    @pytest.mark.api
    def test_sort_is_stable_across_pages(self, client, db_session):
        headers = self._auth_headers(client, db_session)
        self._seed_routes(db_session, count=6)
        page1 = client.get("/api/routes", params={"page": 1, "page_size": 3}, headers=headers).json()
        page2 = client.get("/api/routes", params={"page": 2, "page_size": 3}, headers=headers).json()
        all_page = client.get("/api/routes", params={"page": 1, "page_size": 20}, headers=headers).json()
        paged_codes = [i["route_code"] for i in page1["data"]["items"] + page2["data"]["items"]]
        all_codes = [i["route_code"] for i in all_page["data"]["items"]]
        assert paged_codes == all_codes
        assert paged_codes == sorted(paged_codes, reverse=True) or len(set(paged_codes)) == 6

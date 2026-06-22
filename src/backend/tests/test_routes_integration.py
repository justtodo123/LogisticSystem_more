"""
阶段5（F006路径规划）集成测试

测试完整的API流程：从HTTP请求到数据库操作
使用真实的测试数据库，验证各模块之间的协同工作
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User
from fastapi.testclient import TestClient


# ── 测试夹具 ────────────────────────────────────────────────────

@pytest.fixture
def client_and_db():
    """
    创建测试客户端和数据库，确保共享同一个数据库文件
    
    使用临时文件数据库（而不是内存数据库），确保多个连接可以共享同一个数据库
    """
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    db_url = f"sqlite:///{db_path}"
    
    # 创建数据库引擎并创建表
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # 创建测试数据
    test_data = create_integration_test_data(session)
    
    # 创建测试客户端，覆盖依赖
    from main import app
    from config.database import get_db
    from api.dependencies import get_current_user
    
    # 覆盖数据库依赖 - 使用同一个session
    app.dependency_overrides[get_db] = lambda: session
    
    # 覆盖认证依赖
    mock_user = User()
    mock_user.id = 1
    mock_user.username = "dispatcher"
    mock_user.role = "dispatcher"
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as client:
        yield client, session, test_data
    
    # 清理
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


def create_integration_test_data(db):
    """
    创建集成测试所需的完整数据
    
    包含：
    1. 节点（存储中心、分拣中心）
    2. 全局调度（GlobalSchedule）
    3. 车辆和司机
    4. 调度批次（DispatchBatch）
    5. 节点调度明细（NodeDispatch）
    """
    # 1. 创建节点
    from models.node import Node
    from models.storage_center import StorageCenter
    from models.sorting_center import SortingCenter
    
    nodes = [
        Node(node_code="SC001", name="存储中心1", location="武汉", 
             latitude=30.5, longitude=114.3, node_type="storage_center"),
        Node(node_code="SO001", name="1级分拣中心1", location="武汉",
             latitude=30.6, longitude=114.4, node_type="sorting_center"),
        Node(node_code="SO010", name="0级分拣中心1", location="武昌",
             latitude=30.54, longitude=114.315, node_type="sorting_center"),
    ]
    
    for node in nodes:
        db.add(node)
    db.flush()
    
    # 创建节点的扩展信息
    sc1 = StorageCenter(node_id=nodes[0].id, capacity=1000.0, inventory=0)
    so1 = SortingCenter(node_id=nodes[1].id, level=1, capacity=100, max_storage_time=24)
    so2 = SortingCenter(node_id=nodes[2].id, level=0)
    
    db.add_all([sc1, so1, so2])
    db.flush()
    
    # 2. 创建全局调度（GlobalSchedule）
    from models.global_schedule import GlobalSchedule
    
    global_schedule = GlobalSchedule(
        schedule_code="GS20260614001",
        order_codes=["O001"],
        goods_schedules=[{"goods_code": "G001", "order_code": "O001", "path": ["SC001", "SO001", "SO010"]}],
        total_distance=100.0,
        total_time=10.0,
        total_goods=1,
        score=1000.0
    )
    db.add(global_schedule)
    db.flush()
    
    # 3. 创建车辆
    from models.vehicle import Vehicle
    
    vehicles = [
        Vehicle(vehicle_code="VEH001", model="测试车型", capacity=100.0,
                energy_type="fuel", node_id=nodes[0].id, 
                last_arrived_node_id=nodes[0].id, status="idle"),
    ]
    
    for vehicle in vehicles:
        db.add(vehicle)
    db.flush()
    
    # 4. 创建司机
    from models.driver import Driver
    
    drivers = [
        Driver(driver_code="DRV001", name="测试司机", phone="13800000000",
               license_type="C1", shift="day", node_id=nodes[0].id, status="idle"),
    ]
    
    for driver in drivers:
        db.add(driver)
    db.flush()
    
    # 5. 创建调度批次
    from models.dispatch_batch import DispatchBatch
    
    batch = DispatchBatch(
        batch_code="BATCH20260614001",
        global_schedule_id=global_schedule.id,
        status="pending",
        demo_mode=True
    )
    db.add(batch)
    db.flush()
    
    # 6. 创建节点调度明细
    from models.node_dispatch import NodeDispatch
    
    dispatch = NodeDispatch(
        dispatch_code="DISP20260614001",
        dispatch_batch_id=batch.id,
        vehicle_id=vehicles[0].id,
        driver_id=drivers[0].id,
        level_phase=0,
        tasks=[{
            "from_node_code": "SC001",
            "to_node_code": "SO001",
            "package_codes": ["PKG001"],
            "is_return": False
        }],
        total_distance=50.0,
        total_time=5.0
    )
    db.add(dispatch)
    db.flush()
    
    # 提交事务
    db.commit()
    
    return {
        "nodes": nodes,
        "global_schedule": global_schedule,
        "vehicles": vehicles,
        "drivers": drivers,
        "batch": batch,
        "dispatch": dispatch
    }


# ── 集成测试类 ─────────────────────────────────────────────────

class TestRoutesIntegration:
    """阶段5路径规划集成测试"""
    
    def test_complete_route_planning_flow(self, client_and_db):
        """
        测试完整的路径规划流程：
        
        1. 调用 POST /api/routes/plan 触发路径规划
        2. 验证响应成功
        3. 验证数据库中创建了Route记录
        4. 调用 GET /api/routes 查询路线列表
        5. 验证路线列表响应正确
        6. 调用 GET /api/routes/{route_code} 查询路线详情
        7. 验证路线详情响应正确
        8. 调用 GET /api/routes/by-vehicle/{vehicle_code}/coordinates 查询车辆路线坐标
        9. 验证车辆路线坐标响应正确
        """
        client, session, test_data = client_and_db
        
        # 1. 调用 POST /api/routes/plan 触发路径规划
        response = client.post(
            "/api/routes/plan",
            json={"batch_code": "BATCH20260614001", "dispatch_codes": None}
        )
        
        # 打印响应数据用于调试
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        # 2. 验证响应成功
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0, f"Expected code 0, got {data['code']}, message: {data.get('message', 'N/A')}"
        
        # 提交事务以使Route记录可见
        session.commit()
        
        # 3. 验证数据库中创建了Route记录
        from models.route import Route
        routes = session.query(Route).all()
        assert len(routes) > 0, f"Expected at least 1 route, got {len(routes)}"
        
        # 获取第一个路线的code
        route_code = routes[0].route_code
        
        # 4. 调用 GET /api/routes 查询路线列表
        response = client.get("/api/routes")
        
        # 5. 验证路线列表响应正确
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "items" in data["data"]
        
        # 6. 调用 GET /api/routes/{route_code} 查询路线详情
        response = client.get(f"/api/routes/{route_code}")
        
        # 7. 验证路线详情响应正确
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "route_segments" in data["data"]
        
        # 8. 调用 GET /api/routes/by-vehicle/{vehicle_code}/coordinates 查询车辆路线坐标
        response = client.get("/api/routes/by-vehicle/VEH001/coordinates")
        
        # 9. 验证车辆路线坐标响应正确
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "routes" in data["data"]
    
    def test_plan_routes_batch_not_found(self, client_and_db):
        """
        测试路径规划时批次不存在的情况
        
        应该返回错误响应
        """
        client, session, test_data = client_and_db
        
        # 调用 POST /api/routes/plan 触发路径规划（使用不存在的批次编码）
        response = client.post(
            "/api/routes/plan",
            json={"batch_code": "BATCH_INVALID", "dispatch_codes": None}
        )
        
        # 验证响应失败
        assert response.status_code == 200  # 业务错误返回200
        data = response.json()
        assert data["code"] != 0
        assert "批次不存在" in data["message"]
    
    def test_get_route_detail_not_found(self, client_and_db):
        """
        测试查询不存在的路线详情
        
        应该返回404错误
        """
        client, session, test_data = client_and_db
        
        # 调用 GET /api/routes/{route_code} 查询路线详情（使用不存在的路线编码）
        response = client.get("/api/routes/ROUTE_INVALID")
        
        # 验证响应失败
        assert response.status_code == 200  # 业务错误返回200
        data = response.json()
        assert data["code"] == 40400
        assert "路线不存在" in data["message"]
    
    def test_get_route_coordinates_vehicle_not_found(self, client_and_db):
        """
        测试查询不存在的车辆的路线坐标
        
        应该返回404错误
        """
        client, session, test_data = client_and_db
        
        # 调用 GET /api/routes/by-vehicle/{vehicle_code}/coordinates 查询车辆路线坐标
        response = client.get("/api/routes/by-vehicle/VEH_INVALID/coordinates")
        
        # 验证响应失败
        assert response.status_code == 200  # 业务错误返回200
        data = response.json()
        assert data["code"] == 40400
        assert "车辆不存在" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
VehicleService 单元测试

测试车辆服务 (services/vehicle_service.py) 的所有方法：
- create_vehicle: 创建车辆
- get_vehicles: 获取车辆列表
- get_vehicle: 获取车辆详情
- update_vehicle: 更新车辆
- delete_vehicle: 删除车辆
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from services.vehicle_service import VehicleService
from models.vehicle import Vehicle
from models.node import Node
from schemas.vehicle import VehicleCreate, VehicleUpdate
from core.error_codes import (
    CODE_SUCCESS, CODE_INTERNAL_ERROR, CODE_CONFLICT,
    CODE_NODE_NOT_FOUND, CODE_VEHICLE_NOT_FOUND,
    CODE_VEHICLE_STATUS_NOT_ALLOWED
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_node():
    """示例节点"""
    node = MagicMock(spec=Node)
    node.id = 1
    node.node_code = "SC001"
    node.name = "测试存储中心"
    return node


@pytest.fixture
def sample_vehicle():
    """示例车辆"""
    vehicle = MagicMock(spec=Vehicle)
    vehicle.id = 1
    vehicle.vehicle_code = "V1700000000000"
    vehicle.model = "测试车型"
    vehicle.capacity = 1000.0
    vehicle.energy_type = "electric"
    vehicle.vehicle_type = "normal"
    vehicle.capability_tags = ["cold_chain"]
    vehicle.last_arrived_node_id = 1
    vehicle.status = "idle"
    vehicle.node_id = 1
    vehicle.created_at = datetime.now()
    vehicle.updated_at = datetime.now()
    return vehicle


class TestVehicleServiceCreateVehicle:
    """测试创建车辆"""

    @pytest.mark.asyncio
    async def test_create_vehicle_success(self, mock_db, sample_node):
        """测试成功创建车辆"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 车辆编号不存在
            sample_node,  # 节点存在
            sample_node,  # 最后到达节点存在
        ]
        
        # 创建请求数据
        vehicle_create = VehicleCreate(
            vehicle_code="V1700000000000",
            model="测试车型",
            capacity=1000.0,
            energy_type="electric",
            node_code="SC001",
            last_arrived_node_code="SC001"
        )
        
        # 执行
        result = await VehicleService.create_vehicle(vehicle_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"
        assert result["data"]["vehicle_code"] == "V1700000000000"

    @pytest.mark.asyncio
    async def test_create_vehicle_code_exists(self, mock_db, sample_vehicle):
        """测试车辆编号已存在"""
        # 模拟数据库查询返回已存在的车辆
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vehicle
        
        # 创建请求数据
        vehicle_create = VehicleCreate(
            vehicle_code="V1700000000000",
            model="测试车型",
            capacity=1000.0,
            energy_type="electric",
            node_code="SC001",
            last_arrived_node_code="SC001"
        )
        
        # 执行
        result = await VehicleService.create_vehicle(vehicle_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_CONFLICT
        assert "车辆编号已存在" in result["message"]

    @pytest.mark.asyncio
    async def test_create_vehicle_node_not_found(self, mock_db):
        """测试节点不存在"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 车辆编号不存在
            None,  # 节点不存在
        ]
        
        # 创建请求数据
        vehicle_create = VehicleCreate(
            vehicle_code="V1700000000000",
            model="测试车型",
            capacity=1000.0,
            energy_type="electric",
            node_code="INVALID",
            last_arrived_node_code="SC001"
        )
        
        # 执行
        result = await VehicleService.create_vehicle(vehicle_create, mock_db)
        
        # 验证
        assert result["code"] == CODE_NODE_NOT_FOUND
        assert "节点不存在" in result["message"]


class TestVehicleServiceGetVehicles:
    """测试获取车辆列表"""

    @pytest.mark.asyncio
    async def test_get_vehicles_success(self, mock_db, sample_vehicle):
        """测试成功获取车辆列表"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_vehicle]
        
        # 模拟节点查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(node_code="SC001", name="存储中心1"),
            MagicMock(node_code="SC001", name="存储中心1"),
        ]
        
        # 执行
        result = await VehicleService.get_vehicles(1, 20, None, None, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert "items" in result["data"]
        assert result["data"]["total"] == 1


class TestVehicleServiceGetVehicle:
    """测试获取车辆详情"""

    @pytest.mark.asyncio
    async def test_get_vehicle_success(self, mock_db, sample_vehicle):
        """测试成功获取车辆详情"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vehicle
        
        # 模拟节点查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(node_code="SC001", name="存储中心1"),
            MagicMock(node_code="SC001", name="存储中心1"),
        ]
        
        # 执行
        result = await VehicleService.get_vehicle("V1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["vehicle_code"] == "V1700000000000"

    @pytest.mark.asyncio
    async def test_get_vehicle_not_found(self, mock_db):
        """测试车辆不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await VehicleService.get_vehicle("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_VEHICLE_NOT_FOUND
        assert "车辆不存在" in result["message"]


class TestVehicleServiceUpdateVehicle:
    """测试更新车辆"""

    @pytest.mark.asyncio
    async def test_update_vehicle_success(self, mock_db, sample_vehicle):
        """测试成功更新车辆"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_vehicle,  # 查询车辆
            MagicMock(node_code="SC002", name="新节点"),  # 查询新节点
            MagicMock(node_code="SC002", name="新节点"),  # 再次查询节点
        ]
        
        # 创建更新数据
        vehicle_update = VehicleUpdate(status="maintenance")
        
        # 执行
        result = await VehicleService.update_vehicle("V1700000000000", vehicle_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["data"]["status"] == "maintenance"

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, mock_db):
        """测试车辆不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建更新数据
        vehicle_update = VehicleUpdate(status="maintenance")
        
        # 执行
        result = await VehicleService.update_vehicle("INVALID", vehicle_update, mock_db)
        
        # 验证
        assert result["code"] == CODE_VEHICLE_NOT_FOUND
        assert "车辆不存在" in result["message"]


class TestVehicleServiceDeleteVehicle:
    """测试删除车辆"""

    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self, mock_db, sample_vehicle):
        """测试成功删除车辆"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vehicle
        
        # 执行
        result = await VehicleService.delete_vehicle("V1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_SUCCESS
        assert result["message"] == "success"

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self, mock_db):
        """测试车辆不存在"""
        # 模拟数据库查询返回None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行
        result = await VehicleService.delete_vehicle("INVALID", mock_db)
        
        # 验证
        assert result["code"] == CODE_VEHICLE_NOT_FOUND
        assert "车辆不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_vehicle_status_not_allowed(self, mock_db, sample_vehicle):
        """测试配送中车辆不可删除"""
        # 修改车辆状态为delivering
        sample_vehicle.status = "delivering"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_vehicle
        
        # 执行
        result = await VehicleService.delete_vehicle("V1700000000000", mock_db)
        
        # 验证
        assert result["code"] == CODE_VEHICLE_STATUS_NOT_ALLOWED
        assert "不可删除" in result["message"]

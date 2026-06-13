"""
F006 路径规划算法单元测试
"""

import pytest
import math
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestHaversine:
    """测试 _haversine 函数"""
    
    def test_same_coordinates(self):
        """输入相同坐标，返回0.0"""
        from algorithms.route_planning import _haversine
        result = _haversine(30.5, 114.3, 30.5, 114.3)
        assert result == 0.0
    
    def test_different_coordinates(self):
        """输入不同坐标，返回正确距离"""
        from algorithms.route_planning import _haversine
        # 武汉到北京的大致距离约为 1000 km
        result = _haversine(30.5, 114.3, 39.9, 116.4)
        assert 900 < result < 1100  # 允许一定误差


class TestGenerateRouteCode:
    """测试 _generate_route_code 函数"""
    
    @patch('algorithms.route_planning.Route')
    def test_first_call(self, mock_route):
        """首次调用，返回 ROUTE20260614001"""
        from algorithms.route_planning import _generate_route_code
        
        # 模拟数据库查询返回空
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        
        result = _generate_route_code(mock_db)
        assert result.startswith("ROUTE")
        assert result.endswith("001")
    
    @patch('algorithms.route_planning.Route')
    def test_second_call(self, mock_route):
        """再次调用，返回 ROUTE20260614002"""
        from algorithms.route_planning import _generate_route_code
        
        # 模拟数据库查询返回 ROUTE20260614001
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = ("ROUTE20260614001",)
        
        result = _generate_route_code(mock_db)
        assert result.endswith("002")


class TestCalculateEmission:
    """测试 _calculate_emission 函数"""
    
    def test_fuel_car(self):
        """燃油车，距离10km，返回2.0"""
        from algorithms.route_planning import _calculate_emission
        result = _calculate_emission(10.0, 'fuel')
        assert result == 2.0
    
    def test_electric_car(self):
        """电动车，距离10km，返回0.0"""
        from algorithms.route_planning import _calculate_emission
        result = _calculate_emission(10.0, 'electric')
        assert result == 0.0


class TestRunRoutePlanning:
    """测试 run_route_planning 函数"""
    
    def test_valid_dispatch_id(self):
        """输入有效dispatch_id，返回route_data"""
        from algorithms.route_planning import run_route_planning
        from sqlalchemy.orm import Session
        
        # 模拟 NodeDispatch
        mock_dispatch_instance = MagicMock()
        mock_dispatch_instance.id = 1
        mock_dispatch_instance.vehicle_id = 1
        mock_dispatch_instance.tasks = [
            {"from_node_code": "NODE001", "to_node_code": "NODE002"}
        ]
        
        # 模拟 Vehicle
        mock_vehicle_instance = MagicMock()
        mock_vehicle_instance.id = 1
        mock_vehicle_instance.energy_type = 'fuel'
        
        # 模拟 Node (需要两个节点：起始和目的)
        mock_node_instance1 = MagicMock()
        mock_node_instance1.latitude = 30.5
        mock_node_instance1.longitude = 114.3
        mock_node_instance2 = MagicMock()
        mock_node_instance2.latitude = 30.6
        mock_node_instance2.longitude = 114.4
        
        # 模拟数据库
        mock_db = MagicMock(spec=Session)
        
        # 设置 db.query().filter().first() 的返回值
        # 由于 db.query() 会被调用多次，我们使用 side_effect 来控制返回值
        mock_query = MagicMock()
        
        # 第一次调用 db.query().filter().first() 返回 mock_dispatch_instance
        # 第二次调用 db.query().filter().first() 返回 mock_vehicle_instance
        # 第三次和第四次调用 db.query().filter().first() 返回 mock_node_instance1 和 mock_node_instance2
        mock_query.filter.return_value.first.side_effect = [
            mock_dispatch_instance,  # NodeDispatch
            mock_vehicle_instance,   # Vehicle
            mock_node_instance1,     # Node 1
            mock_node_instance2,     # Node 2
            None,                    # Route (for _generate_route_code)
        ]
        
        mock_db.query.return_value = mock_query
        
        # 调用函数
        result = run_route_planning(mock_db, 1)
        
        # 验证结果
        assert "route_code" in result
        assert "dispatch_id" in result
        assert "vehicle_id" in result
        assert "route_segments" in result
        assert "total_distance" in result
        assert "total_time" in result
        assert "total_emission" in result
        assert "algorithm_type" in result
    
    def test_invalid_dispatch_id(self):
        """输入无效dispatch_id，抛出异常"""
        from algorithms.route_planning import run_route_planning
        
        # 模拟数据库查询返回空
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 调用函数，应该抛出异常
        with pytest.raises(ValueError):
            run_route_planning(mock_db, 999)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

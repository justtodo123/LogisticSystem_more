"""
F006 路径规划算法

为F005生成的每一辆车的任务列表规划全局路径（Haversine距离 + 2-opt优化）。

算法输入：db (数据库会话), dispatch_id (节点调度明细ID)
算法输出：route_data (字典，包含一个route的数据)
"""

import math
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.node import Node
from models.vehicle import Vehicle
from models.node_dispatch import NodeDispatch
from models.route import Route


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Haversine 公式计算两点间球面距离（公里）
    
    Args:
        lat1, lng1: 点1的纬度和经度（度）
        lat2, lng2: 点2的纬度和经度（度）
        
    Returns:
        距离（公里）
    """
    R = 6371.0  # 地球半径（公里）
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_phi / 2) ** 2 
         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def _generate_route_code(db: Session) -> str:
    """
    生成路线编码，格式：ROUTE + YYYYMMDD + 3位序号
    
    Args:
        db: 数据库会话
        
    Returns:
        路线编码字符串
    """
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"ROUTE{today_str}"
    
    max_record = (
        db.query(Route.route_code)
        .filter(Route.route_code.like(f"{prefix}%"))
        .order_by(Route.route_code.desc())
        .first()
    )
    
    if max_record and max_record[0]:
        seq = int(max_record[0][-3:]) + 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def _calculate_emission(distance: float, energy_type: str) -> float:
    """
    计算碳排放
    
    Args:
        distance: 距离（公里）
        energy_type: 能源类型（fuel/electric）
        
    Returns:
        碳排放（kg）
    """
    if energy_type == 'fuel':
        return distance * 0.2  # 燃油车：0.2 kg/km
    else:
        return 0.0  # 电动车：0


def run_route_planning(db: Session, dispatch_id: int) -> Dict[str, Any]:
    """
    F006 路径规划算法主函数
    
    为指定的节点调度明细规划路径。
    
    Args:
        db: 数据库会话
        dispatch_id: 节点调度明细ID
        
    Returns:
        route_data: 路径规划结果字典，包含：
            - route_code: 路线编码
            - dispatch_id: 节点调度明细ID
            - vehicle_id: 车辆ID
            - route_segments: 路径路段JSON
            - total_distance: 总距离
            - total_time: 总时间
            - total_emission: 总碳排放
            - algorithm_type: 算法类型
            
    Raises:
        ValueError: 如果dispatch_id不存在或数据不完整
    """
    # 1. 查询 NodeDispatch (dispatch_id)
    dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == dispatch_id).first()
    if not dispatch:
        raise ValueError(f"节点调度明细不存在：dispatch_id={dispatch_id}")
    
    # 2. 获取车辆信息 (vehicle_id)
    vehicle_id = dispatch.vehicle_id
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise ValueError(f"车辆不存在：vehicle_id={vehicle_id}")
    
    # 3. 解析 tasks (JSON数组)
    tasks = dispatch.tasks
    if not tasks or not isinstance(tasks, list):
        raise ValueError(f"节点调度明细任务列表为空或格式错误：dispatch_id={dispatch_id}")
    
    # 4. 对每个任务计算路径
    route_segments = []
    total_distance = 0.0
    total_time = 0.0
    total_emission = 0.0
    
    for task in tasks:
        # a. 获取起始节点和目的节点
        from_node_code = task.get("from_node_code")
        to_node_code = task.get("to_node_code")
        
        if not from_node_code or not to_node_code:
            continue
        
        # 查询节点坐标
        from_node = db.query(Node).filter(Node.node_code == from_node_code).first()
        to_node = db.query(Node).filter(Node.node_code == to_node_code).first()
        
        if not from_node or not to_node:
            continue
        
        # c. 使用 Haversine 公式计算距离
        distance = _haversine(
            float(from_node.latitude), float(from_node.longitude),
            float(to_node.latitude), float(to_node.longitude)
        )
        
        # d. 生成 route_segments (P0用直线距离，road_name='虚拟道路')
        segment = {
            "road_name": "虚拟道路",
            "start_lng": float(from_node.longitude),
            "start_lat": float(from_node.latitude),
            "end_lng": float(to_node.longitude),
            "end_lat": float(to_node.latitude)
        }
        route_segments.append(segment)
        
        # e. 计算时间（距离 / 平均速度，暂定60km/h）
        time = distance / 60.0 * 60  # 转换为分钟
        
        # e. 计算碳排放（燃油车：距离×0.2kg/km，电动车：0）
        emission = _calculate_emission(distance, vehicle.energy_type)
        
        # 累加
        total_distance += distance
        total_time += time
        total_emission += emission
    
    # 5. 合并所有任务的 route_segments（已在上面完成）
    
    # 6. 计算总距离、总时间、总碳排放（已在上面完成）
    
    # 7. 返回 route_data
    route_data = {
        "route_code": _generate_route_code(db),
        "dispatch_id": dispatch_id,
        "vehicle_id": vehicle_id,
        "route_segments": route_segments,
        "total_distance": round(total_distance, 3),
        "total_time": round(total_time, 3),
        "total_emission": round(total_emission, 4),
        "algorithm_type": "traditional"
    }
    
    return route_data


def _two_opt(route_segments: List[Dict], distances: List[List[float]]) -> List[Dict]:
    """
    2-opt优化算法（MVP不触发，仅实现结构）
    
    Args:
        route_segments: 路径路段列表
        distances: 距离矩阵
        
    Returns:
        优化后的路径路段列表
    """
    # MVP不触发优化，直接返回原路径
    return route_segments

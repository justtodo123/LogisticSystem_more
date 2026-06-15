"""
F005 节点间调度算法

串行执行两次：
1. 第一次调用（L0→L1）：查询 from∈L0、to∈L1、status=packed 的包裹，分配车辆与司机
2. 第二次调用（L1→L2）：查询 from∈L1、to∈L2、status=packed 的包裹，分配车辆与司机

车辆匹配策略（简化）：
1. 载重匹配：优先选择载重足够的车辆（capacity >= 包裹总重量）
2. 节点优先级：本节点空闲车辆 > 返程车辆 > 其他节点空闲车辆
3. 距离评分：暂不实现（阶段5或阶段6补充）

车辆返回规则：每个车辆的任务列表末尾自动追加一个 is_return=true 的返回任务
"""
import math
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, or_

from models.node import Node
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.global_schedule import GlobalSchedule
from models.sorting_center import SortingCenter
from models.storage_center import StorageCenter


def _load_config() -> dict:
    """加载算法配置权重"""
    import os
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "algorithm_config.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


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


def _generate_batch_code(db: Session) -> str:
    """生成调度批次编号，格式：BATCH + YYYYMMDD + 3位序号"""
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"BATCH{today_str}"
    
    max_record = (
        db.query(DispatchBatch.batch_code)
        .filter(DispatchBatch.batch_code.like(f"{prefix}%"))
        .order_by(DispatchBatch.batch_code.desc())
        .first()
    )
    
    if max_record and max_record[0]:
        seq = int(max_record[0][-3:]) + 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def _generate_dispatch_code(db: Session) -> str:
    """生成节点调度明细编号，格式：DISP + YYYYMMDD + 3位序号"""
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"DISP{today_str}"
    
    max_record = (
        db.query(NodeDispatch.dispatch_code)
        .filter(NodeDispatch.dispatch_code.like(f"{prefix}%"))
        .order_by(NodeDispatch.dispatch_code.desc())
        .first()
    )
    
    if max_record and max_record[0]:
        seq = int(max_record[0][-3:]) + 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def _get_idle_vehicles_at_node(db: Session, node_id: int) -> List[Vehicle]:
    """获取指定节点的空闲车辆（status='idle'）"""
    return db.query(Vehicle).filter(
        Vehicle.node_id == node_id,
        Vehicle.status == 'idle'
    ).all()


def _get_return_vehicles_at_node(db: Session, node_id: int) -> List[Vehicle]:
    """获取指定节点的返程车辆（last_arrived_node_id=当前节点）"""
    return db.query(Vehicle).filter(
        Vehicle.last_arrived_node_id == node_id
    ).all()


def _calculate_vehicle_score(
    vehicle: Vehicle, 
    from_node: Node, 
    to_node: Node,
    package_count: int,
    config: dict
) -> float:
    """
    计算车辆评分（规则评分+启发式）
    
    Args:
        vehicle: 车辆对象
        from_node: 起始节点
        to_node: 目的节点
        package_count: 包裹数量
        config: 算法配置
    
    Returns:
        评分（越低越好）
    """
    # 计算距离
    distance = _haversine(
        float(from_node.latitude), float(from_node.longitude),
        float(to_node.latitude), float(to_node.longitude)
    )
    
    # 计算时间（距离 / 平均速度，暂定60km/h）
    time = distance / 60.0
    
    # 获取权重
    weights = config.get("node_dispatch_weights", {"w1": 0.5, "w2": 0.3, "w3": 0.2})
    w1 = weights.get("w1", 0.5)
    w2 = weights.get("w2", 0.3)
    w3 = weights.get("w3", 0.2)
    
    # 计算评分
    score = w1 * distance + w2 * time + w3 * package_count
    
    return score


def _dispatch_level(
    db: Session,
    schedule_id: int,
    level_phase: int,
    config: dict
) -> Tuple[List[Dict[str, Any]], List[Package]]:
    """
    执行一次节点调度（L0→L1 或 L1→L2）
    
    Args:
        db: 数据库会话
        schedule_id: 全局调度方案ID
        level_phase: 层级阶段（0: L0→L1, 1: L1→L2）
        config: 算法配置
    
    Returns:
        (dispatch_list, updated_packages)
        - dispatch_list: 调度明细列表
        - updated_packages: 已更新的包裹列表
    """
    # 创建别名
    NodeAlias1 = aliased(Node)
    NodeAlias2 = aliased(Node)
    SortingCenterAlias1 = aliased(SortingCenter)
    SortingCenterAlias2 = aliased(SortingCenter)
    
    # 1. 根据 level_phase 确定查询条件
    if level_phase == 0:
        # L0→L1: from_node.node_type='storage_center' AND to_node.node_type='sorting_center' 
        # AND to_node.sorting_center.level=1 AND packages.status='packed'
        packages = (
            db.query(Package)
            .join(Node, Package.from_node_id == Node.id)
            .join(NodeAlias1, Package.to_node_id == NodeAlias1.id)
            .join(SortingCenter, NodeAlias1.id == SortingCenter.node_id)
            .filter(
                Node.node_type == 'storage_center',
                NodeAlias1.node_type == 'sorting_center',
                SortingCenter.level == 1,
                Package.status == 'packed',
                Package.schedule_id == schedule_id
            )
            .all()
        )
    else:
        # L1→L2: from_node.node_type='sorting_center' AND from_node.sorting_center.level=1 
        # AND to_node.node_type='sorting_center' AND to_node.sorting_center.level=0 
        # AND packages.status='packed'
        packages = (
            db.query(Package)
            .join(Node, Package.from_node_id == Node.id)
            .join(SortingCenter, Node.id == SortingCenter.node_id)
            .join(NodeAlias1, Package.to_node_id == NodeAlias1.id)
            .join(SortingCenterAlias1, NodeAlias1.id == SortingCenterAlias1.node_id)
            .filter(
                Node.node_type == 'sorting_center',
                SortingCenter.level == 1,
                NodeAlias1.node_type == 'sorting_center',
                SortingCenterAlias1.level == 0,
                Package.status == 'packed',
                Package.schedule_id == schedule_id
            )
            .all()
        )
    
    if not packages:
        return [], []
    
    # 2. 按 from_node_code 分组包裹
    packages_by_from_node = defaultdict(list)
    for pkg in packages:
        from_node_code = pkg.from_node.node_code
        packages_by_from_node[from_node_code].append(pkg)
    
    # 3. 对每个分组进行调度
    dispatch_list = []
    updated_packages = []
    
    for from_node_code, node_packages in packages_by_from_node.items():
        # 获取起始节点
        from_node = db.query(Node).filter(Node.node_code == from_node_code).first()
        if not from_node:
            continue
        
        # 按 to_node_code 分组包裹（同一目的节点的包裹可以一起运输）
        packages_by_to_node = defaultdict(list)
        for pkg in node_packages:
            to_node_code = pkg.to_node.node_code
            packages_by_to_node[to_node_code].append(pkg)
        
        # 对每个目的节点分组进行车辆分配
        for to_node_code, to_packages in packages_by_to_node.items():
            # 获取目的节点
            to_node = db.query(Node).filter(Node.node_code == to_node_code).first()
            if not to_node:
                continue
            
            # 计算包裹总重量
            total_weight = sum(float(pkg.weight) for pkg in to_packages)
            
            # 查询候选车辆
            # 第一优先：本节点空闲车辆
            candidate_vehicles = _get_idle_vehicles_at_node(db, from_node.id)
            
            # 第二优先：返程车辆
            if not candidate_vehicles:
                candidate_vehicles = _get_return_vehicles_at_node(db, from_node.id)
            
            # 筛选载重足够的车辆
            candidate_vehicles = [
                v for v in candidate_vehicles 
                if float(v.capacity) >= total_weight
            ]
            
            if not candidate_vehicles:
                raise ValueError(f"节点 {from_node_code} 没有可用的车辆（载重不足或无不空闲车辆）")
            
            # 计算每辆车的评分，选择评分最低的车辆
            vehicle_scores = []
            for vehicle in candidate_vehicles:
                score = _calculate_vehicle_score(vehicle, from_node, to_node, len(to_packages), config)
                vehicle_scores.append((score, vehicle))
            
            vehicle_scores.sort(key=lambda x: x[0])
            best_vehicle = vehicle_scores[0][1]
            
            # 获取车辆的司机（从车辆归属节点选 status=idle 第一个司机）
            driver = db.query(Driver).filter(
                Driver.node_id == best_vehicle.node_id,
                Driver.status == 'idle'
            ).first()
            
            # 创建任务列表
            tasks = []
            
            # 添加运输任务
            task = {
                "from_node_code": from_node_code,
                "to_node_code": to_node_code,
                "package_codes": [pkg.package_code for pkg in to_packages],
                "is_return": False
            }
            tasks.append(task)
            
            # 添加返回任务
            return_task = {
                "from_node_code": to_node_code,
                "to_node_code": from_node_code,  # 返回起始节点
                "package_codes": [],
                "is_return": True
            }
            tasks.append(return_task)
            
            # 计算总距离和总时间
            total_distance = _haversine(
                float(from_node.latitude), float(from_node.longitude),
                float(to_node.latitude), float(to_node.longitude)
            )
            # 返回距离
            return_distance = _haversine(
                float(to_node.latitude), float(to_node.longitude),
                float(from_node.latitude), float(from_node.longitude)
            )
            total_distance += return_distance
            total_time = total_distance / 60.0  # 平均速度60km/h
            
            # 创建调度明细
            dispatch = {
                "vehicle_code": best_vehicle.vehicle_code,
                "driver_code": driver.driver_code if driver else None,
                "tasks": tasks,
                "total_distance": total_distance,
                "total_time": total_time,
                "vehicle_id": best_vehicle.id,
                "driver_id": driver.id if driver else None,
            }
            dispatch_list.append(dispatch)
            
            # 标记包裹为已分配
            for pkg in to_packages:
                pkg.dispatch_id = 0  # 临时值，后续会更新为实际的dispatch_id
                updated_packages.append(pkg)
    
    return dispatch_list, updated_packages


def run_node_dispatch(db: Session, schedule_code: str, demo_mode: bool = False) -> Dict[str, Any]:
    """
    F005 节点间调度主函数
    
    Args:
        db: 数据库会话
        schedule_code: 全局调度方案编码
        demo_mode: 是否演示模式（跳过L1送达等待）
    
    Returns:
        调度结果字典，包含 batch_code, status, dispatches
    """
    # 1. 查询全局调度方案
    schedule = db.query(GlobalSchedule).filter(
        GlobalSchedule.schedule_code == schedule_code
    ).first()
    
    if not schedule:
        raise ValueError(f"全局调度方案不存在：{schedule_code}")
    
    # 加载算法配置
    config = _load_config()
    
    # 2. 第一次调用（L0→L1）
    try:
        l0_l1_dispatches, l0_l1_packages = _dispatch_level(
            db, schedule.id, 0, config
        )
    except Exception as e:
        raise ValueError(f"L0→L1调度失败：{str(e)}")
    
    if not l0_l1_dispatches:
        raise ValueError("L0→L1没有可调度的包裹")
    
    # 3. 创建调度批次
    batch_code = _generate_batch_code(db)
    batch = DispatchBatch(
        batch_code=batch_code,
        global_schedule_id=schedule.id,
        status='pending',
        demo_mode=demo_mode,
        l0_l1_dispatch_count=len(l0_l1_dispatches),
        l1_l2_dispatch_count=0,
    )
    db.add(batch)
    db.flush()  # 获取batch.id
    
    # 4. 写入第一次调用的调度明细
    for dispatch_data in l0_l1_dispatches:
        dispatch_code = _generate_dispatch_code(db)
        dispatch = NodeDispatch(
            dispatch_code=dispatch_code,
            dispatch_batch_id=batch.id,
            level_phase=0,
            vehicle_id=dispatch_data["vehicle_id"],
            driver_id=dispatch_data["driver_id"],
            tasks=dispatch_data["tasks"],
            total_distance=dispatch_data["total_distance"],
            total_time=dispatch_data["total_time"],
        )
        db.add(dispatch)
        db.flush()  # 获取dispatch.id
        
        # 更新包裹的dispatch_id
        for task in dispatch_data["tasks"]:
            if not task["is_return"]:
                for pkg_code in task["package_codes"]:
                    pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
                    if pkg:
                        pkg.dispatch_id = dispatch.id
                        pkg.status = 'in_transit'
    
    # 5. 更新批次状态为 l0_l1_done
    batch.status = 'l0_l1_done'
    
    # 6. 第二次调用（L1→L2）
    # 检查前置条件
    if demo_mode:
        # demo_mode=true：检查L0→L1是否已完成
        if batch.status != 'l0_l1_done':
            raise ValueError("L0→L1未完成，不能执行L1→L2")
    else:
        # demo_mode=false：检查所有L0→L1的包裹已送达
        # 暂时简化：直接执行第二次调用
        pass
    
    try:
        l1_l2_dispatches, l1_l2_packages = _dispatch_level(
            db, schedule.id, 1, config
        )
    except Exception as e:
        # 第二次调用失败，批次状态保持 l0_l1_done
        # 不提交事务，让服务层回滚
        raise ValueError(f"L1→L2调度失败：{str(e)}")
    
    # 7. 写入第二次调用的调度明细
    for dispatch_data in l1_l2_dispatches:
        dispatch_code = _generate_dispatch_code(db)
        dispatch = NodeDispatch(
            dispatch_code=dispatch_code,
            dispatch_batch_id=batch.id,
            level_phase=1,
            vehicle_id=dispatch_data["vehicle_id"],
            driver_id=dispatch_data["driver_id"],
            tasks=dispatch_data["tasks"],
            total_distance=dispatch_data["total_distance"],
            total_time=dispatch_data["total_time"],
        )
        db.add(dispatch)
        db.flush()
        
        # 更新包裹的dispatch_id
        for task in dispatch_data["tasks"]:
            if not task["is_return"]:
                for pkg_code in task["package_codes"]:
                    pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
                    if pkg:
                        pkg.dispatch_id = dispatch.id
                        pkg.status = 'in_transit'
    
    # 8. 更新批次状态为 completed
    batch.status = 'completed'
    batch.l1_l2_dispatch_count = len(l1_l2_dispatches)
    
    # 9. 返回结果
    return {
        "batch_code": batch.batch_code,
        "status": batch.status,
        "dispatches": l0_l1_dispatches + l1_l2_dispatches
    }


# 内存计数器
_batch_seq: int = 0
_batch_date: str = ""
_dispatch_seq: int = 0
_dispatch_date: str = ""

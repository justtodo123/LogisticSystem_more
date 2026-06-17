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
from models.goods import Goods
from models.order import Order

from services.state_machine import (
    update_state_after_f005,
    simulate_delivery_l0_to_l1,
    repack_at_l1,
    simulate_delivery_l1_to_l2,
    check_and_update_order_status
)


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
) -> Tuple[List[Dict[str, Any]], List[Package], List[Package]]:
    """
    执行一次节点调度（L0→L1 或 L1→L2）
    
    支持部分分配：如果车辆不足，只分配部分包裹，剩余包裹保持未分配状态
    
    Args:
        db: 数据库会话
        schedule_id: 全局调度方案ID
        level_phase: 层级阶段（0: L0→L1, 1: L1→L2）
        config: 算法配置
    
    Returns:
        (dispatch_list, updated_packages, unallocated_packages)
        - dispatch_list: 调度明细列表
        - updated_packages: 已分配并更新状态的包裹列表
        - unallocated_packages: 未分配的包裹列表（保持status=packed, dispatch_id=NULL）
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
        
        # 简化查询：使用 relationships
        packages = db.query(Package).filter(
            Package.status == 'packed',
            Package.schedule_id == schedule_id
        ).all()
        
        # 在 Python 中过滤（更可靠）
        filtered_packages = []
        for pkg in packages:
            # 直接使用 from_node_id 和 to_node_id 查询节点，避免关系属性延迟加载问题
            from_node = db.query(Node).filter(Node.id == pkg.from_node_id).first()
            to_node = db.query(Node).filter(Node.id == pkg.to_node_id).first()
            
            print(f"DEBUG filter: {pkg.package_code}, from_node={from_node.node_code if from_node else 'None'}, to_node={to_node.node_code if to_node else 'None'}")
            
            if not from_node or not to_node:
                print(f"  -> skipped: from_node or to_node is None")
                continue
            if from_node.node_type != 'storage_center':
                print(f"  -> skipped: from_node.node_type={from_node.node_type}")
                continue
            if to_node.node_type != 'sorting_center':
                print(f"  -> skipped: to_node.node_type={to_node.node_type}")
                continue
            # 检查 to_node 是否是 1 级分拣中心
            sorting_center = db.query(SortingCenter).filter(SortingCenter.node_id == to_node.id).first()
            if not sorting_center or sorting_center.level != 1:
                print(f"  -> skipped: to_node is not level 1 sorting center")
                continue
            print(f"  -> PASSED filter")
            filtered_packages.append(pkg)
        
        print(f"DEBUG: After filtering, found {len(filtered_packages)} packages")
        packages = filtered_packages
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
        return [], [], []  # dispatch_list, updated_packages, unallocated_packages
    
    # 2. 按 from_node_code 分组包裹（使用 node_id 查询，避免延迟加载问题）
    packages_by_from_node = defaultdict(list)
    for pkg in packages:
        from_node = db.query(Node).filter(Node.id == pkg.from_node_id).first()
        if from_node:
            packages_by_from_node[from_node.node_code].append(pkg)
    
    # 3. 对每个分组进行调度
    dispatch_list = []
    updated_packages = []
    unallocated_packages = []  # 未分配的包裹
    
    for from_node_code, node_packages in packages_by_from_node.items():
        # 获取起始节点
        from_node = db.query(Node).filter(Node.node_code == from_node_code).first()
        if not from_node:
            # 节点不存在，所有包裹都未分配
            unallocated_packages.extend(node_packages)
            continue
        
        # 按 to_node_code 分组包裹（同一目的节点的包裹可以一起运输）
        packages_by_to_node = defaultdict(list)
        for pkg in node_packages:
            to_node_code = pkg.to_node.node_code
            packages_by_to_node[to_node_code].append(pkg)
        
        # 对每个目的节点分组进行车辆分配
        # 按分组总重量排序（重量大的优先，减少剩余包裹总重量）
        sorted_to_nodes = sorted(
            packages_by_to_node.items(),
            key=lambda x: sum(float(pkg.weight) for pkg in x[1]),
            reverse=True
        )
        
        for to_node_code, to_packages in sorted_to_nodes:
            # 获取目的节点
            to_node = db.query(Node).filter(Node.node_code == to_node_code).first()
            if not to_node:
                # 节点不存在，该分组所有包裹都未分配
                unallocated_packages.extend(to_packages)
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
                # 车辆不足，该分组所有包裹都未分配
                unallocated_packages.extend(to_packages)
                continue  # 跳过该分组，继续处理其他分组
            
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
    
    return dispatch_list, updated_packages, unallocated_packages


def run_node_dispatch(db: Session, schedule_code: str, demo_mode: bool = False) -> Dict[str, Any]:
    """
    F005 节点间调度主函数
    
    自动检测是首次调用还是第二次调用：
    - 如果不存在 status=l0_l1_done 的批次 → 首次调用
    - 如果已存在 status=l0_l1_done 的批次 → 第二次调用
    
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
    
    # 2. 检测是否已有 l0_l1_done 的批次（用于判断是首次调用还是第二次调用）
    existing_batch = db.query(DispatchBatch).filter(
        DispatchBatch.global_schedule_id == schedule.id,
        DispatchBatch.status == 'l0_l1_done'
    ).first()
    
    # 3. 加载算法配置
    config = _load_config()
    
    # 4. 根据 demo_mode 和 existing_batch 决定执行逻辑
    if demo_mode:
        # demo_mode=true：一次完成两次调度（L0→L1 + L1→L2）
        return _run_dispatch_both_levels(db, schedule, config)
    
    else:
        # demo_mode=false：分阶段调度
        if existing_batch:
            # 第二次调用：只执行 L1→L2
            return _run_dispatch_l1_to_l2(db, schedule, existing_batch, config)
        else:
            # 首次调用：只执行 L0→L1
            return _run_dispatch_l0_to_l1(db, schedule, config)


def _run_dispatch_both_levels(db: Session, schedule, config: dict) -> Dict[str, Any]:
    """
    demo_mode=true 时的一次性调度（L0→L1 + L1→L2）
    
    Args:
        db: 数据库会话
        schedule: 全局调度方案对象
        config: 算法配置
    
    Returns:
        调度结果字典
    """
    # 1. 执行 L0→L1 调度
    # 先检查是否有状态为packed的包裹
    packed_packages_count = db.query(Package).filter(
        Package.status == 'packed',
        Package.schedule_id == schedule.id
    ).count()
    
    if packed_packages_count == 0:
        raise ValueError("L0→L1没有可调度的包裹")
    
    try:
        l0_l1_dispatches, _, unallocated_l0_l1 = _dispatch_level(db, schedule.id, 0, config)
    except Exception as e:
        raise ValueError(f"L0→L1调度失败：{str(e)}")
    
    # 调试：打印 l0_l1_dispatches 和 unallocated_l0_l1
    print(f"DEBUG _run_dispatch_both_levels: l0_l1_dispatches={l0_l1_dispatches}")
    print(f"DEBUG _run_dispatch_both_levels: unallocated_l0_l1={unallocated_l0_l1}")
    
    # 2. 创建调度批次（此时还没有 unallocated_l1_l2，先不保存 unallocated_packages）
    batch_code = _generate_batch_code(db)
    batch = DispatchBatch(
        batch_code=batch_code,
        global_schedule_id=schedule.id,
        status='pending',
        demo_mode=True,
        l0_l1_dispatch_count=len(l0_l1_dispatches),
        l1_l2_dispatch_count=0,
        unallocated_packages=json.dumps([pkg.package_code for pkg in unallocated_l0_l1], ensure_ascii=False) if unallocated_l0_l1 else None,
    )
    db.add(batch)
    db.flush()
    
    # 3. 写入 L0→L1 调度明细
    _write_dispatches(db, batch.id, l0_l1_dispatches, level_phase=0)
    
    # 4. 模拟 L0→L1 送达（demo_mode=true 自动推进）
    # 获取 L0→L1 的调度明细对象
    l0_l1_dispatch_objs = db.query(NodeDispatch).filter(
        NodeDispatch.dispatch_batch_id == batch.id,
        NodeDispatch.level_phase == 0
    ).all()
    
    for dispatch_obj in l0_l1_dispatch_objs:
        simulate_delivery_l0_to_l1(db, batch, dispatch_obj)
    
    # 5. 在 L1 重新打包
    # 获取所有相关的订单编码
    order_codes = set()
    for dispatch_data in l0_l1_dispatches:
        for task in dispatch_data["tasks"]:
            if not task["is_return"]:
                for pkg_code in task["package_codes"]:
                    pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
                    if pkg:
                        # 从包裹的goods_items中获取order_code
                        if pkg.goods_items:
                            for item in pkg.goods_items:
                                order_code = item.get('order_code')
                                if order_code:
                                    order_codes.add(order_code)
    
    # 为每个订单在L1重新打包
    for order_code in order_codes:
        # 获取该订单的L1和L2节点编码
        order = db.query(Order).filter(Order.order_code == order_code).first()
        if order:
            # 从global_schedules中获取L1和L2节点编码
            goods_schedules = schedule.goods_schedules if isinstance(schedule.goods_schedules, list) else json.loads(schedule.goods_schedules)
            for gs in goods_schedules:
                if gs.get('order_code') == order_code:
                    path = gs.get('path', [])
                    if len(path) >= 3:
                        l1_node_code = path[1]  # 第二个节点是L1
                        l2_node_code = path[2]  # 第三个节点是L2
                        repack_at_l1(db, order_code, l1_node_code, l2_node_code, schedule.id)
                        break
    
    # 6. 执行 L1→L2 调度
    try:
        l1_l2_dispatches, _, unallocated_l1_l2 = _dispatch_level(db, schedule.id, 1, config)
    except Exception as e:
        raise ValueError(f"L1→L2调度失败：{str(e)}")
    
    # 7. 写入 L1→L2 调度明细
    _write_dispatches(db, batch.id, l1_l2_dispatches, level_phase=1)
    
    # 8. 模拟 L1→L2 送达（demo_mode=true 自动推进）
    l1_l2_dispatch_objs = db.query(NodeDispatch).filter(
        NodeDispatch.dispatch_batch_id == batch.id,
        NodeDispatch.level_phase == 1
    ).all()
    
    for dispatch_obj in l1_l2_dispatch_objs:
        simulate_delivery_l1_to_l2(db, batch, dispatch_obj, list(order_codes))
    
    # 9. 更新批次状态为 completed
    batch.status = 'completed'
    batch.l1_l2_dispatch_count = len(l1_l2_dispatches)
    # 保存完整的 unallocated_packages
    all_unallocated = unallocated_l0_l1 + unallocated_l1_l2 if (unallocated_l0_l1 or unallocated_l1_l2) else []
    batch.unallocated_packages = json.dumps([pkg.package_code for pkg in all_unallocated], ensure_ascii=False) if all_unallocated else None
    
    # 10. 返回结果
    return {
        "batch_code": batch.batch_code,
        "status": batch.status,
        "dispatches": l0_l1_dispatches + l1_l2_dispatches,
        "unallocated_packages": [pkg.package_code for pkg in unallocated_l0_l1 + unallocated_l1_l2]
    }


def _run_dispatch_l0_to_l1(db: Session, schedule, config: dict) -> Dict[str, Any]:
    """
    demo_mode=false 时的首次调用（只执行 L0→L1）
    
    Args:
        db: 数据库会话
        schedule: 全局调度方案对象
        config: 算法配置
    
    Returns:
        调度结果字典
    """
    # 1. 执行 L0→L1 调度
    try:
        l0_l1_dispatches, _, unallocated_l0_l1 = _dispatch_level(db, schedule.id, 0, config)
    except Exception as e:
        raise ValueError(f"L0→L1调度失败：{str(e)}")
    
    if not l0_l1_dispatches:
        raise ValueError("L0→L1没有可调度的包裹")
    
    # 2. 创建调度批次
    batch_code = _generate_batch_code(db)
    batch = DispatchBatch(
        batch_code=batch_code,
        global_schedule_id=schedule.id,
        status='pending',
        demo_mode=False,
        l0_l1_dispatch_count=len(l0_l1_dispatches),
        l1_l2_dispatch_count=0,
        unallocated_packages=json.dumps([pkg.package_code for pkg in unallocated_l0_l1], ensure_ascii=False) if unallocated_l0_l1 else None,
    )
    db.add(batch)
    db.flush()
    
    # 3. 写入 L0→L1 调度明细
    _write_dispatches(db, batch.id, l0_l1_dispatches, level_phase=0)
    
    # 4. 更新批次状态为 l0_l1_done（等待模拟送达）
    batch.status = 'l0_l1_done'
    db.flush()  # 刷新到数据库，确保后续查询能看到更新后的状态
    
    # 5. 返回结果（只包含 L0→L1 的调度明细）
    return {
        "batch_code": batch.batch_code,
        "status": batch.status,
        "dispatches": l0_l1_dispatches,
        "unallocated_packages": [pkg.package_code for pkg in unallocated_l0_l1],
        "message": "L0→L1调度完成，请等待模拟送达后再次调用以执行L1→L2"
    }


def _run_dispatch_l1_to_l2(db: Session, schedule, existing_batch, config: dict) -> Dict[str, Any]:
    """
    demo_mode=false 时的第二次调用（只执行 L1→L2）
    
    Args:
        db: 数据库会话
        schedule: 全局调度方案对象
        existing_batch: 已存在的调度批次（status=l0_l1_done）
        config: 算法配置
    
    Returns:
        调度结果字典
    """
    # 1. 执行 L1→L2 调度
    try:
        l1_l2_dispatches, _, unallocated_l1_l2 = _dispatch_level(db, schedule.id, 1, config)
    except Exception as e:
        raise ValueError(f"L1→L2调度失败：{str(e)}")
    
    if not l1_l2_dispatches:
        raise ValueError("L1→L2没有可调度的包裹")
    
    # 2. 写入 L1→L2 调度明细
    _write_dispatches(db, existing_batch.id, l1_l2_dispatches, level_phase=1)
    
    # 3. 更新批次状态为 completed
    existing_batch.status = 'completed'
    existing_batch.l1_l2_dispatch_count = len(l1_l2_dispatches)
    existing_batch.unallocated_packages = json.dumps([pkg.package_code for pkg in unallocated_l1_l2], ensure_ascii=False) if unallocated_l1_l2 else None
    db.flush()  # 刷新到数据库，确保状态更新被正确保存
    
    # 4. 返回结果（只包含 L1→L2 的调度明细）
    return {
        "batch_code": existing_batch.batch_code,
        "status": existing_batch.status,
        "dispatches": l1_l2_dispatches,
        "unallocated_packages": [pkg.package_code for pkg in unallocated_l1_l2],
        "message": "L1→L2调度完成，整个节点调度流程结束"
    }


def _write_dispatches(db: Session, batch_id: int, dispatches: list, level_phase: int):
    """
    写入调度明细并更新状态
    
    Args:
        db: 数据库会话
        batch_id: 调度批次ID
        dispatches: 调度明细列表
        level_phase: 层级阶段（0: L0→L1, 1: L1→L2）
    """
    for dispatch_data in dispatches:
        dispatch_code = _generate_dispatch_code(db)
        dispatch = NodeDispatch(
            dispatch_code=dispatch_code,
            dispatch_batch_id=batch_id,
            level_phase=level_phase,
            vehicle_id=dispatch_data["vehicle_id"],
            driver_id=dispatch_data["driver_id"],
            tasks=dispatch_data["tasks"],
            total_distance=dispatch_data["total_distance"],
            total_time=dispatch_data["total_time"],
        )
        db.add(dispatch)
        db.flush()
        
        # 收集所有包裹编码
        package_codes = []
        for task in dispatch_data["tasks"]:
            if not task["is_return"]:
                for pkg_code in task["package_codes"]:
                    pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
                    if pkg:
                        pkg.dispatch_id = dispatch.id
                        package_codes.append(pkg_code)
        
        # 调用状态机更新状态（货物、车辆、司机）
        update_state_after_f005(db, dispatch, package_codes)


# 内存计数器
_batch_seq: int = 0
_batch_date: str = ""
_dispatch_seq: int = 0
_dispatch_date: str = ""

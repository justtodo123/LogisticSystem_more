"""
F021 打包算法

将 F007 输出的货物调度计划打包为包裹：
- L0 → L1：按 (from_node_code, to_node_code) 节点对打包

注意：L1→L2 包裹不在初始 F021 中生成，而是在 confirm-arrival 触发
_trigger_repacking 时按 order_code 动态创建。这符合 P1-3 规范：
"L1→L2 包裹在 confirm-arrival 后才生成"。
"""
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from models.package import Package
from models.node import Node
from models.goods import Goods
from models.vehicle import Vehicle

def get_min_vehicle_capacity(db: Session) -> float:
    """
    获取系统中最小车辆载重（用于限制L0→L1包裹重量）
    
    返回：
        float: 最小车辆载重（kg），如果没有车辆则返回默认值1000kg
    """
    min_capacity = db.query(Vehicle.capacity).order_by(Vehicle.capacity.asc()).first()
    if min_capacity:
        return float(min_capacity[0])
    return 1000.0  # 默认最小值


def _generate_package_code(db: Session, _local_counter: dict) -> str:
    """
    生成包裹编号，格式：PKG + YYYYMMDD + 4位序号
    
    使用局部计数器（传入的字典）在事务内生成唯一编码，
    同时查询数据库获取跨事务的最大序号，避免重复
    
    Args:
        db: 数据库会话
        _local_counter: 局部计数器字典，格式：{"date": "YYYYMMDD", "seq": int}
                       在单个 packaging() 调用中共享，跨调用不共享
    """
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"PKG{today_str}"
    
    # 如果是新的一天，或者首次调用，从数据库查询最大序号
    if _local_counter.get("date") != today_str:
        max_record = (
            db.query(Package.package_code)
            .filter(Package.package_code.like(f"{prefix}%"))
            .order_by(Package.package_code.desc())
            .first()
        )
        if max_record and max_record[0]:
            _local_counter["seq"] = int(max_record[0][-4:])
        else:
            _local_counter["seq"] = 0
        _local_counter["date"] = today_str
    
    # 递增序号
    _local_counter["seq"] += 1
    return f"{prefix}{_local_counter['seq']:04d}"


def packaging(
    schedule_result: Dict[str, Any],
    schedule_id: int,
    db: Session,
    is_replan: bool = False,
) -> List[Package]:
    """
    F021 打包算法

    根据 F007 输出的 goods_schedules，生成 L0→L1 包裹（按节点对分组）。
    L1→L2 包裹不在初始 F021 中生成，而是在 confirm-arrival 触发 repacking 时创建。

    Args:
        schedule_result: F007 输出的调度结果，必须包含 "goods_schedules"
        schedule_id: 关联的 global_schedules.id（可为 None，由调用方后续赋值）
        db: 数据库会话
        is_replan: 是否为重规划模式（True=允许打包 exception 状态货物，False=只打包 pending_pack 货物）

    Returns:
        Package 对象列表（未写入数据库，由调用方统一写入）
    """
    # 初始化局部计数器（在单个 packaging() 调用中共享，跨调用不共享）
    counter = {"date": "", "seq": 0}
    
    goods_schedules = schedule_result.get("goods_schedules", [])
    if not goods_schedules:
        raise ValueError("goods_schedules 为空，无法打包")

    packages: List[Package] = []

    # 预加载 goods_code → Goods 映射（避免逐个查询）
    # 正常模式：只加载待打包状态的货物，防止已打包/运输中/已送达的货物被重复打包
    # 重规划模式：加载异常状态的货物
    all_goods_codes = [gs["goods_code"] for gs in goods_schedules]
    goods_map: Dict[str, Goods] = {}
    for gc in all_goods_codes:
        goods = db.query(Goods).filter(
            Goods.goods_code == gc,
            Goods.status == ("exception" if is_replan else "pending_pack")
        ).first()
        if goods:
            goods_map[gc] = goods

    # 预加载 node_code → Node 映射
    all_node_codes = set()
    for gs in goods_schedules:
        for code in gs["path"]:
            all_node_codes.add(code)
    node_map: Dict[str, Node] = {}
    for nc in all_node_codes:
        node = db.query(Node).filter(Node.node_code == nc).first()
        if node:
            node_map[nc] = node

    def _sum_weight_volume(gs_list: list) -> tuple:
        """计算一组货物的总重量和总体积"""
        total_w = 0.0
        total_v = 0.0
        for gs in gs_list:
            g = goods_map.get(gs["goods_code"])
            if g:
                total_w += float(g.weight)
                total_v += float(g.volume)
        return total_w, total_v

    def _make_goods_items(gs_list: list) -> list:
        """生成 goods_items JSON"""
        return [
            {"goods_code": gs["goods_code"], "order_code": gs["order_code"]}
            for gs in gs_list
        ]

    # ── 1. L0 → L1 打包：按 (L0_code, L1_code) 节点对分组，并按重量拆分 ──
    # 获取最小车辆载重作为包裹重量上限
    min_vehicle_capacity = get_min_vehicle_capacity(db)
    
    l0_l1_groups: Dict[tuple, list] = defaultdict(list)
    for gs in goods_schedules:
        key = (gs["path"][0], gs["path"][1])  # (L0_code, L1_code)
        l0_l1_groups[key].append(gs)

    for (from_code, to_code), gs_list in l0_l1_groups.items():
        from_node = node_map.get(from_code)
        to_node = node_map.get(to_code)
        if not from_node or not to_node:
            continue

        # 按重量拆分包裹：每个子包裹重量不超过最小车辆载重
        current_group = []
        current_weight = 0.0
        
        for gs in gs_list:
            g = goods_map.get(gs["goods_code"])
            if not g:
                continue
            goods_weight = float(g.weight)
            
            # 如果单个货物就超过重量上限，仍然单独打包（会在车辆分配时报错）
            if goods_weight > min_vehicle_capacity:
                # 单独打包这个超重货物
                pkg = Package(
                    package_code=_generate_package_code(db, counter),
                    weight=round(goods_weight, 3),
                    volume=round(float(g.volume), 3),
                    status="packed",
                    from_node_id=from_node.id,
                    to_node_id=to_node.id,
                    from_longitude=from_node.longitude,
                    from_latitude=from_node.latitude,
                    to_longitude=to_node.longitude,
                    to_latitude=to_node.latitude,
                    goods_items=[{"goods_code": gs["goods_code"], "order_code": gs["order_code"]}],
                    schedule_id=schedule_id,
                )
                packages.append(pkg)
            elif current_weight + goods_weight > min_vehicle_capacity and current_group:
                # 当前分组已满，先打包当前分组
                total_weight, total_volume = _sum_weight_volume(current_group)
                pkg = Package(
                    package_code=_generate_package_code(db, counter),
                    weight=round(total_weight, 3),
                    volume=round(total_volume, 3),
                    status="packed",
                    from_node_id=from_node.id,
                    to_node_id=to_node.id,
                    from_longitude=from_node.longitude,
                    from_latitude=from_node.latitude,
                    to_longitude=to_node.longitude,
                    to_latitude=to_node.latitude,
                    goods_items=_make_goods_items(current_group),
                    schedule_id=schedule_id,
                )
                packages.append(pkg)
                # 开始新分组
                current_group = [gs]
                current_weight = goods_weight
            else:
                # 添加到当前分组
                current_group.append(gs)
                current_weight += goods_weight
        
        # 打包剩余的分组
        if current_group:
            total_weight, total_volume = _sum_weight_volume(current_group)
            pkg = Package(
                package_code=_generate_package_code(db, counter),
                weight=round(total_weight, 3),
                volume=round(total_volume, 3),
                status="packed",
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                from_longitude=from_node.longitude,
                from_latitude=from_node.latitude,
                to_longitude=to_node.longitude,
                to_latitude=to_node.latitude,
                goods_items=_make_goods_items(current_group),
                schedule_id=schedule_id,
            )
            packages.append(pkg)

    return packages

"""
F007 全局调度算法

贪心策略：为每票货物选择评分最低的 1 级分拣中心，规划 L0 → L1 → L2 路径。
硬约束：L1 容量、同订单汇聚、最大存储时长。
"""
import math
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from models.node import Node
from models.sorting_center import SortingCenter
from models.order import Order
from models.goods import Goods
from models.package import Package


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


def _calculate_storage_time(
    l0_node: Node, l1_node: Node, l2_node: Node
) -> float:
    """
    预估货物在 L1 节点的存储时长（小时）

    简化模型：存储时长与 L0→L1 距离正相关（假设配送频率与距离相关）。
    实际业务中可能需要更复杂的模型。

    Returns:
        预估存储时长（小时）
    """
    distance_l0_l1 = _haversine(
        float(l0_node.latitude), float(l0_node.longitude),
        float(l1_node.latitude), float(l1_node.longitude),
    )
    # 基础存储时间 2 小时 + 每 100 公里额外 1 小时
    return 2.0 + distance_l0_l1 / 100.0


# 内存计数器
_schedule_seq: int = 0
_schedule_date: str = ""


def _generate_schedule_code(db: Session) -> str:
    """生成调度方案编号，格式：GS + YYYYMMDD + 3位序号"""
    global _schedule_seq, _schedule_date
    today_str = datetime.now().strftime("%Y%m%d")
    if _schedule_date != today_str:
        _schedule_date = today_str
        from models.global_schedule import GlobalSchedule
        prefix = f"GS{today_str}"
        max_record = (
            db.query(GlobalSchedule.schedule_code)
            .filter(GlobalSchedule.schedule_code.like(f"{prefix}%"))
            .order_by(GlobalSchedule.schedule_code.desc())
            .first()
        )
        if max_record and max_record[0]:
            _schedule_seq = int(max_record[0][-3:])
        else:
            _schedule_seq = 0
    _schedule_seq += 1
    return f"GS{today_str}{_schedule_seq:03d}"


def global_schedule(
    order_codes: Optional[List[str]],
    algorithm: str,
    db: Session,
    excluded_nodes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    F007 全局调度算法

    Args:
        order_codes: 订单编号列表（可选，None 则处理所有 pending 订单）
        algorithm: 算法类型（"traditional" 或 "deepseek"，阶段3仅实现 traditional）
        db: 数据库会话

    Returns:
        dict: {
            "schedule_code": str,
            "order_codes": List[str],
            "total_distance": float,
            "total_time": float,
            "total_goods": int,
            "score": float,
            "goods_schedules": List[dict],
        }

    Raises:
        ValueError: 无法为某货物找到满足条件的 L1 节点
    """
    if algorithm != "traditional":
        raise ValueError(f"阶段3仅支持 traditional 算法，收到: {algorithm}")

    # 加载配置
    config = _load_config()
    weights = config["global_schedule_weights"]
    w1 = weights["w1_distance"]
    w2 = weights["w2_time"]
    w3 = weights["w3_packages"]

    # ── 1. 查询订单 ──
    # 允许 pending 和 exception 状态的订单参与调度
    # - pending: 正常待调度订单
    # - exception: 异常重规划时需要重新调度的订单
    query = db.query(Order).filter(Order.status.in_(["pending", "exception"]))
    if order_codes:
        query = query.filter(Order.order_code.in_(order_codes))
    orders = query.all()

    if not orders:
        raise ValueError("没有找到符合条件的订单（status=pending 或 status=exception）")

    # ── 2. 预加载 L1 节点（含 sorting_center 属性） ──
    l1_nodes = (
        db.query(Node)
        .join(SortingCenter, Node.id == SortingCenter.node_id)
        .filter(
            Node.node_type == "sorting_center",
            SortingCenter.level == 1,
        )
        .all()
    )
    if not l1_nodes:
        raise ValueError("没有找到 1 级分拣中心（L1），请先初始化演示数据")

    # 为每个 L1 节点附加 sorting_center 属性便于访问
    l1_node_map = {}
    for node in l1_nodes:
        sc = db.query(SortingCenter).filter(SortingCenter.node_id == node.id).first()
        l1_node_map[node.id] = sc

    # ── 3. 遍历订单和货物，贪心选择 L1 ──
    goods_schedules = []
    order_l1_map: Dict[str, str] = {}  # order_code → l1_node_code
    total_distance = 0.0
    total_time = 0.0

    for order in orders:
        for goods in order.goods:
            # 2a. 获取 L0 节点（货物所在存储中心）
            l0_node = db.query(Node).filter(Node.id == goods.node_id).first()
            if not l0_node:
                raise ValueError(f"货物 {goods.goods_code} 的起点节点不存在 (node_id={goods.node_id})")

            # 2b. 获取 L2 节点（订单目的地，0 级分拣中心）
            l2_node = db.query(Node).filter(Node.id == order.destination_node_id).first()
            if not l2_node:
                raise ValueError(f"订单 {order.order_code} 的目的地节点不存在 (node_id={order.destination_node_id})")

            # 2c. 遍历 L1 节点，选择评分最低的
            best_l1 = None
            best_l1_sc = None
            best_score = float("inf")

            for l1_node in l1_nodes:
                # 新增：排除异常节点
                if excluded_nodes and l1_node.node_code in excluded_nodes:
                    continue

                l1_sc = l1_node_map.get(l1_node.id)
                if not l1_sc:
                    continue

                # ---- 硬约束 1：L1 容量检查（到达 L1 的 packed 包裹数 + 1 > capacity） ----
                packed_count = (
                    db.query(Package)
                    .filter(
                        Package.to_node_id == l1_node.id,
                        Package.status == "packed",
                    )
                    .count()
                )
                if l1_sc.capacity is not None and packed_count + 1 > l1_sc.capacity:
                    continue

                # ---- 硬约束 2：同订单汇聚 ----
                if order.order_code in order_l1_map:
                    if order_l1_map[order.order_code] != l1_node.node_code:
                        continue

                # ---- 硬约束 3：最大存储时长 ----
                estimated_hours = _calculate_storage_time(l0_node, l1_node, l2_node)
                if l1_sc.max_storage_time is not None:
                    if float(goods.volume) * estimated_hours > l1_sc.max_storage_time:
                        continue

                # ---- 计算评分 ----
                dist_l0_l1 = _haversine(
                    float(l0_node.latitude), float(l0_node.longitude),
                    float(l1_node.latitude), float(l1_node.longitude),
                )
                # 时间估算：基于距离 / 平均速度 60 km/h
                time_est = dist_l0_l1 / 60.0 + estimated_hours
                score = w1 * dist_l0_l1 + w2 * time_est + w3 * 1.0

                if score < best_score:
                    best_score = score
                    best_l1 = l1_node
                    best_l1_sc = l1_sc

            # 2d. 记录结果
            if best_l1 is None:
                raise ValueError(
                    f"无法为货物 {goods.goods_code}（订单 {order.order_code}）"
                    f"找到满足所有硬约束的 L1 分拣中心"
                )

            path = [l0_node.node_code, best_l1.node_code, l2_node.node_code]
            goods_schedules.append({
                "goods_code": goods.goods_code,
                "order_code": order.order_code,
                "path": path,
            })

            # 记录同订单汇聚映射
            order_l1_map[order.order_code] = best_l1.node_code

            # 累计距离和时间
            dist_l0_l1 = _haversine(
                float(l0_node.latitude), float(l0_node.longitude),
                float(best_l1.latitude), float(best_l1.longitude),
            )
            dist_l1_l2 = _haversine(
                float(best_l1.latitude), float(best_l1.longitude),
                float(l2_node.latitude), float(l2_node.longitude),
            )
            total_distance += dist_l0_l1 + dist_l1_l2
            total_time += (dist_l0_l1 + dist_l1_l2) / 60.0 + _calculate_storage_time(
                l0_node, best_l1, l2_node
            )

    # ── 4. 计算结果 ──
    goods_count = len(goods_schedules)
    # 整体评分：所有货物评分之和（归一化）
    overall_score = round(total_distance * w1 + total_time * w2 + goods_count * w3, 4)

    schedule_code = _generate_schedule_code(db)
    involved_order_codes = list(dict.fromkeys(gs["order_code"] for gs in goods_schedules))

    return {
        "schedule_code": schedule_code,
        "order_codes": involved_order_codes,
        "total_distance": round(total_distance, 3),
        "total_time": round(total_time, 3),
        "total_goods": goods_count,
        "score": overall_score,
        "goods_schedules": goods_schedules,
    }

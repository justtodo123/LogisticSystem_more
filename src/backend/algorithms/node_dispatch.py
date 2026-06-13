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
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from models.node import Node
from models.package import Package
from models.vehicle import Vehicle
from models.driver import Driver
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch


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
    
    from models.dispatch_batch import DispatchBatch
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
    
    from models.node_dispatch import NodeDispatch
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
    # TODO: 实现 F005 算法
    # 1. 查询全局调度方案
    # 2. 第一次调用（L0→L1）
    # 3. 第二次调用（L1→L2）
    # 4. 返回结果
    
    raise NotImplementedError("F005 算法尚未实现")


# 内存计数器
_batch_seq: int = 0
_batch_date: str = ""
_dispatch_seq: int = 0
_dispatch_date: str = ""

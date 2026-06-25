"""
状态机服务 - 管理物流系统中的所有状态流转

所有状态变更必须通过本模块的函数完成，算法层和服务层不直接修改 .status 字段。

状态流转规则（P1-3 版本）：
0. P1-2 调度方案生命周期:
   - 预览创建 → global_schedules.status = draft（仅存方案，不执行打包/状态更新）
   - 确认确认 → draft → active（执行 F021 + 状态更新）
   - 丢弃 draft → 物理删除记录（返回 "discarded" 瞬态值）
   - active 方案不可变（immutable）
1. F007完成 → 订单状态: pending/exception → delivering
2. F021完成 → 货物状态: pending_pack/exception → packed
               包裹状态: L0→L1: pending_pack → packed
                          L1→L2: 新建时 status=pending_pack（激活前不变）
3. F005调用 → 货物状态: packed → in_transit; 包裹状态: packed → in_transit;
               车辆状态: idle → delivering; 司机状态: idle → busy
4. simulate_delivery（P1-3 语义）→ 包裹: in_transit → delivered
                                    货物: node_id 更新，status 保持 in_transit（不改变）
                                    车辆: delivering → idle; 司机: busy → idle
5. confirm-arrival（正常→L1）→ 货物: in_transit → pending_pack（触发 L1 重新打包）
                                   L1→L2包裹: pending_pack → packed（F021 激活）
6. confirm-arrival（正常→L2）→ 货物: in_transit → delivered
                               订单: delivering → completed（全部货物送达后）
7. confirm-arrival（异常）→ 包裹/货物/订单 → exception; 写入 exception_events
8. 批次状态流转: pending → l0_l1_done（L0→L1 confirm 完成）→ completed/failed
9. 异常事件创建 → 关联订单/货物/包裹 → exception; 关联车辆 → disabled
10. 重规划 → 旧方案包裹 → exception; 旧批次 → failed; 新方案重新走1-8
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import Order, Goods, Package, Vehicle, Driver, DispatchBatch, NodeDispatch, Node
from models.global_schedule import GlobalSchedule
from models.package import Package
from algorithms.packaging import packaging


# ══════════════════════════════════════════════════════════════════════
# 合法状态转换映射（所有 7 个实体）
# ══════════════════════════════════════════════════════════════════════

ORDER_TRANSITIONS = {
    "pending":    ["delivering", "exception"],
    "delivering": ["completed", "exception"],
    "completed":  [],
    "exception":  ["delivering"],  # 重规划恢复
}

GOODS_TRANSITIONS = {
    "pending_pack": ["packed", "exception"],
    "packed":       ["in_transit", "exception"],
    "in_transit":   ["pending_pack", "delivered", "exception"],
    "delivered":    [],
    "exception":    ["pending_pack", "packed", "in_transit"],  # 重规划重置 / F021恢复 / F005直转
}

PACKAGE_TRANSITIONS = {
    "pending_pack": ["packed", "exception"],
    "packed":       ["in_transit", "exception"],
    "in_transit":   ["delivered", "exception"],
    "delivered":    ["exception"],     # confirm-arrival 异常路径
    "exception":    ["pending_pack"],  # 重规划重置
}

BATCH_TRANSITIONS = {
    "pending":      ["l0_l1_done", "completed", "failed"],
    "l0_l1_done":   ["completed", "failed"],
    "completed":    [],
    "failed":       [],
}

SCHEDULE_TRANSITIONS = {
    "draft":  ["active"],
    "active": [],
}

VEHICLE_TRANSITIONS = {
    "idle":        ["delivering", "maintenance", "disabled"],
    "delivering":  ["idle", "disabled"],
    "maintenance": ["idle"],
    "disabled":    [],
}

DRIVER_TRANSITIONS = {
    "idle": ["busy"],
    "busy": ["idle"],
}

# 所有转换映射的查找表
_ALL_TRANSITIONS = {
    "order":     ORDER_TRANSITIONS,
    "goods":     GOODS_TRANSITIONS,
    "package":   PACKAGE_TRANSITIONS,
    "batch":     BATCH_TRANSITIONS,
    "schedule":  SCHEDULE_TRANSITIONS,
    "vehicle":   VEHICLE_TRANSITIONS,
    "driver":    DRIVER_TRANSITIONS,
}


# ══════════════════════════════════════════════════════════════════════
# 内部校验工具
# ══════════════════════════════════════════════════════════════════════

def _validate(transitions: dict, current: str, target: str, entity: str) -> None:
    """校验状态转换合法性，不合法时抛出 ValueError"""
    if current == target:
        return  # 幂等跳过
    allowed = transitions.get(current, [])
    if target not in allowed:
        raise ValueError(
            f"非法{entity}状态转换: {current} → {target}，"
            f"允许的目标状态: {allowed}"
        )


# ══════════════════════════════════════════════════════════════════════
# 统一状态转换函数（供外部服务调用）
# ══════════════════════════════════════════════════════════════════════

def transition_order_status(db: Session, order: Order, new_status: str, force: bool = False) -> None:
    """统一更新订单状态，含合法性校验"""
    if not force:
        _validate(ORDER_TRANSITIONS, order.status, new_status, "订单")
    if order.status != new_status:
        order.status = new_status
        db.flush()


def transition_goods_status(db: Session, goods: Goods, new_status: str, force: bool = False) -> None:
    """统一更新货物状态，含合法性校验"""
    if not force:
        _validate(GOODS_TRANSITIONS, goods.status, new_status, "货物")
    if goods.status != new_status:
        goods.status = new_status
        db.flush()


def transition_package_status(db: Session, package: Package, new_status: str, force: bool = False) -> None:
    """统一更新包裹状态，含合法性校验"""
    if not force:
        _validate(PACKAGE_TRANSITIONS, package.status, new_status, "包裹")
    if package.status != new_status:
        package.status = new_status
        db.flush()


def transition_vehicle_status(db: Session, vehicle: Vehicle, new_status: str, force: bool = False) -> None:
    """统一更新车辆状态，含合法性校验"""
    if not force:
        _validate(VEHICLE_TRANSITIONS, vehicle.status, new_status, "车辆")
    if vehicle.status != new_status:
        vehicle.status = new_status
        db.flush()


def transition_driver_status(db: Session, driver: Driver, new_status: str, force: bool = False) -> None:
    """统一更新司机状态，含合法性校验"""
    if not force:
        _validate(DRIVER_TRANSITIONS, driver.status, new_status, "司机")
    if driver.status != new_status:
        driver.status = new_status
        db.flush()


# ══════════════════════════════════════════════════════════════════════
# 业务流程状态更新函数
# ══════════════════════════════════════════════════════════════════════

def update_state_after_f005(
    db: Session,
    dispatch: NodeDispatch,
    package_codes: List[str]
) -> None:
    """
    F005调用后的状态更新
    
    更新以下状态：
    - 货物状态: packed → in_transit
    - 包裹状态: packed → in_transit
    - 车辆状态: idle → delivering
    - 司机状态: idle → busy
    
    Args:
        db: 数据库会话
        dispatch: 调度明细对象
        package_codes: 包裹编码列表
    """
    # 1. 更新包裹状态和货物状态
    for pkg_code in package_codes:
        pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
        if pkg:
            transition_package_status(db, pkg, 'in_transit')
            
            # 2. 更新货物状态（通过package的goods_items）
            if pkg.goods_items:
                items = pkg.goods_items
                if isinstance(items, str):
                    import json
                    items = json.loads(items)
                for item in items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            transition_goods_status(db, goods, 'in_transit')
    
    # 3. 更新车辆状态
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle:
        transition_vehicle_status(db, vehicle, 'delivering')
    
    # 4. 更新司机状态
    driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
    if driver:
        transition_driver_status(db, driver, 'busy')
    
    db.flush()


def simulate_delivery_l0_to_l1(
    db: Session,
    batch: DispatchBatch,
    dispatch: NodeDispatch
) -> None:
    """
    模拟L0→L1送达
    
    更新以下状态：
    - L0→L1包裹: in_transit → delivered
    - 货物状态: in_transit → pending_pack
    - L1→L2包裹: pending_pack（不变，等待L1重新打包激活）
    - 批次状态: pending/l0_l1_done → l0_l1_done
    - 车辆状态: delivering → idle
    - 司机状态: busy → idle
    
    Args:
        db: 数据库会话
        batch: 调度批次对象
        dispatch: 调度明细对象
    """
    # 1. 获取该调度明细的所有包裹
    package_codes = []
    for task in dispatch.tasks:
        if isinstance(task, str):
            import json
            task = json.loads(task)
        if not task.get('is_return', False):
            package_codes.extend(task.get('package_codes', []))
    
    # 2. 更新包裹状态（仅L0→L1的包裹）
    for pkg_code in package_codes:
        pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
        if pkg:
            transition_package_status(db, pkg, 'delivered')
            
            # 3. 更新货物状态
            items = pkg.goods_items
            if isinstance(items, str):
                import json
                items = json.loads(items)
            if items:
                for item in items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            transition_goods_status(db, goods, 'pending_pack')
    
    # 4. 更新批次状态（使用统一函数）
    update_batch_status(db, batch, 'l0_l1_done')
    
    # 5. 更新车辆状态
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle:
        transition_vehicle_status(db, vehicle, 'idle')
    
    # 6. 更新司机状态
    driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
    if driver:
        transition_driver_status(db, driver, 'idle')
    
    db.flush()


def repack_at_l1(
    db: Session,
    order_code: str,
    l1_node_code: str,
    l2_node_code: str,
    schedule_id: int = None
) -> Dict[str, Any]:
    """
    在L1分拣中心重新打包
    
    更新以下状态：
    - 货物状态: pending_pack → packed
    - 创建新包裹: status = packed
    
    Args:
        db: 数据库会话
        order_code: 订单编码
        l1_node_code: L1分拣中心编码
        l2_node_code: L2存储中心/门店编码
        schedule_id: 全局调度方案ID（可选）
    
    Returns:
        字典，包含新创建的包裹列表和层级信息
    """
    from datetime import datetime
    
    # 1. 查询订单
    order = db.query(Order).filter(Order.order_code == order_code).first()
    if not order:
        return []
    
    # 2. 查询该订单的所有货物，状态为 pending_pack
    goods_list = db.query(Goods).filter(
        Goods.order_id == order.id,
        Goods.status == 'pending_pack'
    ).all()
    
    if not goods_list:
        return []
    
    # 3. 获取L1和L2节点
    l1_node = db.query(Node).filter(Node.node_code == l1_node_code).first()
    l2_node = db.query(Node).filter(Node.node_code == l2_node_code).first()
    
    if not l1_node or not l2_node:
        return []
    
    # 4. 检查是否已有F021生成的L1→L2包裹（重用，避免重复）
    existing_package = None
    if schedule_id:
        all_matching = db.query(Package).filter(
            Package.schedule_id == schedule_id,
            Package.status.in_(['packed', 'pending_pack']),
            Package.from_node_id == l1_node.id,
            Package.to_node_id == l2_node.id
        ).all()
        
        # 优先匹配 goods_items 中包含当前 order_code 的包裹
        for pkg in all_matching:
            items = pkg.goods_items
            if isinstance(items, str):
                import json
                items = json.loads(items)
            if items:
                for item in items:
                    if item.get('order_code') == order_code:
                        existing_package = pkg
                        break
            if existing_package:
                break
        
        # 兜底：若 goods_items 中未匹配到（兼容旧数据），使用第一个 pending_pack 包裹
        if not existing_package:
            for pkg in all_matching:
                if pkg.status == 'pending_pack':
                    existing_package = pkg
                    break
            if not existing_package and all_matching:
                existing_package = all_matching[0]
    
    if existing_package:
        # 重用现有包裹：F021已正确设置了goods_items，只需更新状态
        transition_package_status(db, existing_package, 'packed')
        
        # 更新货物状态：pending_pack → packed
        for goods in goods_list:
            transition_goods_status(db, goods, 'packed')
        
        db.flush()
        
        return {
            "new_packages": [existing_package],
            "level_info": {
                "level_phase": 1,
                "description": "L1→L2重新打包（重用F021包裹）"
            }
        }
    else:
        # 5. 计算总重量和总体积
        total_weight = sum(float(g.weight) for g in goods_list)
        total_volume = sum(float(g.volume) for g in goods_list)
        
        # 6. 生成包裹编号
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"PKG{today_str}"
        
        max_record = (
            db.query(Package.package_code)
            .filter(Package.package_code.like(f"{prefix}%"))
            .order_by(Package.package_code.desc())
            .first()
        )
        
        if max_record and max_record[0]:
            seq = int(max_record[0][-4:]) + 1
        else:
            seq = 1
        
        package_code = f"{prefix}{seq:04d}"
        
        # 7. 创建goods_items
        goods_items = [
            {"goods_code": g.goods_code, "order_code": order_code}
            for g in goods_list
        ]
        
        # 8. 创建新包裹（构造时设 packed，无需 transition）
        new_package = Package(
            package_code=package_code,
            weight=round(total_weight, 3),
            volume=round(total_volume, 3),
            status="packed",
            from_node_id=l1_node.id,
            to_node_id=l2_node.id,
            from_longitude=l1_node.longitude,
            from_latitude=l1_node.latitude,
            to_longitude=l2_node.longitude,
            to_latitude=l2_node.latitude,
            goods_items=goods_items,
            schedule_id=schedule_id,
        )
        
        db.add(new_package)
        db.flush()
        
        # 9. 更新货物状态
        for goods in goods_list:
            transition_goods_status(db, goods, 'packed')
        
        db.flush()
        
        return {
            "new_packages": [new_package],
            "level_info": {
                "level_phase": 1,
                "description": "L1→L2重新打包"
            }
        }


def simulate_delivery_l1_to_l2(
    db: Session,
    batch: DispatchBatch,
    dispatch: NodeDispatch,
    order_codes: List[str]
) -> None:
    """
    模拟L1→L2送达
    
    更新以下状态：
    - 包裹状态: in_transit → delivered
    - 货物状态: in_transit → delivered
    - 订单状态: delivering → completed
    - 批次状态: l0_l1_done → completed
    - 车辆状态: delivering → idle
    - 司机状态: busy → idle
    
    Args:
        db: 数据库会话
        batch: 调度批次对象
        dispatch: 调度明细对象
        order_codes: 订单编码列表
    """
    # 1. 获取该调度明细的所有包裹
    package_codes = []
    for task in dispatch.tasks:
        if isinstance(task, str):
            import json
            task = json.loads(task)
        if not task.get('is_return', False):
            package_codes.extend(task.get('package_codes', []))
    
    # 2. 更新包裹状态
    for pkg_code in package_codes:
        pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
        if pkg:
            transition_package_status(db, pkg, 'delivered')
            
            # 3. 更新货物状态
            items = pkg.goods_items
            if isinstance(items, str):
                import json
                items = json.loads(items)
            if items:
                for item in items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            transition_goods_status(db, goods, 'delivered')
    
    # 4. 更新订单状态（仅当该订单所有货物都已 delivered 时才设为 completed）
    for order_code in order_codes:
        check_and_update_order_status(db, order_code)
    
    # 5. 更新车辆状态
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle:
        transition_vehicle_status(db, vehicle, 'idle')
    
    # 6. 更新司机状态
    driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
    if driver:
        transition_driver_status(db, driver, 'idle')
    
    db.flush()


def check_and_update_order_status(db: Session, order_code: str) -> None:
    """
    检查并更新订单状态
    
    如果订单的所有货物都已delivered，则将订单状态更新为completed
    
    Args:
        db: 数据库会话
        order_code: 订单编码
    """
    order = db.query(Order).filter(Order.order_code == order_code).first()
    if not order:
        return
    
    # 查询该订单的所有货物
    goods_list = db.query(Goods).filter(Goods.order_id == order.id).all()
    
    # 检查是否所有货物都已delivered
    all_delivered = all(g.status == 'delivered' for g in goods_list)
    
    # 异常订单不走 completed（ORDER_TRANSITIONS["exception"] = ["delivering"]）
    if all_delivered and order.status != "exception":
        transition_order_status(db, order, 'completed')


def transition_global_schedule_status(
    db: Session,
    gs: GlobalSchedule,
    new_status: str,
    force: bool = False,
) -> None:
    """
    统一更新全局调度方案状态，包含状态转换合法性校验。

    合法转换：
      draft        → active（确认方案）
      active       → （不可转换，immutable）
      draft → 物理删除（由调用方 db.delete() 处理，不进此函数）

    Args:
        db: 数据库会话
        gs: 全局调度方案 ORM 对象
        new_status: 目标状态（"draft" / "active"）
        force: 强制更新（跳过校验，用于数据修复场景）
    """
    if not force:
        _validate(SCHEDULE_TRANSITIONS, gs.status, new_status, "全局调度方案")
    if gs.status != new_status:
        gs.status = new_status
        db.flush()


def update_batch_status(
    db: Session,
    batch: DispatchBatch,
    new_status: str,
    force: bool = False,
) -> None:
    """
    统一更新批次状态，包含状态转换合法性校验。

    合法转换：
      pending       → l0_l1_done / completed / failed
      l0_l1_done    → completed / failed
      completed     → completed（幂等，不可转换到其他状态）
      failed        → failed（幂等，不可转换到其他状态）

    Args:
        db: 数据库会话
        batch: 批次 ORM 对象
        new_status: 目标状态
        force: 强制更新（跳过校验，用于数据修复场景）
    """
    if not force:
        _validate(BATCH_TRANSITIONS, batch.status, new_status, "批次")
    if batch.status != new_status:
        batch.status = new_status
        db.flush()


def update_orders_after_f007(
    db: Session,
    order_codes: List[str],
) -> None:
    """
    F007 全局调度完成后的订单状态更新。

    Order: pending / exception → delivering

    Args:
        db: 数据库会话
        order_codes: 订单编码列表
    """
    for order_code in order_codes:
        order = db.query(Order).filter(Order.order_code == order_code).first()
        if order and order.status in ("pending", "exception"):
            transition_order_status(db, order, "delivering")
    db.flush()


def update_goods_after_f021(
    db: Session,
    schedule_id: int,
    is_replan: bool = False,
) -> None:
    """
    F021 打包完成后的货物状态更新。

    Goods: pending_pack → packed  （首次调度）
    Goods: exception   → packed  （重规划，恢复异常货物）

    Args:
        db: 数据库会话
        schedule_id: 全局调度方案 ID
        is_replan: 是否为重规划模式
    """
    schedule = db.query(GlobalSchedule).filter(GlobalSchedule.id == schedule_id).first()
    if not schedule:
        return

    order_codes = schedule.order_codes
    if isinstance(order_codes, str):
        import json
        order_codes = json.loads(order_codes)

    if not order_codes:
        return

    orders = db.query(Order).filter(Order.order_code.in_(order_codes)).all()
    order_ids = [o.id for o in orders]

    if not order_ids:
        return

    target_status = "exception" if is_replan else "pending_pack"
    goods_list = db.query(Goods).filter(
        Goods.order_id.in_(order_ids),
        Goods.status == target_status,
    ).all()

    for goods in goods_list:
        transition_goods_status(db, goods, "packed")
    db.flush()


def mark_exception_statuses(
    db: Session,
    schedule_code: str,
) -> None:
    """
    创建异常事件时，将关联实体状态标记为 exception。

    更新以下状态：
    - Order:  delivering → exception
    - Goods:  packed / in_transit → exception
    - Package: packed / in_transit / pending_pack → exception

    Args:
        db: 数据库会话
        schedule_code: 关联调度方案编码
    """
    schedule = db.query(GlobalSchedule).filter(
        GlobalSchedule.schedule_code == schedule_code
    ).first()
    if not schedule:
        return

    # 1. 更新订单状态
    order_codes = schedule.order_codes
    if isinstance(order_codes, str):
        import json
        order_codes = json.loads(order_codes)
    for order_code in (order_codes or []):
        order = db.query(Order).filter(Order.order_code == order_code).first()
        if order and order.status == "delivering":
            transition_order_status(db, order, "exception")

    # 2. 更新货物状态
    order_objs = db.query(Order).filter(Order.order_code.in_(order_codes or [])).all()
    order_ids = [o.id for o in order_objs]
    if order_ids:
        goods_list = db.query(Goods).filter(
            Goods.order_id.in_(order_ids),
            Goods.status.in_(["packed", "in_transit"]),
        ).all()
        for goods in goods_list:
            transition_goods_status(db, goods, "exception")

    # 3. 更新包裹状态
    packages = db.query(Package).filter(
        Package.schedule_id == schedule.id,
        Package.status.in_(["packed", "in_transit", "pending_pack"]),
    ).all()
    for pkg in packages:
        transition_package_status(db, pkg, "exception")

    db.flush()


def reset_goods_for_replan(
    db: Session,
    order_codes: List[str],
) -> None:
    """
    AI 重规划时重置货物状态，使其重新参与 F007 调度。

    Goods: packed / in_transit / delivered → pending_pack

    Args:
        db: 数据库会话
        order_codes: 订单编码列表
    """
    for order_code in order_codes:
        order = db.query(Order).filter(Order.order_code == order_code).first()
        if not order:
            continue
        goods_list = db.query(Goods).filter(
            Goods.order_id == order.id,
            Goods.status.in_(["packed", "in_transit", "delivered"]),
        ).all()
        for goods in goods_list:
            transition_goods_status(db, goods, "pending_pack", force=True)
    db.flush()


def mark_old_entities_exception(
    db: Session,
    old_schedule_id: int,
) -> None:
    """
    重规划时，将旧方案的包裹标记为 exception，
    并将旧批次标记为 failed。
    """
    # 1. 旧包裹 → exception
    old_packages = db.query(Package).filter(
        Package.schedule_id == old_schedule_id,
        Package.status.in_(["packed", "pending_pack", "in_transit"]),
    ).all()
    for pkg in old_packages:
        transition_package_status(db, pkg, "exception", force=True)

    # 2. 旧批次 → failed
    old_batches = db.query(DispatchBatch).filter(
        DispatchBatch.global_schedule_id == old_schedule_id,
    ).all()
    for batch in old_batches:
        if batch.status in ("pending", "l0_l1_done"):
            update_batch_status(db, batch, "failed", force=True)

    db.flush()


def mark_vehicle_exception(
    db: Session,
    vehicle_code: str,
) -> None:
    """
    车辆异常时，将关联实体状态标记为 exception。

    更新以下状态：
    - Package（该车辆关联）: packed / in_transit / pending_pack → exception
    - Goods（通过包裹关联）: packed / in_transit → exception

    Vehicle 状态（disabled）由调用方设置。

    Args:
        db: 数据库会话
        vehicle_code: 车辆编码
    """
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
    if not vehicle:
        return

    # 1. 查找该车辆的所有调度明细
    dispatches = db.query(NodeDispatch).filter(
        NodeDispatch.vehicle_id == vehicle.id
    ).all()
    dispatch_ids = [d.id for d in dispatches]

    if not dispatch_ids:
        return

    # 2. 更新关联包裹状态
    packages = db.query(Package).filter(
        Package.dispatch_id.in_(dispatch_ids),
        Package.status.in_(["packed", "in_transit", "pending_pack"]),
    ).all()

    for pkg in packages:
        transition_package_status(db, pkg, "exception", force=True)

        # 3. 更新关联货物状态
        items = pkg.goods_items
        if isinstance(items, str):
            import json
            items = json.loads(items)
        if items:
            for item in items:
                goods_code = item.get("goods_code")
                if goods_code:
                    goods = db.query(Goods).filter(
                        Goods.goods_code == goods_code,
                        Goods.status.in_(["packed", "in_transit"]),
                    ).first()
                    if goods:
                        transition_goods_status(db, goods, "exception", force=True)

    db.flush()

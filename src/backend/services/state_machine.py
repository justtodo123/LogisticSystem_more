"""
状态机服务 - 管理物流系统中的所有状态流转

所有状态变更必须通过本模块的函数完成，算法层和服务层不直接修改 .status 字段。

状态流转规则（修正版）：
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
4. 模拟送达（L0→L1）→ L0→L1包裹: in_transit → delivered
                         货物状态: in_transit → pending_pack
                         L1→L2包裹: pending_pack（不变，等待L1重新打包激活）
                         批次状态: pending/l0_l1_done → l0_l1_done
                         车辆状态: delivering → idle; 司机状态: busy → idle
5. F021重新打包 → 货物状态: pending_pack → packed
                         L1→L2包裹: pending_pack → packed（激活）
6. 模拟送达（L1→L2）→ L1→L2包裹: in_transit → delivered
                         货物状态: in_transit → delivered
                         订单状态: delivering → completed（所有货物送达后）
                         批次状态: l0_l1_done → completed
                         车辆状态: delivering → idle; 司机状态: busy → idle
7. 异常事件创建 → 关联订单/货物/包裹 → exception; 关联车辆 → disabled
8. 重规划 → 旧方案包裹 → exception; 旧批次 → failed; 新方案重新走1-6
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import Order, Goods, Package, Vehicle, Driver, DispatchBatch, NodeDispatch, Node
from models.global_schedule import GlobalSchedule
from models.package import Package
from algorithms.packaging import packaging


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
    # 1. 更新包裹状态
    for pkg_code in package_codes:
        pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
        if pkg:
            pkg.status = 'in_transit'
            
            # 2. 更新货物状态（通过package的goods_items）
            if pkg.goods_items:
                for item in pkg.goods_items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            goods.status = 'in_transit'
    
    # 3. 更新车辆状态
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle:
        vehicle.status = 'delivering'
    
    # 4. 更新司机状态
    driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
    if driver:
        driver.status = 'busy'
    
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
        if not task.get('is_return', False):
            package_codes.extend(task.get('package_codes', []))
    
    # 2. 更新包裹状态（仅L0→L1的包裹）
    for pkg_code in package_codes:
        pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
        if pkg:
            pkg.status = 'delivered'
            
            # 3. 更新货物状态
            if pkg.goods_items:
                for item in pkg.goods_items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            goods.status = 'pending_pack'
    
    # 4. 更新批次状态（使用统一函数）
    update_batch_status(db, batch, 'l0_l1_done')
    
    # 5. 更新车辆状态
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle:
        vehicle.status = 'idle'
    
    # 6. 更新司机状态
    driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
    if driver:
        driver.status = 'idle'
    
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
    # F021生成的L1→L2包裹状态为 pending_pack（货物尚在L0），
    # 但为兼容旧数据也检查 packed 状态（重规划等场景可能已有packed包裹）
    # 
    # 关键修复：使用 .all() 而非 .first()，并按 goods_items 中的 order_code
    # 精确匹配。当多个订单共享同一 L1→L2 路线时，每个订单有独立的 F021 包裹，
    # .first() 会错误地重复激活同一个包裹，导致其他订单的包裹永远停在 pending_pack。
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
            # 最后兜底：使用第一个包裹
            if not existing_package and all_matching:
                existing_package = all_matching[0]
    
    if existing_package:
        # 重用现有包裹：F021已正确设置了goods_items，只需更新状态和货物状态
        # existing_package.goods_items 在F021中已包含该订单的所有货物，无需重复添加
        existing_package.status = 'packed'  # L1重新打包完成：pending_pack → packed
        
        db.flush()
        
        # 更新货物状态：pending_pack → packed
        for goods in goods_list:
            goods.status = 'packed'
        
        db.flush()
        
        # 返回结果（包含层级信息）
        return {
            "new_packages": [existing_package],
            "level_info": {
                "level_phase": 1,  # L1→L2
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
        
        # 8. 创建新包裹
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
            goods.status = 'packed'
        
        db.flush()
        
        # 10. 返回结果（包含层级信息）
        return {
            "new_packages": [new_package],
            "level_info": {
                "level_phase": 1,  # L1→L2
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
        if not task.get('is_return', False):
            package_codes.extend(task.get('package_codes', []))
    
    # 2. 更新包裹状态
    for pkg_code in package_codes:
        pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
        if pkg:
            pkg.status = 'delivered'
            
            # 3. 更新货物状态
            if pkg.goods_items:
                for item in pkg.goods_items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            goods.status = 'delivered'
    
    # 4. 更新订单状态（仅当该订单所有货物都已 delivered 时才设为 completed）
    for order_code in order_codes:
        check_and_update_order_status(db, order_code)
    
    # 5. 更新批次状态（仅当 goods 全部送达时才 completed，否则保持 l0_l1_done）
    # 由调用方负责最终批次状态更新
    # batch.status = 'completed'  # 不再在此处设置，由 _run_dispatch_both_levels 统一管理
    
    # 6. 更新车辆状态
    vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
    if vehicle:
        vehicle.status = 'idle'
    
    # 7. 更新司机状态
    driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
    if driver:
        driver.status = 'idle'
    
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
    
    if all_delivered:
        order.status = 'completed'
        db.flush()


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

    禁止转换：
      active       → draft / 其他（方案已生效不可回退）
      draft        → draft（幂等跳过）
      active       → active（幂等跳过）

    Args:
        db: 数据库会话
        gs: 全局调度方案 ORM 对象
        new_status: 目标状态（"draft" / "active"）
        force: 强制更新（跳过校验，用于数据修复场景）
    """
    # 同状态幂等：直接返回
    if gs.status == new_status:
        return

    valid = {
        "draft":  ["active"],   # draft 只能 → active
        "active": [],            # active 不可变
    }

    if not force and new_status not in valid.get(gs.status, []):
        raise ValueError(
            f"非法全局调度方案状态转换: {gs.schedule_code} {gs.status} → {new_status}"
        )

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
      l0_l1_done  → l0_l1_done（幂等）/ completed / failed
      completed    → completed（幂等，不可转换到其他状态）
      failed       → failed（幂等，不可转换到其他状态）

    Args:
        db: 数据库会话
        batch: 批次 ORM 对象
        new_status: 目标状态
        force: 强制更新（跳过校验，用于数据修复场景）
    """
    # 同状态幂等：直接返回，不报错
    if batch.status == new_status:
        return

    valid = {
        "pending":      ["l0_l1_done", "completed", "failed"],
        "l0_l1_done": ["completed", "failed"],
        "completed":    [],
        "failed":       [],
    }
    if not force and new_status not in valid.get(batch.status, []):
        raise ValueError(
            f"非法批次状态转换: {batch.status} → {new_status}"
        )
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
            order.status = "delivering"
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

    注意：Goods 模型没有 schedule_id 字段，通过 order 间接查找：
    GlobalSchedule.order_codes → Order.id → Goods.order_id

    Args:
        db: 数据库会话
        schedule_id: 全局调度方案 ID
        is_replan: 是否为重规划模式
    """
    # 通过 GlobalSchedule → Orders → Goods 查找关联货物
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
        goods.status = "packed"
    db.flush()


def mark_exception_statuses(
    db: Session,
    schedule_code: str,
) -> None:
    """
    创建异常事件时，将关联实体状态标记为 exception。

    更新以下状态：
    - Order:  delivering → exception
    - Goods: packed / in_transit → exception
    - Package: packed / in_transit / pending_pack → exception
    - Vehicle（如 target_type=vehicle）: → disabled（由调用方设置）

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
    order_codes = schedule.order_codes  # JSON 字段：["O001", "O002", ...]
    if isinstance(order_codes, str):
        import json
        order_codes = json.loads(order_codes)
    for order_code in (order_codes or []):
        order = db.query(Order).filter(Order.order_code == order_code).first()
        if order and order.status == "delivering":
            order.status = "exception"

    # 2. 更新货物状态（通过 Order 间接查找，Goods 无 schedule_id）
    order_objs = db.query(Order).filter(Order.order_code.in_(order_codes or [])).all()
    order_ids = [o.id for o in order_objs]
    if order_ids:
        goods_list = db.query(Goods).filter(
            Goods.order_id.in_(order_ids),
            Goods.status.in_(["packed", "in_transit"]),
        ).all()
        for goods in goods_list:
            goods.status = "exception"

    # 3. 更新包裹状态（通过 schedule_id 关联）
    packages = db.query(Package).filter(
        Package.schedule_id == schedule.id,
        Package.status.in_(["packed", "in_transit", "pending_pack"]),
    ).all()
    for pkg in packages:
        pkg.status = "exception"

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
            goods.status = "pending_pack"
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
        pkg.status = "exception"

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
        pkg.status = "exception"

        # 3. 更新关联货物状态
        if pkg.goods_items:
            items = pkg.goods_items
            if isinstance(items, str):
                import json
                items = json.loads(items)
            for item in items:
                goods_code = item.get("goods_code")
                if goods_code:
                    goods = db.query(Goods).filter(
                        Goods.goods_code == goods_code,
                        Goods.status.in_(["packed", "in_transit"]),
                    ).first()
                    if goods:
                        goods.status = "exception"

    db.flush()

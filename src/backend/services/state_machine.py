"""
状态机服务 - 管理物流系统中的所有状态流转

状态流转规则：
1. F007完成 → 订单状态: pending → delivering
2. F021完成 → 货物状态: pending_pack → packed; 包裹状态: pending_pack → packed
3. F005调用 → 货物状态: packed → in_transit; 包裹状态: packed → in_transit; 
               车辆状态: idle → delivering; 司机状态: idle → busy
4. 模拟送达（L0→L1）→ 包裹状态: in_transit → delivered; 货物状态: in_transit → pending_pack;
                     批次状态: pending/l0_l1_done → l0_l1_done; 
                     车辆状态: delivering → idle; 司机状态: busy → idle
5. F021重新打包 → 货物状态: pending_pack → packed; 新包裹状态: pending_pack → packed
6. 模拟送达（L1→L2）→ 包裹状态: in_transit → delivered; 货物状态: in_transit → delivered;
                     订单状态: delivering → completed; 批次状态: l0_l1_done → completed;
                     车辆状态: delivering → idle; 司机状态: busy → idle
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import Order, Goods, Package, Vehicle, Driver, DispatchBatch, NodeDispatch, Node
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
    - 包裹状态: in_transit → delivered
    - 货物状态: in_transit → pending_pack
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
                            goods.status = 'pending_pack'
    
    # 4. 更新批次状态
    batch.status = 'l0_l1_done'
    
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
) -> List[Package]:
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
        新创建的包裹列表
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
    
    # 4. 计算总重量和总体积
    total_weight = sum(float(g.weight) for g in goods_list)
    total_volume = sum(float(g.volume) for g in goods_list)
    
    # 5. 生成包裹编号
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
    
    # 6. 创建goods_items
    goods_items = [
        {"goods_code": g.goods_code, "order_code": order_code}
        for g in goods_list
    ]
    
    # 7. 创建新包裹
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
    
    # 8. 更新货物状态
    for goods in goods_list:
        goods.status = 'packed'
    
    db.flush()
    
    return [new_package]


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

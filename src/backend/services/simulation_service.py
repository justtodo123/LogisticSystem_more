"""
模拟送达服务

编排模拟送达的完整流程。
单事务保证原子性：packages/goods/vehicles/drivers/orders 状态更新全部成功或全部回滚。
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.package import Package
from models.goods import Goods
from models.order import Order
from models.vehicle import Vehicle
from models.driver import Driver
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.global_schedule import GlobalSchedule
from models.node import Node
from utils.response import success_response, error_response
from algorithms.node_dispatch import dispatch_level, _load_config
import json
import logging


class SimulationService:
    """模拟送达服务"""

    @staticmethod
    async def deliver_packages(
        vehicle_code: Optional[str],
        package_code: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        模拟送达，驱动状态流转
        
        流程：
        1. 根据参数查询要送达的包裹
        2. 检查包裹状态（必须 in_transit）
        3. 更新包裹状态：in_transit → delivered
        4. 更新货物状态（根据是否送达目的地）
        5. 检查车辆状态（所有包裹送达后 vehicle → idle）
        6. 检查司机状态（车辆 idle 后 driver → idle）
        7. 检查订单状态（所有货物送达后 order → completed）
        8. 返回结果
        
        Args:
            vehicle_code: 车辆编号（可选）
            package_code: 包裹编号（可选）
            db: 数据库会话
            
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 根据参数查询要送达的包裹
            query = db.query(Package).filter(Package.status == "in_transit")
            
            if package_code:
                # 按 package_code 查询
                query = query.filter(Package.package_code == package_code)
            elif vehicle_code:
                # 按 vehicle_code 查询（需要 JOIN node_dispatches 和 vehicles）
                query = query.join(NodeDispatch, Package.dispatch_id == NodeDispatch.id)
                query = query.join(Vehicle, NodeDispatch.vehicle_id == Vehicle.id)
                query = query.filter(Vehicle.vehicle_code == vehicle_code)
            # 都不传：查询所有 in_transit 包裹（已在 filter 中）
            
            packages = query.all()
            
            if not packages:
                return error_response(code=40001, message="没有找到可送达的包裹")
            
            # 准备响应数据
            delivered_package_codes = []
            status_changed_goods_count = 0
            updated_order_ids = set()
            level_info = {"l0_to_l1": 0, "l1_to_l2": 0}  # 层级信息：记录每种层级的送达数量
            
            # 2. 处理每个包裹
            for package in packages:
                # 检查包裹状态（必须 in_transit）
                if package.status != "in_transit":
                    return error_response(
                        code=40001,
                        message=f"包裹 {package.package_code} 状态不是 in_transit，无法送达"
                    )
                
                # 3. 更新包裹状态：in_transit → delivered
                package.status = "delivered"
                delivered_package_codes.append(package.package_code)
                
                # 4. 更新货物状态（根据是否送达目的地）
                goods_items = package.goods_items  # JSON: [{"goods_code": "G001", "order_code": "O001"}]
                # 解析 JSON（如果是字符串）
                if isinstance(goods_items, str):
                    import json
                    goods_items = json.loads(goods_items)
                for item in goods_items:
                    goods_code = item["goods_code"]
                    order_code = item["order_code"]
                    
                    # 查询货物
                    goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                    if not goods:
                        continue
                    
                    # 查询订单
                    order = db.query(Order).filter(Order.order_code == order_code).first()
                    if not order:
                        continue
                    
                    # 更新货物位置：goods.node_id = package.to_node_id
                    goods.node_id = package.to_node_id
                    
                    # 判断是否送达目的地
                    if goods.node_id == order.destination_node_id:
                        # 送达目的地 → delivered（L1→L2）
                        goods.status = "delivered"
                        level_info["l1_to_l2"] += 1
                    else:
                        # 中间节点 → pending_pack（L0→L1）
                        goods.status = "pending_pack"
                        level_info["l0_to_l1"] += 1
                    
                    status_changed_goods_count += 1
                    updated_order_ids.add(order.id)
            
            # 5. 检查车辆状态（所有包裹送达后 vehicle → idle）
            # 收集所有受影响的车辆 ID
            vehicle_ids = set()
            for package in packages:
                if package.dispatch_id:
                    dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == package.dispatch_id).first()
                    if dispatch:
                        vehicle_ids.add(dispatch.vehicle_id)
            
            for vehicle_id in vehicle_ids:
                # 查询该车辆的所有包裹（包括已更新的）
                db.flush()  # 确保能看到最新的包裹状态
                vehicle_packages = db.query(Package).join(
                    NodeDispatch, Package.dispatch_id == NodeDispatch.id
                ).filter(
                    NodeDispatch.vehicle_id == vehicle_id,
                    Package.status == "in_transit"
                ).all()
                
                if not vehicle_packages:
                    # 所有包裹都已送达，车辆变为 idle
                    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
                    if vehicle and vehicle.status == "delivering":
                        vehicle.status = "idle"
                        
                        # 6. 检查司机状态（车辆 idle 后 driver → idle）
                        # 查询该车辆的司机（从 node_dispatches 中找）
                        dispatch = db.query(NodeDispatch).filter(
                            NodeDispatch.vehicle_id == vehicle_id
                        ).order_by(NodeDispatch.id.desc()).first()
                        if dispatch and dispatch.driver_id:
                            driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first()
                            if driver and driver.status == "busy":
                                driver.status = "idle"
            
            # 7. 检查订单状态（所有货物送达后 order → completed）
            delivered_order_codes = []
            for order_id in updated_order_ids:
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    continue
                
                # 查询该订单的所有货物
                all_goods = db.query(Goods).filter(Goods.order_id == order_id).all()
                
                # 检查是否所有货物都已 delivered
                all_delivered = all(g.status == "delivered" for g in all_goods)
                
                if all_delivered and order.status == "delivering":
                    order.status = "completed"
                    delivered_order_codes.append(order.order_code)
            
            # 8. 更新批次状态（第一次送达完成后）
            SimulationService._update_batch_status_after_delivery(db, packages)
            
            # 9. 自动触发逻辑（demo_mode=false 完整流程支持）
            auto_triggered = {"repackaging": False, "second_f005": False}
            
            try:
                # 检查是否有 pending_pack 货物（需要L1重新打包）
                pending_pack_goods = db.query(Goods).filter(
                    Goods.status == 'pending_pack'
                ).first()
                
                if pending_pack_goods:
                    # 获取 schedule_id（从任意一个已送达的包裹中获取）
                    schedule_id = None
                    for pkg in packages:
                        if pkg.schedule_id:
                            schedule_id = pkg.schedule_id
                            break
                    
                    if schedule_id:
                        # 自动触发L1重新打包
                        repack_result = SimulationService._trigger_repackaging(db, schedule_id)
                        auto_triggered["repackaging"] = repack_result
                        
                        if repack_result:
                            # 自动触发第二次F005（异步）
                            second_f005_result = SimulationService._trigger_second_f005_async(db, schedule_id)
                            auto_triggered["second_f005"] = second_f005_result
            except Exception as e:
                # 记录错误日志，但不影响第一次送达的结果
                import logging
                logging.error(f"自动触发失败：{e}")
            
            # 9. 自动重新调度未分配包裹
            try:
                redispatch_result = SimulationService._auto_redispatch_unallocated(db)
                auto_triggered["redispatch"] = redispatch_result
            except Exception as e:
                logging.error(f"自动重新调度失败：{e}")
                auto_triggered["redispatch"] = False
            
            # 10. 返回结果
            return success_response(data={
                "delivered_package_codes": delivered_package_codes,
                "status_changed_goods_count": status_changed_goods_count,
                "updated_order_count": len(delivered_order_codes),
                "delivered_order_codes": delivered_order_codes,
                "auto_triggered": auto_triggered,
                "level_info": level_info  # 添加层级信息
            })
            
        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"模拟送达失败：{str(e)}")

    @staticmethod
    def _trigger_repackaging(db: Session, schedule_id: int) -> bool:
        """
        触发L1重新打包
        
        查询所有 pending_pack 状态的货物，按订单分组，调用 repack_at_l1()
        
        Args:
            db: 数据库会话
            schedule_id: 全局调度方案ID
            
        Returns:
            bool: 是否成功触发重新打包
        """
        try:
            from models.goods import Goods
            from models.order import Order
            from models.global_schedule import GlobalSchedule
            import json
            import logging
            
            # 查询所有 pending_pack 货物
            pending_goods = db.query(Goods).filter(
                Goods.status == 'pending_pack'
            ).all()
            
            if not pending_goods:
                return False
            
            # 按订单分组
            order_goods_map = {}
            for goods in pending_goods:
                order_id = goods.order_id
                if order_id not in order_goods_map:
                    order_goods_map[order_id] = []
                order_goods_map[order_id].append(goods)
            
            # 获取 schedule
            schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.id == schedule_id
            ).first()
            
            if not schedule:
                return False
            
            # 解析 goods_schedules
            goods_schedules = schedule.goods_schedules
            if isinstance(goods_schedules, str):
                goods_schedules = json.loads(goods_schedules)
            
            # 为每个订单重新打包
            for order_id, goods_list in order_goods_map.items():
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    continue
                
                # 查找该订单的路径
                l1_node_code = None
                l2_node_code = None
                for gs in goods_schedules:
                    if gs.get('order_code') == order.order_code:
                        path = gs.get('path', [])
                        if len(path) >= 3:
                            l1_node_code = path[1]  # 第二个节点是L1
                            l2_node_code = path[2]  # 第三个节点是L2
                            break
                
                if l1_node_code and l2_node_code:
                    # 调用 repack_at_l1()
                    from services.state_machine import repack_at_l1
                    repack_at_l1(db, order.order_code, l1_node_code, l2_node_code, schedule_id)
            
            # 提交事务（确保重新打包的结果已保存）
            db.commit()
            
            return True
            
        except Exception as e:
            # 回滚事务
            db.rollback()
            
            import logging
            logging.error(f"重新打包失败：{e}")
            return False

    @staticmethod
    def _trigger_second_f005_async(db: Session, schedule_id: int) -> bool:
        """
        异步触发第二次F005
        
        使用 ThreadPoolExecutor 在新线程中执行，避免阻塞API响应
        """
        import json
        from concurrent.futures import ThreadPoolExecutor
        from models.global_schedule import GlobalSchedule
        
        # 获取 schedule_code
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.id == schedule_id
        ).first()
        
        if not schedule:
            return False
        
        schedule_code = schedule.schedule_code
        
        # 在新线程中执行第二次F005
        def _execute_second_f005():
            try:
                # 创建新的数据库会话
                from config.database import SessionLocal
                new_db = SessionLocal()
                
                # 调用 run_node_dispatch（demo_mode=False，会自动检测并执行第二次调用）
                from algorithms.node_dispatch import run_node_dispatch
                result = run_node_dispatch(new_db, schedule_code, demo_mode=False)
                
                # 提交事务
                new_db.commit()
                
                import logging
                logging.info(f"第二次F005执行成功：{result}")
                
            except Exception as e:
                import logging
                logging.error(f"第二次F005执行失败：{e}")
                
                # 更新批次状态为 failed
                try:
                    from models.node_dispatch import DispatchBatch
                    batch = new_db.query(DispatchBatch).filter(
                        DispatchBatch.global_schedule_id == schedule_id,
                        DispatchBatch.status == 'l0_l1_done'
                    ).first()
                    
                    if batch:
                        batch.status = 'failed'
                        new_db.commit()
                except:
                    pass
                    
            finally:
                new_db.close()
        
        # 提交当前事务（确保重新打包的结果已保存）
        db.commit()
        
        # 异步执行
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(_execute_second_f005)
        
        return True

    @staticmethod
    def _update_batch_status_after_delivery(db: Session, packages: List[Package]) -> None:
        """
        更新批次状态为 l0_l1_done（第一次送达完成后）
        
        Args:
            db: 数据库会话
            packages: 已送达的包裹列表
        """
        # 收集所有受影响的批次ID
        batch_ids = set()
        for pkg in packages:
            if pkg.dispatch_id:
                dispatch = db.query(NodeDispatch).filter(NodeDispatch.id == pkg.dispatch_id).first()
                if dispatch and dispatch.dispatch_batch_id:
                    batch_ids.add(dispatch.dispatch_batch_id)
        
        # 更新批次状态
        for batch_id in batch_ids:
            batch = db.query(DispatchBatch).filter(DispatchBatch.id == batch_id).first()
            if batch and batch.status in ['pending', 'l0_l1_done']:
                batch.status = 'l0_l1_done'
        
        db.flush()

    @staticmethod
    def _auto_redispatch_unallocated(db: Session) -> bool:
        """
        自动重新调度未分配的包裹（支持递归重新调度）
        
        逻辑：
        1. 查询所有有未分配包裹的批次
        2. 检查这些批次相关的节点是否有空闲车辆
        3. 如果有空闲车辆，调用 dispatch_level() 重新调度
        4. 更新批次的未分配包裹列表
        5. 如果成功重新调度了至少一个包裹，递归调用自身，尝试重新调度剩余的未分配包裹
        
        Returns:
            bool: 是否成功重新调度了至少一个包裹
        """
        try:
            # 1. 查询所有有未分配包裹的批次
            batches = db.query(DispatchBatch).filter(
                DispatchBatch.unallocated_packages.isnot(None)
            ).all()
            
            if not batches:
                return False
            
            # 2. 加载配置
            config = _load_config()
            
            total_redispatch_count = 0
            
            # 3. 遍历每个批次
            for batch in batches:
                if not batch.unallocated_packages:
                    continue
                
                # 递归重新调度该批次的未分配包裹
                redispatch_count = SimulationService._redispatch_batch_unallocated(
                    db, batch, config
                )
                
                total_redispatch_count += redispatch_count
            
            return total_redispatch_count > 0
            
        except Exception as e:
            logging.error(f"自动重新调度失败：{e}")
            return False
    
    @staticmethod
    def _redispatch_batch_unallocated(db: Session, batch, config: dict) -> int:
        """
        重新调度指定批次的未分配包裹（递归调用）
        
        递归逻辑：
        1. 尝试重新调度未分配的包裹
        2. 如果成功分配了至少一个包裹，递归调用自身，尝试分配剩余的未分配包裹
        3. 递归终止条件：没有成功分配任何包裹，或者所有包裹都已分配
        
        Args:
            db: 数据库会话
            batch: 调度批次对象
            config: 算法配置
            
        Returns:
            int: 成功重新调度的包裹数量
        """
        # 1. 解析未分配包裹
        if not batch.unallocated_packages:
            return 0
        
        unallocated_codes = json.loads(batch.unallocated_packages)
        
        # 查询这些包裹
        unallocated_pkgs = db.query(Package).filter(
            Package.package_code.in_(unallocated_codes),
            Package.status == 'packed'
        ).all()
        
        if not unallocated_pkgs:
            # 这些包裹已经被分配了，清除记录
            batch.unallocated_packages = None
            db.flush()
            return 0
        
        # 2. 检查是否有空闲车辆
        # 获取这些包裹的起始节点
        from_node_ids = set(pkg.from_node_id for pkg in unallocated_pkgs)
        
        has_idle_vehicle = False
        for node_id in from_node_ids:
            idle_vehicles = db.query(Vehicle).filter(
                Vehicle.node_id == node_id,
                Vehicle.status == 'idle'
            ).first()
            
            if idle_vehicles:
                has_idle_vehicle = True
                break
        
        if not has_idle_vehicle:
            # 没有空闲车辆，终止递归
            return 0
        
        # 3. 确定是 L0→L1 还是 L1→L2
        # 检查第一个包裹的 from_node 类型
        first_pkg = unallocated_pkgs[0]
        from_node = db.query(Node).filter(Node.id == first_pkg.from_node_id).first()
        
        if not from_node:
            return 0
        
        if from_node.node_type == 'storage_center':
            level_phase = 0  # L0→L1
        else:
            level_phase = 1  # L1→L2
        
        # 4. 调用调度算法，只调度未分配的包裹
        # 传入batch_id，自动写入调度明细
        _, updated_packages, new_unallocated = dispatch_level(
            db, batch.global_schedule_id, level_phase, config, 
            package_codes=unallocated_codes,
            batch_id=batch.id
        )
        
        # 5. 更新已分配包裹的状态
        for pkg in updated_packages:
            pkg.status = 'in_transit'
            # 更新货物状态
            if pkg.goods_items:
                goods_items = pkg.goods_items
                if isinstance(goods_items, str):
                    goods_items = json.loads(goods_items)
                for item in goods_items:
                    goods_code = item.get('goods_code')
                    if goods_code:
                        goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                        if goods:
                            goods.status = 'in_transit'
        
        # 6. 更新批次的未分配包裹
        if new_unallocated:
            batch.unallocated_packages = json.dumps(
                [pkg.package_code for pkg in new_unallocated]
            )
        else:
            batch.unallocated_packages = None
        
        db.flush()
        
        # 7. 递归调用：如果成功分配了至少一个包裹，尝试分配剩余的未分配包裹
        if updated_packages:
            # 递归调用，尝试分配剩余的未分配包裹
            remaining_count = SimulationService._redispatch_batch_unallocated(db, batch, config)
            return len(updated_packages) + remaining_count
        else:
            return 0

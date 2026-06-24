"""
到货确认服务

核心功能：
1. 单个到货确认（正常/异常）
2. 批量到货确认（事务性，任一失败则全部回滚）
3. F021 重新打包触发
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.package import Package
from models.goods import Goods
from models.order import Order
from models.global_schedule import GlobalSchedule
from models.exception_event import ExceptionEvent
from schemas.arrival_confirm import ArrivalConfirmRequest, BatchArrivalConfirmRequest


class ArrivalConfirmService:
    """到货确认服务"""

    @staticmethod
    def confirm_arrival(
        db: Session,
        schedule_code: str,
        package_code: str,
        is_normal: bool,
        exception_subtype: Optional[str] = None,
        remark: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        单个到货确认
        
        正常路径：
        1. 更新包裹状态：delivered
        2. 处理货物：检查是否到目的地
           - 若已到目的地：goods.status = delivered
           - 若未到目的地：goods.status = pending_pack，触发 F021 重新打包
        3. 检查订单是否完成
        
        异常路径：
        1. 更新包裹状态：exception
        2. 处理货物：goods.status = exception
        3. 写入 exception_events（审计用，不触发 replan）
        4. 更新订单状态：exception
        5. 级联下游包裹（若存在）
        
        Args:
            db: 数据库会话
            schedule_code: 调度方案编号
            package_code: 包裹编号
            is_normal: 是否正常到站
            exception_subtype: 异常子类型（仅 is_normal=False 时必填）
            remark: 备注
            
        Returns:
            结果字典
        """
        # 1. 查询包裹
        package = db.query(Package).filter(Package.package_code == package_code).first()
        if not package:
            raise HTTPException(status_code=404, detail=f"包裹 {package_code} 不存在")

        # 2. 正常路径
        if is_normal:
            # 2.1 更新包裹状态
            package.status = "delivered"

            # 2.2 处理货物：检查是否到目的地
            triggered_repacking = False
            new_package_code = None

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

                # 检查是否到目的地
                if goods.node_id == order.destination_node_id:
                    # 已到目的地
                    goods.status = "delivered"
                else:
                    # 未到目的地：pending_pack，触发 F021 重新打包
                    goods.status = "pending_pack"

                    # 2.3 触发 F021 重新打包
                    result = ArrivalConfirmService._trigger_repacking(db, schedule_code)
                    if result:
                        triggered_repacking = True
                        new_package_code = result

            # 2.4 检查订单是否完成（所有货物都已 delivered）
            for item in goods_items:
                order_code = item["order_code"]
                order = db.query(Order).filter(Order.order_code == order_code).first()
                if order:
                    ArrivalConfirmService._check_order_completion(db, order)

            return {
                "package_code": package_code,
                "status": "delivered",
                "goods_status": "pending_pack" if not triggered_repacking else "delivered",
                "triggered_repacking": triggered_repacking,
                "new_package_code": new_package_code
            }

        # 3. 异常路径
        else:
            # 3.1 更新包裹状态
            package.status = "exception"

            goods_items = package.goods_items
            if isinstance(goods_items, str):
                import json
                goods_items = json.loads(goods_items)

            order_status = None

            # 3.2 处理货物
            for item in goods_items:
                goods_code = item["goods_code"]
                order_code = item["order_code"]

                goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
                if not goods:
                    continue

                goods.status = "exception"

                # 3.3 写入 exception_events（审计用，不触发 replan）
                import time
                import random
                event_code = f"EX{int(time.time() * 1000)}{random.randint(100, 999)}"
                # 包裹异常的推荐操作：reroute（重新路径规划）
                recommended_action = "reroute"
                exception_event = ExceptionEvent(
                    event_code=event_code,
                    exception_type="package",
                    exception_subtype=exception_subtype,
                    target_type="package",
                    target_code=package_code,
                    recommended_action=recommended_action,
                    related_schedule_code=schedule_code,
                    description=remark if remark else ""
                )
                db.add(exception_event)

                # 3.4 更新订单状态
                order = db.query(Order).filter(Order.order_code == order_code).first()
                if order and order.status != "exception":
                    order.status = "exception"
                    order_status = "exception"

                # 3.5 级联下游包裹（若存在）
                ArrivalConfirmService._cascade_exception_packages(db, schedule_code, package_code)

            return {
                "package_code": package_code,
                "status": "exception",
                "goods_status": "exception",
                "order_status": order_status
            }

    @staticmethod
    def confirm_arrival_batch(
        db: Session,
        schedule_code: str,
        confirmations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量到货确认（事务性，任一失败则全部回滚）
        
        Args:
            db: 数据库会话
            schedule_code: 调度方案编号（所有包裹必须属于该方案）
            confirmations: 确认列表 [{"package_code": "PKG001", "is_normal": true}, ...]
            
        Returns：
            结果字典 {total, success_count, failed_count, results, errors}
        """
        # 1. 预校验所有包裹（事务性：任一失败则全部回滚）
        for conf in confirmations:
            package_code = conf["package_code"]

            package = db.query(Package).filter(Package.package_code == package_code).first()
            if not package:
                raise HTTPException(status_code=400, detail=f"包裹 {package_code} 不存在")

            # 1.2 包裹不属于该 schedule
            schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == schedule_code
            ).first()
            if not schedule or package.schedule_id != schedule.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"包裹 {package_code} 不属于该调度方案"
                )

            # 1.3 包裹状态不正确（必须是 in_transit 或 delivered）
            if package.status not in ["in_transit", "delivered"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"包裹 {package_code} 状态不正确：{package.status}"
                )

        # 2. 批量确认（事务性）
        results = []
        try:
            for conf in confirmations:
                # 2.1 复用单个确认逻辑
                result = ArrivalConfirmService.confirm_arrival(
                    db,
                    schedule_code=schedule_code,
                    package_code=conf["package_code"],
                    is_normal=conf["is_normal"],
                    exception_subtype=conf.get("exception_subtype"),
                    remark=conf.get("remark")
                )
                results.append(result)

            # 3. 返回成功响应
            return {
                "total": len(confirmations),
                "success_count": len(results),
                "failed_count": 0,
                "results": results,
                "errors": None
            }

        except HTTPException as e:
            # 4. 返回失败响应（已回滚）
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"批量确认失败：{str(e)}")

    @staticmethod
    def _trigger_repacking(db: Session, schedule_code: str) -> Optional[str]:
        """
        触发 F021 重新打包
        
        当 confirm-arrival（正常）后，若货物未到目的地，触发 F021 重新打包：
        1. 遍历 global_schedule.goods_schedules
        2. 对每条 goods_schedule：
           - 若 goods.status == pending_pack：
               from_node = goods.node_id（当前所在节点）
               to_node = path[index(goods.node_id) + 1]（按实际位置取 path 下一个节点）
               生成新的下游包裹（packed）
           - 更新 goods.status = packed（F021 完成后）
        3. 若 goods.status == exception：跳过，不参与重新打包
        
        Args:
            db: 数据库会话
            schedule_code: 调度方案编号
            
        Returns:
            新包裹编号（若生成了新包裹），否则 None
        """
        # 1. 查询 global_schedule
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        if not schedule:
            return None

        goods_schedules = schedule.goods_schedules  # JSON
        if isinstance(goods_schedules, str):
            import json
            goods_schedules = json.loads(goods_schedules)

        # 2. 按 from_node → to_node 聚合（L1→L2 阶段，同一订单的货物必须打成一个包裹）
        from collections import defaultdict
        repacking_groups = defaultdict(list)  # key: (from_node_code, to_node_code), value: [gs, ...]
        
        for gs in goods_schedules:
            goods_code = gs["goods_code"]
            goods = db.query(Goods).filter(Goods.goods_code == goods_code).first()
            if not goods or goods.status != "pending_pack":
                continue

            # 2.1 确定 from_node 和 to_node
            from_node_id = goods.node_id
            
            # 从 path 中取下一个节点
            path = gs["path"]  # path 中是 node_code 字符串列表
            
            # 查询 from_node_code
            from models.node import Node
            from_node = db.query(Node).filter(Node.id == from_node_id).first()
            if not from_node:
                continue
            from_node_code = from_node.node_code
            
            try:
                current_index = path.index(from_node_code)
                if current_index + 1 >= len(path):
                    # 已到目的地，无需重新打包
                    goods.status = "delivered"
                    continue
                to_node_code = path[current_index + 1]
            except ValueError:
                # from_node 不在 path 中，跳过
                continue

            # 按 (from_node_code, to_node_code) 聚合
            key = (from_node_code, to_node_code)
            repacking_groups[key].append({
                "gs": gs,
                "goods": goods,
                "from_node_id": from_node_id,
                "to_node_id": None  # 稍后查询
            })

        # 3. 生成新包裹（按聚合组）
        new_package_codes = []
        
        for (from_node_code, to_node_code), group in repacking_groups.items():
            # 3.1 查询 to_node_id
            to_node = db.query(Node).filter(Node.node_code == to_node_code).first()
            if not to_node:
                continue
            to_node_id = to_node.id
            
            # 3.2 查询 from_node_id
            from_node = db.query(Node).filter(Node.node_code == from_node_code).first()
            if not from_node:
                continue
            from_node_id = from_node.id

            # 3.3 检查是否已存在相同 from_node → to_node 的包裹
            existing_package = db.query(Package).filter(
                Package.schedule_id == schedule.id,
                Package.from_node_id == from_node_id,
                Package.to_node_id == to_node_id,
                Package.status.in_(["pending_pack", "packed"])
            ).first()

            if not existing_package:
                # 3.4 生成新包裹
                import time
                new_code = f"PKG{int(time.time() * 1000)}{len(new_package_codes)}"

                # 计算重量和体积
                total_weight = sum(float(item["goods"].weight) for item in group)
                total_volume = sum(float(item["goods"].volume) for item in group)

                # 构建 goods_items
                goods_items = []
                for item in group:
                    gs = item["gs"]
                    goods_items.append({
                        "goods_code": gs["goods_code"],
                        "order_code": gs["order_code"]
                    })

                new_package = Package(
                    package_code=new_code,
                    weight=total_weight,
                    volume=total_volume,
                    status="packed",  # 关键：新包裹状态为 packed
                    from_node_id=from_node_id,
                    to_node_id=to_node_id,
                    schedule_id=schedule.id,  # 关键：设置 schedule_id
                    goods_items=goods_items
                )
                db.add(new_package)
                new_package_codes.append(new_code)

            # 3.5 更新货物状态
            for item in group:
                item["goods"].status = "packed"

        return new_package_codes[0] if new_package_codes else None

    @staticmethod
    def _check_order_completion(db: Session, order: Order) -> None:
        """
        检查订单是否完成（所有货物都已 delivered）
        
        Args:
            db: 数据库会话
            order: 订单对象
        """
        all_goods = db.query(Goods).filter(Goods.order_id == order.id).all()
        all_delivered = all(g.status == "delivered" for g in all_goods)

        if all_delivered and order.status == "delivering":
            order.status = "completed"

    @staticmethod
    def _cascade_exception_packages(
        db: Session,
        schedule_code: str,
        package_code: str
    ) -> None:
        """
        级联下游包裹（若当前包裹异常，其下游包裹也标记为异常）
        
        逻辑：
        1. 查询异常包裹的 goods_items，获取所有货物
        2. 查询 global_schedule.goods_schedules，找到这些货物的 path
        3. 对每条 path：
           - 找到异常包裹的 to_node 在 path 中的位置
           - 将所有 to_node 在 path 中位于该位置之后的包裹标记为异常
        4. 更新这些包裹的状态为 exception，并记录日志
        
        Args:
            db: 数据库会话
            schedule_code: 调度方案编号
            package_code: 异常包裹编号
        """
        # 1. 查询异常包裹
        package = db.query(Package).filter(Package.package_code == package_code).first()
        if not package:
            return

        # 2. 获取异常包裹的货物列表
        goods_items = package.goods_items
        if isinstance(goods_items, str):
            import json
            goods_items = json.loads(goods_items)

        # 3. 查询 global_schedule
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        if not schedule:
            return

        goods_schedules = schedule.goods_schedules
        if isinstance(goods_schedules, str):
            import json
            goods_schedules = json.loads(goods_schedules)

        # 4. 构建货物 code → path 的映射
        goods_path_map = {}
        for gs in goods_schedules:
            goods_path_map[gs["goods_code"]] = gs["path"]

        # 5. 找到异常包裹的 to_node 在 path 中的位置
        from models.node import Node
        to_node = db.query(Node).filter(Node.id == package.to_node_id).first()
        if not to_node:
            return
        to_node_code = to_node.node_code

        # 6. 遍历所有包裹，标记下游包裹为异常
        all_packages = db.query(Package).filter(
            Package.schedule_id == schedule.id,
            Package.status == "in_transit"
        ).all()

        for pkg in all_packages:
            # 6.1 获取包裹的货物列表
            pkg_goods_items = pkg.goods_items
            if isinstance(pkg_goods_items, str):
                import json
                pkg_goods_items = json.loads(pkg_goods_items)

            # 6.2 检查包裹的任何货物是否在异常包裹的货物列表中
            for item in pkg_goods_items:
                goods_code = item["goods_code"]
                
                if goods_code in goods_path_map:
                    path = goods_path_map[goods_code]
                    
                    # 6.3 找到 to_node_code 在 path 中的位置
                    try:
                        to_index = path.index(to_node_code)
                        
                        # 6.4 找到当前包裹的 to_node 在 path 中的位置
                        pkg_to_node = db.query(Node).filter(Node.id == pkg.to_node_id).first()
                        if not pkg_to_node:
                            continue
                        pkg_to_node_code = pkg_to_node.node_code
                        
                        pkg_to_index = path.index(pkg_to_node_code)
                        
                        # 6.5 若当前包裹的 to_node 在异常包裹的 to_node 之后，则标记为异常
                        if pkg_to_index > to_index:
                            pkg.status = "exception"
                            
                            # 6.6 更新货物状态
                            for pkg_item in pkg_goods_items:
                                goods = db.query(Goods).filter(
                                    Goods.goods_code == pkg_item["goods_code"]
                                ).first()
                                if goods:
                                    goods.status = "exception"
                            
                            # 6.7 记录日志
                            import logging
                            logging.info(f"级联异常：包裹 {package_code} 异常，下游包裹 {pkg.package_code} 标记为异常")
                            break
                    except ValueError:
                        # to_node 不在 path 中，跳过
                        continue

    @staticmethod
    def get_arrival_packages(
        db: Session,
        schedule_code: str,
        node_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询到站包裹（状态为 in_transit 或 delivered 的包裹）
        
        Args:
            db: 数据库会话
            schedule_code: 调度方案编号
            node_code: 到站节点编号（不传则查所有）
            
        Returns:
            到站包裹列表
        """
        # 1. 查询 schedule
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        if not schedule:
            return []

        # 2. 查询包裹
        query = db.query(Package).filter(
            Package.schedule_id == schedule.id,
            Package.status.in_(["in_transit", "delivered"])
        )

        if node_code:
            from models.node import Node
            node = db.query(Node).filter(Node.node_code == node_code).first()
            if node:
                query = query.filter(Package.to_node_id == node.id)

        packages = query.all()

        # 3. 构建响应
        results = []
        for pkg in packages:
            from models.node import Node
            from_node = db.query(Node).filter(Node.id == pkg.from_node_id).first()
            to_node = db.query(Node).filter(Node.id == pkg.to_node_id).first()

            results.append({
                "package_code": pkg.package_code,
                "schedule_code": schedule_code,
                "from_node_code": from_node.node_code if from_node else "",
                "to_node_code": to_node.node_code if to_node else "",
                "status": pkg.status,
                "arrived_at": pkg.updated_at.isoformat() if pkg.updated_at else None
            })

        return results

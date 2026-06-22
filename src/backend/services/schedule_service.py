"""
调度编排服务

编排 F007 → F021 → 写库 的完整调度流程。
单事务保证原子性：global_schedules + packages + orders/goods 状态更新全部成功或全部回滚。

状态流转（与 API 契约 api-contract-phase3.md §3.2 一致）：

| 步骤    | 订单状态           | 货物状态               | 包裹状态              |
| ------- | ------------------ | ---------------------- | --------------------- |
| F007完成 | pending → delivering | pending_pack (不变)     | - (不涉及)            |
| F021完成 | delivering (不变)   | pending_pack → packed  | pending_pack → packed |
"""
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from algorithms.global_schedule import global_schedule
from algorithms.packaging import packaging
from models.global_schedule import GlobalSchedule
from models.order import Order
from models.goods import Goods
from models.package import Package
from utils.response import success_response, error_response


class ScheduleService:
    """调度编排服务"""

    @staticmethod
    async def create_global_schedule(
        order_codes: Optional[List[str]],
        algorithm: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        编排 F007 → F021 → 写库（单事务）

        流程（与 API 契约 api-contract-phase3.md §3.2 一致）：
        1. 调用 F007 全局调度算法（纯计算，不写状态）
        2. 调用 F021 打包算法（纯计算，生成 pending_pack 包裹）
        3a. F007 完成 → 写入 global_schedule + 订单 pending → delivering
        3b. F021 完成 → 写入 packages(pending_pack→packed) + 货物 pending_pack → packed
        4. db.commit() 单事务提交

        Args:
            order_codes: 订单编号列表（可选）
            algorithm: 算法类型
            db: 数据库会话

        Returns:
            统一响应格式 dict
        """
        try:
            # ── 1. F007 全局调度（纯计算） ──
            schedule_result = global_schedule(order_codes, algorithm, db)

            # ── 2. F021 打包（纯计算，暂不传 schedule_id） ──
            packages = packaging(schedule_result, None, db)

            # ── 3. 单事务写入 ──
            global_schedule_obj = GlobalSchedule(
                schedule_code=schedule_result["schedule_code"],
                order_codes=schedule_result["order_codes"],
                goods_schedules=schedule_result["goods_schedules"],
                total_distance=schedule_result["total_distance"],
                total_time=schedule_result["total_time"],
                total_goods=schedule_result["total_goods"],
                score=schedule_result["score"],
                algorithm_type=algorithm,
                version=1,
                is_replan=False,
            )
            db.add(global_schedule_obj)
            db.flush()  # 获取 global_schedule_obj.id

            # ── 3a. F007 完成 → 更新订单状态：pending → delivering ──
            for order_code in schedule_result["order_codes"]:
                order = db.query(Order).filter(Order.order_code == order_code).first()
                if order:
                    order.status = "delivering"

            # ── 3b. 写入 packages + F021 完成 → 更新货物和包裹状态 ──
            for pkg in packages:
                pkg.schedule_id = global_schedule_obj.id
                pkg.status = "packed"  # F021 打包完成：pending_pack → packed
                db.add(pkg)

            # F021 完成后更新货物状态：pending_pack → packed
            # 从生成的包裹中提取货物代码，只更新真正被打包的货物（防御性编程）
            packed_goods_codes = set()
            for pkg in packages:
                for item in pkg.goods_items:
                    packed_goods_codes.add(item["goods_code"])
            
            for gc in packed_goods_codes:
                goods = db.query(Goods).filter(Goods.goods_code == gc).first()
                if goods and goods.status == "pending_pack":  # 双重保险
                    goods.status = "packed"

            db.commit()

            return success_response(data={
                "schedule_code": schedule_result["schedule_code"],
                "total_distance": schedule_result["total_distance"],
                "total_time": schedule_result["total_time"],
                "total_goods": schedule_result["total_goods"],
                "score": schedule_result["score"],
                "package_count": len(packages),
                "version": 1,
                "is_replan": False,
            })

        except ValueError as e:
            db.rollback()
            return error_response(code=40001, message=f"全局调度失败: {str(e)}")

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"全局调度异常: {str(e)}")

    @staticmethod
    async def get_global_schedules(
        page: int,
        page_size: int,
        order_code: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        获取历史全局调度方案列表

        Args:
            page: 页码
            page_size: 每页数量
            order_code: 按订单编号筛选（可选）
            db: 数据库会话

        Returns:
            统一响应格式 dict
        """
        query = db.query(GlobalSchedule)

        if order_code:
            # JSON 字段包含匹配（SQLite 不支持 JSON_CONTAINS，用 LIKE）
            query = query.filter(
                GlobalSchedule.order_codes.cast(str).like(f"%{order_code}%")
            )

        total = query.count()
        schedules = (
            query.order_by(desc(GlobalSchedule.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for gs in schedules:
            pkg_count = db.query(Package).filter(
                Package.schedule_id == gs.id
            ).count()
            items.append({
                "schedule_code": gs.schedule_code,
                "total_distance": float(gs.total_distance),
                "total_time": float(gs.total_time),
                "total_goods": gs.total_goods,
                "score": float(gs.score),
                "package_count": pkg_count,
                "version": gs.version,
                "is_replan": gs.is_replan,
                "created_at": gs.created_at.isoformat() if gs.created_at else None,
            })

        return success_response(data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        })

    @staticmethod
    async def get_global_schedule(
        schedule_code: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        获取全局调度方案详情

        Args:
            schedule_code: 调度方案编号
            db: 数据库会话

        Returns:
            统一响应格式 dict
        """
        gs = (
            db.query(GlobalSchedule)
            .filter(GlobalSchedule.schedule_code == schedule_code)
            .first()
        )

        if not gs:
            return error_response(code=40401, message=f"调度方案不存在: {schedule_code}")

        # 查询关联 packages
        packages = (
            db.query(Package)
            .filter(Package.schedule_id == gs.id)
            .all()
        )

        pkg_list = []
        for pkg in packages:
            from_node = pkg.from_node
            to_node = pkg.to_node
            pkg_list.append({
                "package_code": pkg.package_code,
                "weight": float(pkg.weight),
                "volume": float(pkg.volume),
                "status": pkg.status,
                "from_node_code": from_node.node_code if from_node else None,
                "to_node_code": to_node.node_code if to_node else None,
                "goods_items": pkg.goods_items,
            })

        return success_response(data={
            "schedule_code": gs.schedule_code,
            "total_distance": float(gs.total_distance),
            "total_time": float(gs.total_time),
            "total_goods": gs.total_goods,
            "score": float(gs.score),
            "package_count": len(pkg_list),
            "version": gs.version,
            "is_replan": gs.is_replan,
            "goods_schedules": gs.goods_schedules,
            "packages": pkg_list,
            "created_at": gs.created_at.isoformat() if gs.created_at else None,
        })

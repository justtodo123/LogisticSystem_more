"""
节点调度服务

编排 F005 算法 → 写库 的完整调度流程。
单事务保证原子性：dispatch_batches + node_dispatches + packages/orders/goods 状态更新全部成功或全部回滚。

状态流转（与阶段4开发文档 §3.3 一致）：

| 步骤    | 包裹状态               | 货物状态               | 车辆状态         | 司机状态     |
| ------- | ---------------------- | ---------------------- | ---------------- | ------------ |
| F005完成 | packed → in_transit    | packed → in_transit     | idle → delivering | idle → busy |
"""
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from algorithms.node_dispatch import run_node_dispatch
from models.dispatch_batch import DispatchBatch
from models.node_dispatch import NodeDispatch
from models.node import Node
from models.package import Package
from models.goods import Goods
from models.vehicle import Vehicle
from models.driver import Driver
from models.order import Order
from schemas.dispatch import (
    DispatchBatchListResponse, DispatchBatchResponse,
    DispatchDetailResponse, DispatchesListResponse,
    NodeDispatchTaskResponse, PackageDetail, GoodsItemDetail,
)
from utils.response import success_response, error_response


class DispatchService:
    """节点调度服务"""

    # ── 辅助方法：构建单个 dispatch 的详情（含展开的 tasks） ──
    @staticmethod
    def _build_dispatch_detail(dispatch: "NodeDispatch", db: Session) -> Dict[str, Any]:
        """
        构建单个 dispatch 的详情，展开 tasks 中的 package_codes 为 package_details，
        并获取 node_name。
        
        Args:
            dispatch: NodeDispatch 对象
            db: 数据库会话
            
        Returns:
            包含 dispatch 详情的 dict（含展开的 tasks）
        """
        # 获取车辆和司机
        vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
        driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first() if dispatch.driver_id else None

        # 展开 tasks
        tasks_with_detail = []
        for task in dispatch.tasks:
            # 获取 from_node 和 to_node 的 name
            from_node = db.query(Node).filter(Node.node_code == task["from_node_code"]).first()
            to_node = db.query(Node).filter(Node.node_code == task["to_node_code"]).first()

            # 展开 package_codes 为 package_details
            package_details = []
            for pkg_code in task.get("package_codes", []):
                pkg = db.query(Package).filter(Package.package_code == pkg_code).first()
                if not pkg:
                    continue

                # 展开 goods_items
                goods_items_detail = []
                for gi in (pkg.goods_items or []):
                    g = db.query(Goods).filter(Goods.goods_code == gi["goods_code"]).first()
                    goods_items_detail.append({
                        "goods_code": gi["goods_code"],
                        "goods_name": g.goods_name if g else "",
                        "goods_type": g.goods_type if g else "",
                        "order_code": gi.get("order_code", ""),
                    })

                package_details.append({
                    "package_code": pkg.package_code,
                    "weight": float(pkg.weight),
                    "volume": float(pkg.volume),
                    "goods_items": goods_items_detail,
                })

            tasks_with_detail.append({
                "from_node_code": task["from_node_code"],
                "from_node_name": from_node.name if from_node else task["from_node_code"],
                "to_node_code": task["to_node_code"],
                "to_node_name": to_node.name if to_node else task["to_node_code"],
                "package_details": package_details,
                "is_return": task.get("is_return", False),
            })

        return {
            "dispatch_code": dispatch.dispatch_code,
            "vehicle_code": vehicle.vehicle_code if vehicle else None,
            "driver_code": driver.driver_code if driver else None,
            "level_phase": dispatch.level_phase,
            "tasks": tasks_with_detail,
            "total_distance": float(dispatch.total_distance),
            "total_time": float(dispatch.total_time),
        }

    @staticmethod
    async def create_node_dispatch(
        schedule_code: str,
        demo_mode: bool,
        db: Session,
        excluded_vehicles: Optional[List[str]] = None,
        is_replan: bool = False,
        custom_weights: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        编排 F005 算法 → 写库（单事务）
        
        流程（与阶段4开发文档 §3.3 一致）：
        1. 调用 F005 节点调度算法（纯计算）
        2. 写入 dispatch_batches + node_dispatches
        3. 更新 packages/orders/goods/vehicles/drivers 状态
        4. db.commit() 单事务提交
        
        Args:
            schedule_code: 全局调度方案编码
            demo_mode: 是否演示模式
            db: 数据库会话
            excluded_vehicles: 排除的车辆编码列表（可选，用于重规划规避异常车辆）
            is_replan: 是否为重规划模式（True=调度exception包裹，False=调度packed包裹）
            custom_weights: 自定义权重参数（可选，优先级高于 algorithm_config.json）
        
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 调用 F005 算法（纯计算，不提交事务）
            dispatch_result = run_node_dispatch(db, schedule_code, demo_mode, excluded_vehicles, is_replan=is_replan, custom_weights=custom_weights)
            
            # 2. 检查是否有调度明细创建
            dispatches = dispatch_result["dispatches"]
            unallocated_packages = dispatch_result.get("unallocated_packages", [])
            
            # 如果没有创建任何调度明细且所有包裹都未分配，则返回错误
            if not dispatches and unallocated_packages:
                db.rollback()
                return error_response(code=40001, message=f"节点调度失败：没有可用的车辆完成调度，{len(unallocated_packages)}个包裹未分配")
            
            # 3. 状态更新已由 run_node_dispatch() 内部完成
            #     (_write_dispatches() → update_state_after_f005())
            batch_code = dispatch_result["batch_code"]
            
            # 4. 提交事务
            db.commit()
            
            # 5. 返回结果
            return success_response(data={
                "batch_code": batch_code,
                "status": dispatch_result["status"],
                "dispatches": dispatches,
                "unallocated_packages": unallocated_packages
            })
            
        except Exception as e:
            db.rollback()
            # 检查是否是调度方案不存在的错误
            error_msg = str(e)
            if "不存在" in error_msg:
                # 提取调度方案编码
                if "全局调度方案不存在：" in error_msg:
                    return error_response(code=40401, message=error_msg)
            return error_response(code=40001, message=f"节点调度失败：{error_msg}")

    @staticmethod
    async def get_dispatch_batches(
        schedule_code: Optional[str],
        status: Optional[str],
        db: Session,
    ) -> Dict[str, Any]:
        """
        查询调度批次列表
        
        Args:
            schedule_code: 调度方案编码（可选）
            status: 状态筛选（可选）
            db: 数据库会话
        
        Returns:
            统一响应格式 dict
        """
        # 导入模型（避免循环导入）
        from models.global_schedule import GlobalSchedule
        
        # 构建查询
        query = db.query(DispatchBatch)
        
        # 按调度方案筛选
        if schedule_code:
            schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == schedule_code
            ).first()
            if schedule:
                query = query.filter(DispatchBatch.global_schedule_id == schedule.id)
        
        # 按状态筛选
        if status:
            query = query.filter(DispatchBatch.status == status)
        
        # 执行查询
        batches = query.order_by(DispatchBatch.created_at.desc()).all()
        
        # 构建响应（使用 Pydantic schema）
        items = []
        for batch in batches:
            # 获取调度方案编码
            schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.id == batch.global_schedule_id
            ).first()
            schedule_code = schedule.schedule_code if schedule else None
            
            # 构建批次响应（使用DispatchBatch表中的字段）
            batch_data = {
                "batch_code": batch.batch_code,
                "schedule_code": schedule_code,
                "status": batch.status,
                "demo_mode": batch.demo_mode if hasattr(batch, 'demo_mode') else False,
                "l0_l1_dispatch_count": batch.l0_l1_dispatch_count,
                "l1_l2_dispatch_count": batch.l1_l2_dispatch_count,
                "unallocated_packages": [],  # 列表视图暂不返回，详情接口返回
                "created_at": batch.created_at,
                "updated_at": batch.updated_at,
                "dispatches": None  # 列表视图不返回调度明细
            }
            items.append(DispatchBatchResponse(**batch_data))
        
        # 使用 Pydantic schema 序列化
        response_data = DispatchBatchListResponse(items=items, total=len(items))
        return success_response(data=response_data.model_dump())

    @staticmethod
    async def get_dispatch_batch_detail(
        batch_code: str,
        db: Session,
        vehicle_code: Optional[str] = None,
        level_phase: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        查询调度批次详情（P1-07 新增过滤参数）
        
        Args:
            batch_code: 批次编码
            db: 数据库会话
            vehicle_code: 按车辆编码过滤（可选）
            level_phase: 按层级阶段过滤（可选，0=L0→L1，1=L1→L2）
        
        Returns:
            统一响应格式 dict
        """
        # 查询调度批次
        batch = db.query(DispatchBatch).filter(
            DispatchBatch.batch_code == batch_code
        ).first()
        
        if not batch:
            return error_response(code=40402, message=f"调度批次不存在：{batch_code}")
        
        # 获取调度方案编码
        from models.global_schedule import GlobalSchedule
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.id == batch.global_schedule_id
        ).first()
        schedule_code = schedule.schedule_code if schedule else None
        
        # 查询调度明细（支持过滤）
        query = db.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id == batch.id
        )
        
        # 按车辆过滤
        if vehicle_code:
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if vehicle:
                query = query.filter(NodeDispatch.vehicle_id == vehicle.id)
        
        # 按 level_phase 过滤
        if level_phase is not None:
            query = query.filter(NodeDispatch.level_phase == level_phase)
        
        dispatches = query.all()
        
        # 构建调度明细响应（使用辅助方法展开 tasks）
        dispatch_list = []
        for dispatch in dispatches:
            detail = DispatchService._build_dispatch_detail(dispatch, db)
            dispatch_list.append(detail)
        
        # 解析 unallocated_packages（JSON 字符串 → 列表）
        unallocated_packages = []
        if batch.unallocated_packages:
            try:
                import json
                unallocated_packages = json.loads(batch.unallocated_packages)
            except:
                unallocated_packages = []
        
        # 构建响应
        return success_response(data={
            "batch_code": batch.batch_code,
            "schedule_code": schedule_code,
            "status": batch.status,
            "unallocated_packages": unallocated_packages,
            "dispatches": dispatch_list
        })

    @staticmethod
    async def get_batch_dispatches(
        batch_code: str,
        db: Session,
        vehicle_code: Optional[str] = None,
        level_phase: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        按批次查询调度明细列表（P1-07 新增端点）
        
        Args:
            batch_code: 批次编码
            db: 数据库会话
            vehicle_code: 按车辆编码过滤（可选）
            level_phase: 按层级阶段过滤（可选，0=L0→L1，1=L1→L2）
        
        Returns:
            统一响应格式 dict（含 dispatches 列表）
        """
        # 验证批次存在
        batch = db.query(DispatchBatch).filter(
            DispatchBatch.batch_code == batch_code
        ).first()
        
        if not batch:
            return error_response(code=40402, message=f"调度批次不存在：{batch_code}")
        
        # 复用 get_dispatch_batch_detail 的过滤逻辑
        query = db.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id == batch.id
        )
        
        # 按车辆过滤
        if vehicle_code:
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if vehicle:
                query = query.filter(NodeDispatch.vehicle_id == vehicle.id)
        
        # 按 level_phase 过滤
        if level_phase is not None:
            query = query.filter(NodeDispatch.level_phase == level_phase)
        
        dispatches = query.all()
        
        # 构建响应（使用辅助方法）
        dispatch_list = []
        for dispatch in dispatches:
            detail = DispatchService._build_dispatch_detail(dispatch, db)
            dispatch_list.append(detail)
        
        return success_response(data={
            "items": dispatch_list,
            "total": len(dispatch_list)
        })

    @staticmethod
    async def get_schedule_dispatches(
        schedule_code: str,
        db: Session,
        vehicle_code: Optional[str] = None,
        level_phase: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        按方案查询所有调度明细列表（P1-07 新增端点）
        
        查询指定方案下所有批次的调度明细。
        
        Args:
            schedule_code: 调度方案编码
            db: 数据库会话
            vehicle_code: 按车辆编码过滤（可选）
            level_phase: 按层级阶段过滤（可选，0=L0→L1，1=L1→L2）
        
        Returns:
            统一响应格式 dict（含 dispatches 列表）
        """
        # 查询调度方案
        from models.global_schedule import GlobalSchedule
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code == schedule_code
        ).first()
        
        if not schedule:
            return error_response(code=40401, message=f"调度方案不存在：{schedule_code}")
        
        # 查询该方案下的所有批次
        batches = db.query(DispatchBatch).filter(
            DispatchBatch.global_schedule_id == schedule.id
        ).all()
        
        if not batches:
            return success_response(data={"items": [], "total": 0})
        
        # 构建批次 ID 列表
        batch_ids = [b.id for b in batches]
        
        # 查询所有批次下的调度明细（支持过滤）
        query = db.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id.in_(batch_ids)
        )
        
        # 按车辆过滤
        if vehicle_code:
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if vehicle:
                query = query.filter(NodeDispatch.vehicle_id == vehicle.id)
        
        # 按 level_phase 过滤
        if level_phase is not None:
            query = query.filter(NodeDispatch.level_phase == level_phase)
        
        dispatches = query.all()
        
        # 构建响应（使用辅助方法）
        dispatch_list = []
        for dispatch in dispatches:
            detail = DispatchService._build_dispatch_detail(dispatch, db)
            dispatch_list.append(detail)
        
        return success_response(data={
            "items": dispatch_list,
            "total": len(dispatch_list)
        })

    @staticmethod
    async def get_dispatch_detail(
        dispatch_code: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        查询单个调度明细详情（P1-07 新增端点）
        
        Args:
            dispatch_code: 调度明细编码
            db: 数据库会话
        
        Returns:
            统一响应格式 dict（含单个 dispatch 详情）
        """
        # 查询调度明细
        dispatch = db.query(NodeDispatch).filter(
            NodeDispatch.dispatch_code == dispatch_code
        ).first()
        
        if not dispatch:
            return error_response(code=40403, message=f"调度明细不存在：{dispatch_code}")
        
        # 使用辅助方法构建详情
        detail = DispatchService._build_dispatch_detail(dispatch, db)
        
        return success_response(data=detail)


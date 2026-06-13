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
from models.package import Package
from models.goods import Goods
from models.vehicle import Vehicle
from models.driver import Driver
from models.order import Order
from models.global_schedule import GlobalSchedule
from utils.response import success_response, error_response


class DispatchService:
    """节点调度服务"""

    @staticmethod
    async def create_node_dispatch(
        schedule_code: str,
        demo_mode: bool,
        db: Session,
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
        
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 调用 F005 算法（纯计算，不提交事务）
            dispatch_result = run_node_dispatch(db, schedule_code, demo_mode)
            
            # 2. 更新状态（包裹、货物、车辆、司机）
            batch_code = dispatch_result["batch_code"]
            dispatches = dispatch_result["dispatches"]
            batch_status = dispatch_result["status"]
            
            # 更新车辆和司机状态
            for dispatch_data in dispatches:
                # 更新车辆状态：idle → delivering
                vehicle = db.query(Vehicle).filter(
                    Vehicle.vehicle_code == dispatch_data["vehicle_code"]
                ).first()
                if vehicle:
                    vehicle.status = 'delivering'
                
                # 更新司机状态：idle → busy
                if dispatch_data.get("driver_code"):
                    driver = db.query(Driver).filter(
                        Driver.driver_code == dispatch_data["driver_code"]
                    ).first()
                    if driver:
                        driver.status = 'busy'
            
            # 3. 【新增】仅当F005两次都完成后（status="completed"）才调用F006
            if batch_status == "completed":
                from services.route_service import RouteService
                await RouteService.create_route_planning(
                    batch_code=batch_code,
                    dispatch_codes=None,  # 处理批次下所有dispatch
                    db=db
                )
            
            # 4. 提交事务
            db.commit()
            
            # 4. 返回结果
            return success_response(data={
                "batch_code": batch_code,
                "status": dispatch_result["status"],
                "dispatches": dispatches
            })
            
        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"节点调度失败：{str(e)}")

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
        
        # 构建响应
        items = []
        for batch in batches:
            # 获取调度方案编码
            schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.id == batch.global_schedule_id
            ).first()
            schedule_code = schedule.schedule_code if schedule else None
            
            items.append({
                "batch_code": batch.batch_code,
                "schedule_code": schedule_code,
                "status": batch.status,
                "created_at": batch.created_at.isoformat() if batch.created_at else None
            })
        
        return success_response(data={
            "items": items,
            "total": len(items)
        })

    @staticmethod
    async def get_dispatch_batch_detail(
        batch_code: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        查询调度批次详情
        
        Args:
            batch_code: 批次编码
            db: 数据库会话
        
        Returns:
            统一响应格式 dict
        """
        # 查询调度批次
        batch = db.query(DispatchBatch).filter(
            DispatchBatch.batch_code == batch_code
        ).first()
        
        if not batch:
            return error_response(code=404, message=f"调度批次不存在：{batch_code}")
        
        # 获取调度方案编码
        from models.global_schedule import GlobalSchedule
        schedule = db.query(GlobalSchedule).filter(
            GlobalSchedule.id == batch.global_schedule_id
        ).first()
        schedule_code = schedule.schedule_code if schedule else None
        
        # 查询调度明细
        dispatches = db.query(NodeDispatch).filter(
            NodeDispatch.dispatch_batch_id == batch.id
        ).all()
        
        # 构建调度明细响应
        dispatch_list = []
        for dispatch in dispatches:
            # 获取车辆和司机编码
            vehicle = db.query(Vehicle).filter(Vehicle.id == dispatch.vehicle_id).first()
            driver = db.query(Driver).filter(Driver.id == dispatch.driver_id).first() if dispatch.driver_id else None
            
            dispatch_list.append({
                "dispatch_code": dispatch.dispatch_code,
                "vehicle_code": vehicle.vehicle_code if vehicle else None,
                "driver_code": driver.driver_code if driver else None,
                "level_phase": dispatch.level_phase,
                "tasks": dispatch.tasks,
                "total_distance": float(dispatch.total_distance),
                "total_time": float(dispatch.total_time)
            })
        
        # 构建响应
        return success_response(data={
            "batch_code": batch.batch_code,
            "schedule_code": schedule_code,
            "status": batch.status,
            "dispatches": dispatch_list
        })

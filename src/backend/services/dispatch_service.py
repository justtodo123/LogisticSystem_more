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
from schemas.dispatch import DispatchBatchListResponse, DispatchBatchResponse
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
            
            # 2. 检查是否有调度明细创建
            dispatches = dispatch_result["dispatches"]
            unallocated_packages = dispatch_result.get("unallocated_packages", [])
            
            # 如果没有创建任何调度明细且所有包裹都未分配，则返回错误
            if not dispatches and unallocated_packages:
                db.rollback()
                return error_response(code=40001, message=f"节点调度失败：没有可用的车辆完成调度，{len(unallocated_packages)}个包裹未分配")
            
            # 3. 更新状态（包裹、货物、车辆、司机）
            batch_code = dispatch_result["batch_code"]
            
            # demo_mode=true 时，算法内部已通过 simulate 函数正确处理了所有状态
            # （车辆/driver 已恢复为 idle），服务层不需要再次更新，否则会覆盖正确状态
            if not demo_mode:
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
            return error_response(code=40402, message=f"调度批次不存在：{batch_code}")
        
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

"""
重规划服务（方案A：不修改现有服务层）

在 ReplanService 中实现版本链逻辑：
1. 读取原调度方案
2. 直接调用现有服务层（不修改它们）
3. 在 ReplanService 中更新新方案的版本链字段

阶段7新增。
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.route import Route
from models.node_dispatch import NodeDispatch
from models.dispatch_batch import DispatchBatch
from models.vehicle import Vehicle
from utils.response import success_response, error_response


class ReplanService:
    """重规划服务（方案A：不修改现有服务层）"""

    @staticmethod
    async def redispatch(
        db: Session,
        original_schedule_code: str,
        replan_reason: str,
        event: Optional[ExceptionEvent] = None,
        custom_weights: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        重调度（F007→F021→F005→F006）

        流程：
        1. 读取原调度方案（GlobalSchedule）
        2. 获取相关订单编号
        3. 提取排除参数（excluded_nodes）
        4. 调用现有 ScheduleService.create_global_schedule()（不修改它）
        5. 更新新版调度方案的版本链字段
        6. 调用 DispatchService.create_node_dispatch() 执行节点调度
        7. 返回新调度方案编码

        Args:
            db: 数据库会话
            original_schedule_code: 原调度方案业务编号
            replan_reason: 重规划原因
            event: 异常事件对象（可选，用于提取排除参数）
            custom_weights: 自定义权重参数（可选，用于AI驱动的重规划）

        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 读取原调度方案
            original = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == original_schedule_code
            ).first()

            if not original:
                return error_response(
                    code=40401,
                    message=f"原调度方案不存在: {original_schedule_code}",
                )

            # 2. 获取相关订单编号
            order_codes = original.order_codes
            algorithm = original.algorithm_type or "traditional"

            # 3. 提取排除参数
            excluded_nodes = []
            excluded_vehicles = []
            if event:
                if event.target_type == "node" and event.target_code:
                    excluded_nodes.append(event.target_code)
                elif event.target_type == "vehicle" and event.target_code:
                    excluded_vehicles.append(event.target_code)
                    # 同时从关联调度明细中查找该车辆参与的所有调度
                    vehicle = db.query(Vehicle).filter(
                        Vehicle.vehicle_code == event.target_code
                    ).first()
                    if vehicle:
                        dispatches = db.query(NodeDispatch).filter(
                            NodeDispatch.vehicle_id == vehicle.id
                        ).all()
                        for d in dispatches:
                            v = db.query(Vehicle).filter(Vehicle.id == d.vehicle_id).first()
                            if v and v.vehicle_code not in excluded_vehicles:
                                excluded_vehicles.append(v.vehicle_code)

            # 4. 调用现有服务层（不修改它们）
            from services.schedule_service import ScheduleService

            schedule_result = await ScheduleService.create_global_schedule(
                order_codes=order_codes,
                algorithm=algorithm,
                db=db,
                excluded_nodes=excluded_nodes if excluded_nodes else None,
                is_replan=True,  # 重规划模式：只调度 exception 订单
                custom_weights=custom_weights,  # AI驱动的自定义权重
            )

            # 检查调度是否成功
            if schedule_result.get("code") != 0:
                return schedule_result

            new_schedule_code = schedule_result["data"]["schedule_code"]

            # 4. 更新新版调度方案的版本链字段
            new_schedule = db.query(GlobalSchedule).filter(
                GlobalSchedule.schedule_code == new_schedule_code
            ).first()

            if new_schedule:
                new_schedule.version = original.version + 1
                new_schedule.parent_id = original.id
                new_schedule.replan_reason = replan_reason
                new_schedule.is_replan = True
                db.commit()

            # 5. 继续调用节点调度（获取该方案的完整结果）
            #    注：重规划只生成方案，不走 demo_mode 自动送达
            from services.dispatch_service import DispatchService

            dispatch_result = await DispatchService.create_node_dispatch(
                schedule_code=new_schedule_code,
                demo_mode=False,  # 重规划只生成方案，不模拟送达
                db=db,
                excluded_vehicles=excluded_vehicles if excluded_vehicles else None,
                is_replan=True,  # 重规划模式：只调度 exception 包裹
                custom_weights=custom_weights,  # AI驱动的自定义权重
            )

            # 提取批次编码（节点调度可能失败，不影响主结果）
            batch_code = None
            if isinstance(dispatch_result, dict) and dispatch_result.get("code") == 0:
                batch_code = dispatch_result["data"].get("batch_code")

            return success_response(data={
                "schedule_code": new_schedule_code,
                "new_schedule_code": new_schedule_code,
                "batch_code": batch_code,
                "version": new_schedule.version if new_schedule else original.version + 1,
                "is_replan": True,
                "replan_reason": replan_reason,
                "original_schedule_code": original_schedule_code,
            })

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"重调度失败: {str(e)}")

    @staticmethod
    async def reroute(
        db: Session,
        original_route_code: str,
        replan_reason: str,
        excluded_vehicles: Optional[List[str]] = None,
        custom_weights: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        重路径规划（F006）
        
        流程：
        1. 读取原路径规划（Route）
        2. 通过 dispatch_id 找到关联的 dispatch_batch
        3. 获取同批次下所有 dispatch_codes
        4. 调用现有 RouteService.create_route_planning()（不修改它）
        5. 更新新路径规划的版本链字段
        6. 返回新路径规划编码
        
        Args:
            db: 数据库会话
            original_route_code: 原路径规划业务编号
            replan_reason: 重规划原因
            excluded_vehicles: 排除的车辆编码列表（可选，用于重规划规避异常车辆）
            custom_weights: 自定义权重参数（可选，用于AI驱动的重规划）
        
        Returns:
            统一响应格式 dict
        """
        try:
            # 1. 读取原路径规划
            original_route = db.query(Route).filter(
                Route.route_code == original_route_code
            ).first()

            if not original_route:
                return error_response(
                    code=40401,
                    message=f"原路径规划不存在: {original_route_code}",
                )

            # 2. 通过 dispatch_id 找到关联的 dispatch_batch
            dispatch = db.query(NodeDispatch).filter(
                NodeDispatch.id == original_route.dispatch_id
            ).first()

            if not dispatch:
                return error_response(
                    code=40001,
                    message=f"原路径规划关联的调度明细不存在",
                )

            batch = db.query(DispatchBatch).filter(
                DispatchBatch.id == dispatch.dispatch_batch_id
            ).first()

            if not batch:
                return error_response(
                    code=40001,
                    message=f"原路径规划关联的调度批次不存在",
                )

            # 3. 获取同批次下所有 dispatch_codes（仅重规划当前 dispatch 的路线）
            dispatch_codes = [dispatch.dispatch_code]

            # 4. 调用现有路径规划服务（不修改它）
            from services.route_service import RouteService

            route_result = await RouteService.create_route_planning(
                batch_code=batch.batch_code,
                dispatch_codes=dispatch_codes,
                db=db,
                excluded_vehicles=excluded_vehicles if excluded_vehicles else None,
                custom_weights=custom_weights,  # AI驱动的自定义权重
            )

            # 检查路径规划是否成功
            if route_result.get("code") != 0:
                return route_result

            new_routes_data = route_result["data"].get("routes", [])
            new_route_codes = [r["route_code"] for r in new_routes_data]

            # 5. 更新新路径规划的版本链字段
            for rc in new_route_codes:
                new_route = db.query(Route).filter(
                    Route.route_code == rc
                ).first()
                if new_route:
                    new_route.version = original_route.version + 1
                    new_route.parent_id = original_route.id
                    new_route.replan_reason = replan_reason
                    new_route.is_replan = True

            db.commit()

            new_route_code = new_route_codes[0] if new_route_codes else None

            return success_response(data={
                "batch_code": batch.batch_code,
                "route_codes": new_route_codes,
                "new_route_code": new_route_code,
                "version": original_route.version + 1,
                "is_replan": True,
                "replan_reason": replan_reason,
                "original_route_code": original_route_code,
            })

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"重路径规划失败: {str(e)}")

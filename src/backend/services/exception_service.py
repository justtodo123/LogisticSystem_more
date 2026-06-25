"""
异常事件服务

提供异常事件的 CRUD 操作和重规划触发。
阶段7新增（方案A：不修改现有服务层）。
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import time

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.node_dispatch import NodeDispatch
from models.route import Route
from models.order import Order
from models.goods import Goods
from models.package import Package
from models.vehicle import Vehicle
from models.node import Node
from schemas.exception_event import (
    CreateExceptionEventRequest,
    ExceptionEventResponse,
)
from utils.response import success_response, error_response
from services.state_machine import (
    mark_exception_statuses,
    mark_vehicle_exception,
    transition_vehicle_status,
)

# 允许的枚举值
ALLOWED_EXCEPTION_TYPES = {"road", "package", "node"}
ALLOWED_ACTIONS = {"redispatch", "reroute"}


class ExceptionService:
    """异常事件服务"""

    # ── 工具方法 ───────────────────────────────────────────────

    @staticmethod
    def _generate_event_code() -> str:
        """生成异常事件编号：EX + 时间戳 + 随机后缀"""
        ts = int(time.time() * 1000)
        return f"EX{ts}"

    @staticmethod
    def _to_response(event: ExceptionEvent, db: Session) -> ExceptionEventResponse:
        """将 ORM 对象转为响应模型"""
        return ExceptionEventResponse(
            event_code=event.event_code,
            exception_type=event.exception_type,
            exception_subtype=event.exception_subtype,
            target_type=event.target_type,
            target_code=event.target_code,
            recommended_action=event.recommended_action,
            related_schedule_code=event.related_schedule_code,
            replan_batch_code=event.replan_batch_code,
            description=event.description,
            status=event.status,
            resolved_at=event.resolved_at,
            created_at=event.created_at,
        )

    @staticmethod
    def _verify_target(db: Session, target_type: str, target_code: str) -> bool:
        """
        校验 target_code 在对应表中是否存在

        - node    → nodes 表
        - route   → routes 表
        - package → packages 表
        - vehicle → vehicles 表
        """
        target_map = {
            "node": (Node, Node.node_code),
            "route": (Route, Route.route_code),
            "package": (Package, Package.package_code),
            "vehicle": (Vehicle, Vehicle.vehicle_code),
        }
        entry = target_map.get(target_type)
        if not entry:
            return True  # 未知 target_type 不在此处阻断（Schema 层已校验）
        model_cls, col = entry
        return db.query(model_cls).filter(col == target_code).first() is not None

    # ── CRUD 方法 ───────────────────────────────────────────────

    @staticmethod
    async def create_exception_event(
        db: Session,
        data: CreateExceptionEventRequest,
    ) -> Dict[str, Any]:
        """
        创建异常事件

        流程：
        1. 验证 related_schedule_code 是否存在
        2. 生成 event_code
        3. 写入数据库
        """
        # 0. 校验 exception_type（Schema 层已校验，此处兜底）
        if data.exception_type not in ALLOWED_EXCEPTION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"无效的异常类型: {data.exception_type}，允许值: {', '.join(sorted(ALLOWED_EXCEPTION_TYPES))}",
            )

        try:
            # 1. 验证 target_code 对应实体是否存在
            if data.target_type and data.target_code:
                target_exists = ExceptionService._verify_target(db, data.target_type, data.target_code)
                if not target_exists:
                    return error_response(
                        code=40001,
                        message=f"target_code 不存在: {data.target_type}={data.target_code}",
                    )

            # 2. 验证 related_schedule_code
            if data.related_schedule_code:
                schedule = db.query(GlobalSchedule).filter(
                    GlobalSchedule.schedule_code == data.related_schedule_code
                ).first()
                if not schedule:
                    return error_response(
                        code=40401,
                        message=f"关联调度方案不存在: {data.related_schedule_code}",
                    )

            # 2. 生成 event_code
            event_code = ExceptionService._generate_event_code()

            # 3. 重置关联订单/货物/包裹状态为 exception
            if data.related_schedule_code:
                # 重新查询调度方案（确保会话活跃）
                # 统一标记异常状态（调度方案关联的实体）
                mark_exception_statuses(db, data.related_schedule_code)

            # 4. 处理车辆异常（如果 target_type 是 vehicle）
            if data.target_type == "vehicle" and data.target_code:
                vehicle = db.query(Vehicle).filter(
                    Vehicle.vehicle_code == data.target_code
                ).first()
                if vehicle:
                    # 将车辆状态设为 disabled（异常事件强制）
                    transition_vehicle_status(db, vehicle, "disabled", force=True)

                    # 统一标记车辆关联实体状态（包裹→exception，货物→exception）
                    mark_vehicle_exception(db, data.target_code)

            # 5. 写入数据库
            event = ExceptionEvent(
                event_code=event_code,
                exception_type=data.exception_type,
                exception_subtype=data.exception_subtype,
                target_type=data.target_type,
                target_code=data.target_code,
                recommended_action=data.recommended_action,
                related_schedule_code=data.related_schedule_code,
                description=data.description,
                status="open",
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            return success_response(
                data=ExceptionService._to_response(event, db).model_dump()
            )

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"创建异常事件失败: {str(e)}")

    @staticmethod
    async def get_exception_events(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        exception_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        查询异常事件列表（分页、筛选）

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页数量
            status: 状态筛选（open / resolved）
            exception_type: 异常类型筛选（road / package / node）
        """
        query = db.query(ExceptionEvent)

        if status:
            query = query.filter(ExceptionEvent.status == status)
        if exception_type:
            query = query.filter(ExceptionEvent.exception_type == exception_type)

        total = query.count()
        events = (
            query.order_by(desc(ExceptionEvent.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [ExceptionService._to_response(e, db).model_dump() for e in events]

        return success_response(data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        })

    @staticmethod
    async def get_exception_event_by_code(
        db: Session,
        event_code: str,
    ) -> Dict[str, Any]:
        """
        查询异常事件详情
        """
        event = db.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == event_code
        ).first()

        if not event:
            return error_response(
                code=40401,
                message=f"异常事件不存在: {event_code}",
            )

        return success_response(
            data=ExceptionService._to_response(event, db).model_dump()
        )

    @staticmethod
    async def update_exception(
        db: Session,
        event_code: str,
        status: Optional[str] = None,
        resolution_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新异常事件

        支持更新 status。当 status 设为 resolved 时，自动记录 resolved_at。
        """
        event = db.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == event_code
        ).first()

        if not event:
            return error_response(
                code=40401,
                message=f"异常事件不存在: {event_code}",
            )

        if status:
            event.status = status
            if status == "resolved":
                event.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.commit()
        db.refresh(event)

        return success_response(
            data=ExceptionService._to_response(event, db).model_dump()
        )

    @staticmethod
    async def resolve_exception(
        db: Session,
        event_code: str,
        resolution_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        标记异常已解决

        流程：
        1. 查询异常事件
        2. 更新 status → resolved
        3. 记录 resolved_at
        """
        event = db.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == event_code
        ).first()

        if not event:
            return error_response(
                code=40401,
                message=f"异常事件不存在: {event_code}",
            )

        if event.status == "resolved":
            return error_response(
                code=40001,
                message=f"异常事件已解决，无需重复操作: {event_code}",
            )

        event.status = "resolved"
        event.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(event)

        return success_response(
            data=ExceptionService._to_response(event, db).model_dump()
        )

    @staticmethod
    async def trigger_replan(
        db: Session,
        event_code: str,
        action: str,
        replan_reason: str,
    ) -> Dict[str, Any]:
        """
        触发重规划

        流程：
        1. 查询异常事件
        2. 校验 action 合法性
        3. 根据 action 调用不同的重规划服务：
           - redispatch → ReplanService.redispatch()
           - reroute → ReplanService.reroute()
        4. 更新 exception_event.replan_batch_code
        5. 返回新调度方案编码
        """
        # 校验 action
        if action not in ALLOWED_ACTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"无效的重规划动作: {action}，允许值: {', '.join(sorted(ALLOWED_ACTIONS))}",
            )

        event = db.query(ExceptionEvent).filter(
            ExceptionEvent.event_code == event_code
        ).first()

        if not event:
            return error_response(
                code=40401,
                message=f"异常事件不存在: {event_code}",
            )

        if event.status == "resolved":
            return error_response(
                code=40001,
                message=f"异常事件已解决，无法触发重规划: {event_code}",
            )

        # 延迟导入避免循环依赖
        from services.replan_service import ReplanService

        try:
            if action == "redispatch":
                if not event.related_schedule_code:
                    return error_response(
                        code=40001,
                        message="重调度需要关联调度方案(related_schedule_code)",
                    )
                result = await ReplanService.redispatch(
                    db=db,
                    original_schedule_code=event.related_schedule_code,
                    replan_reason=replan_reason,
                    event=event,  # 传递异常事件以提取排除参数
                )

            elif action == "reroute":
                # 通过 target_type=route + target_code 查找关联路线
                route = None
                if event.target_type == "route" and event.target_code:
                    route = db.query(Route).filter(
                        Route.route_code == event.target_code
                    ).first()
                
                if not route:
                    return error_response(
                        code=40001,
                        message="重路径规划需要关联路线(target_type=route, target_code=路线编码)",
                    )
                
                # 提取排除车辆参数
                excluded_vehicles = []
                if route.dispatch_id:
                    dispatch = db.query(NodeDispatch).filter(
                        NodeDispatch.id == route.dispatch_id
                    ).first()
                    if dispatch and dispatch.vehicle_id:
                        vehicle = db.query(Vehicle).filter(
                            Vehicle.id == dispatch.vehicle_id
                        ).first()
                        if vehicle:
                            excluded_vehicles.append(vehicle.vehicle_code)
                
                result = await ReplanService.reroute(
                    db=db,
                    original_route_code=route.route_code,
                    replan_reason=replan_reason,
                    excluded_vehicles=excluded_vehicles if excluded_vehicles else None,
                )
            else:
                return error_response(
                    code=40001,
                    message=f"不支持的重规划类型: {action}",
                )

            # 更新 exception_event.replan_batch_code
            if isinstance(result, dict) and result.get("data"):
                new_code = result["data"].get("schedule_code") or result["data"].get("batch_code")
                if new_code:
                    event.replan_batch_code = new_code
                    db.commit()

            return result

        except Exception as e:
            db.rollback()
            return error_response(code=40001, message=f"重规划失败: {str(e)}")

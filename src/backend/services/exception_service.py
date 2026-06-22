"""
异常事件服务

提供异常事件的 CRUD 操作和重规划触发。
阶段7新增（方案A：不修改现有服务层）。
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import time

from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.exception_event import ExceptionEvent
from models.global_schedule import GlobalSchedule
from models.node import Node
from models.route import Route
from schemas.exception_event import (
    CreateExceptionEventRequest,
    ExceptionEventResponse,
)
from utils.response import success_response, error_response


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
        trigger_node_code = None
        if event.trigger_node_id:
            node = db.query(Node).filter(Node.id == event.trigger_node_id).first()
            trigger_node_code = node.node_code if node else None

        related_route_code = None
        if event.related_route_id:
            route = db.query(Route).filter(Route.id == event.related_route_id).first()
            related_route_code = route.route_code if route else None

        return ExceptionEventResponse(
            event_code=event.event_code,
            exception_type=event.exception_type,
            exception_subtype=event.exception_subtype,
            target_type=event.target_type,
            target_code=event.target_code,
            severity=event.severity,
            recommended_action=event.recommended_action,
            trigger_node_code=trigger_node_code,
            related_route_code=related_route_code,
            related_schedule_code=event.related_schedule_code,
            replan_batch_code=event.replan_batch_code,
            description=event.description,
            status=event.status,
            resolution_note=event.resolution_note,
            resolved_at=event.resolved_at,
            created_at=event.created_at,
        )

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
        2. 解析 trigger_node_code / related_route_code 为内部 ID
        3. 生成 event_code
        4. 写入数据库
        """
        try:
            # 1. 验证 related_schedule_code
            if data.related_schedule_code:
                schedule = db.query(GlobalSchedule).filter(
                    GlobalSchedule.schedule_code == data.related_schedule_code
                ).first()
                if not schedule:
                    return error_response(
                        code=40401,
                        message=f"关联调度方案不存在: {data.related_schedule_code}",
                    )

            # 2. 解析 trigger_node_code → trigger_node_id
            trigger_node_id = None
            if data.trigger_node_code:
                node = db.query(Node).filter(
                    Node.node_code == data.trigger_node_code
                ).first()
                if node:
                    trigger_node_id = node.id

            # 3. 解析 related_route_code → related_route_id
            related_route_id = None
            if data.related_route_code:
                route = db.query(Route).filter(
                    Route.route_code == data.related_route_code
                ).first()
                if route:
                    related_route_id = route.id

            # 4. 生成 event_code
            event_code = ExceptionService._generate_event_code()

            # 5. 写入数据库
            event = ExceptionEvent(
                event_code=event_code,
                exception_type=data.exception_type,
                exception_subtype=data.exception_subtype,
                target_type=data.target_type,
                target_code=data.target_code,
                severity=data.severity or "medium",
                recommended_action=data.recommended_action,
                trigger_node_id=trigger_node_id,
                related_route_id=related_route_id,
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
        3. 记录 resolution_note 和 resolved_at
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
        event.resolution_note = resolution_note
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
        replan_reason: str,
    ) -> Dict[str, Any]:
        """
        触发重规划

        流程：
        1. 查询异常事件
        2. 根据 recommended_action 调用不同的重规划服务：
           - redispatch → ReplanService.redispatch()
           - reroute → ReplanService.reroute()
        3. 更新 exception_event.replan_batch_code
        4. 返回新调度方案编码
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
                message=f"异常事件已解决，无法触发重规划: {event_code}",
            )

        # 延迟导入避免循环依赖
        from services.replan_service import ReplanService

        try:
            if event.recommended_action == "redispatch":
                if not event.related_schedule_code:
                    return error_response(
                        code=40001,
                        message="重调度需要关联调度方案(related_schedule_code)",
                    )
                result = await ReplanService.redispatch(
                    db=db,
                    original_schedule_code=event.related_schedule_code,
                    replan_reason=replan_reason,
                )

            elif event.recommended_action == "reroute":
                # 通过 related_route_id（FK）查找关联路线编码
                if event.related_route_id:
                    route = db.query(Route).filter(
                        Route.id == event.related_route_id
                    ).first()
                    if not route:
                        return error_response(
                            code=40001,
                            message="重路径规划需要关联路线",
                        )
                    result = await ReplanService.reroute(
                        db=db,
                        original_route_code=route.route_code,
                        replan_reason=replan_reason,
                    )
                else:
                    return error_response(
                        code=40001,
                        message="重路径规划需要关联路线",
                    )
            else:
                return error_response(
                    code=40001,
                    message=f"不支持的重规划类型: {event.recommended_action}",
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

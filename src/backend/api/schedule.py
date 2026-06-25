"""
调度管理 API 路由

提供全局调度的触发、查询功能：
- POST /api/schedule/global：触发全局调度（F007 + F021）
- GET /api/schedule/global：历史方案列表
- GET /api/schedule/global/{schedule_code}：方案详情

提供节点调度的触发、查询功能（阶段4新增）：
- POST /api/schedule/node-dispatch：触发节点调度（F005）
- GET /api/schedule/batches：调度批次列表
- GET /api/schedule/batches/{code}：调度批次详情
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from pydantic import BaseModel, Field

from services.schedule_service import ScheduleService
from services.dispatch_service import DispatchService
from services.log_service import LogService, build_global_schedule_event_data
from schemas.dispatch import NodeDispatchRequest, DispatchBatchListResponse, DispatchBatchResponse
from config.database import get_db
from api.dependencies import get_current_user, require_dispatcher
from models.user import User

router = APIRouter(prefix="/api/schedule", tags=["调度管理"])


class GlobalScheduleRequest(BaseModel):
    """全局调度请求体"""
    order_codes: Optional[List[str]] = Field(
        default=None,
        description="订单编号列表，不传则处理所有 status=pending 的订单",
    )
    algorithm: str = Field(
        ...,
        description="算法类型：traditional / deepseek",
    )
    preview: bool = Field(
        default=True,
        description="预览模式：true=生成 draft 不落库（默认）；P1-2 已移除直接落库功能",
    )


@router.post("/global")
async def create_global_schedule(
    body: GlobalScheduleRequest,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    触发全局调度（F007 + F021）
    
    需要角色：dispatcher
    
    流程：
    1. F007 全局调度算法：为每票货物规划 L0 → L1 → L2 路径
    2. F021 打包算法：生成 L0→L1 和 L1→L2 包裹
    3. 单事务写入数据库并更新订单/货物状态
    """
    result = await ScheduleService.create_global_schedule(
        order_codes=body.order_codes,
        algorithm=body.algorithm,
        db=db,
        preview=body.preview,
    )
    
    # 记录埋点
    if result.get("code") == 0:  # 成功
        LogService.log_event(
            event_name="global_schedule",
            user_id=current_user.id,
            role=current_user.role,
            event_data=build_global_schedule_event_data(
                schedule_code=result["data"]["schedule_code"],
                order_count=len(result["data"].get("order_codes", [])),
                algorithm_type=body.algorithm
            ),
            db=db
        )
    
    return result


@router.get("/global")
async def list_global_schedules(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    order_code: Optional[str] = Query(default=None, description="按订单编号筛选"),
    status: Optional[str] = Query(default=None, description="按状态筛选（active/draft，默认过滤 draft）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取历史全局调度方案列表

    需要角色：dispatcher / manager
    """
    return await ScheduleService.get_global_schedules(
        page=page,
        page_size=page_size,
        order_code=order_code,
        status=status,
        db=db,
    )


@router.get("/global/{schedule_code}")
async def get_global_schedule(
    schedule_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取全局调度方案详情（含 goods_schedules 和 packages）

    需要角色：dispatcher / manager
    """
    return await ScheduleService.get_global_schedule(
        schedule_code=schedule_code,
        db=db,
    )


@router.post("/node-dispatch")
async def create_node_dispatch(
    body: NodeDispatchRequest,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    触发节点调度（F005）
    
    需要角色：dispatcher
    
    流程：
    1. F005 节点调度算法：分配车辆与司机（L0→L1 和 L1→L2）
    2. 单事务写入数据库并更新包裹/货物/车辆/司机状态
    """
    result = await DispatchService.create_node_dispatch(
        schedule_code=body.schedule_code,
        demo_mode=body.demo_mode,
        db=db,
    )
    
    # 记录埋点
    if result.get("code") == 0:  # 成功
        from services.log_service import build_node_dispatch_event_data
        LogService.log_event(
            event_name="node_dispatch",
            user_id=current_user.id,
            role=current_user.role,
            event_data=build_node_dispatch_event_data(
                batch_code=result["data"]["batch_code"],
                package_count=result["data"].get("package_count", 0),
                vehicle_count=result["data"].get("vehicle_count", 0),
                algorithm_type="traditional"
            ),
            db=db
        )
    
    return result


@router.get("/batches")
async def list_dispatch_batches(
    schedule_code: Optional[str] = Query(default=None, description="按调度方案筛选"),
    status: Optional[str] = Query(default=None, description="按状态筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取调度批次列表
    
    需要角色：dispatcher / manager
    """
    return await DispatchService.get_dispatch_batches(
        schedule_code=schedule_code,
        status=status,
        db=db,
    )


@router.get("/batches/{batch_code}")
async def get_dispatch_batch_detail(
    batch_code: str,
    vehicle_code: Optional[str] = Query(default=None, description="按车辆编码过滤"),
    level_phase: Optional[int] = Query(default=None, description="按层级阶段过滤（0=L0→L1，1=L1→L2）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取调度批次详情（含 dispatches，P1-07 新增过滤参数）
    
    需要角色：dispatcher / manager
    """
    return await DispatchService.get_dispatch_batch_detail(
        batch_code=batch_code,
        db=db,
        vehicle_code=vehicle_code,
        level_phase=level_phase,
    )

@router.get("/batches/{batch_code}/dispatches")
async def get_batch_dispatches(
    batch_code: str,
    vehicle_code: Optional[str] = Query(default=None, description="按车辆编码过滤"),
    level_phase: Optional[int] = Query(default=None, description="按层级阶段过滤（0=L0→L1，1=L1→L2）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按批次查询调度明细列表（P1-07 新增端点）
    
    需要角色：dispatcher / manager
    """
    return await DispatchService.get_batch_dispatches(
        batch_code=batch_code,
        db=db,
        vehicle_code=vehicle_code,
        level_phase=level_phase,
    )

@router.get("/{schedule_code}/dispatches")
async def get_schedule_dispatches(
    schedule_code: str,
    vehicle_code: Optional[str] = Query(default=None, description="按车辆编码过滤"),
    level_phase: Optional[int] = Query(default=None, description="按层级阶段过滤（0=L0→L1，1=L1→L2）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按方案查询所有调度明细列表（P1-07 新增端点）
    
    查询指定方案下所有批次的调度明细。
    
    需要角色：dispatcher / manager
    """
    return await DispatchService.get_schedule_dispatches(
        schedule_code=schedule_code,
        db=db,
        vehicle_code=vehicle_code,
        level_phase=level_phase,
    )

@router.get("/dispatches/{dispatch_code}")
async def get_dispatch_detail(
    dispatch_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查询单个调度明细详情（P1-07 新增端点）
    
    需要角色：dispatcher / manager
    """
    return await DispatchService.get_dispatch_detail(
        dispatch_code=dispatch_code,
        db=db,
    )


@router.post("/confirm/{schedule_code}")
async def confirm_schedule(
    schedule_code: str,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    确认 draft 调度方案（执行 F021 + 状态更新）
    
    需要角色：dispatcher
    """
    return await ScheduleService.confirm_schedule(
        schedule_code=schedule_code,
        db=db,
    )


@router.delete("/draft/{schedule_code}")
async def discard_draft(
    schedule_code: str,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db),
):
    """
    丢弃 draft 调度方案
    
    需要角色：dispatcher
    """
    return await ScheduleService.discard_draft(
        schedule_code=schedule_code,
        db=db,
    )


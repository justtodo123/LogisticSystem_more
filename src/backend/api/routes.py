"""
路径规划 API 路由
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from pydantic import BaseModel, Field

from schemas.route import (  # noqa: F401
    RoutePlanRequest, RouteListResponse, RouteDetailResponse, RouteCoordinatesResponse
)
from services.route_service import RouteService
from services.log_service import LogService, build_route_plan_event_data
from config.database import get_db
from api.dependencies import get_current_user, require_dispatcher
from models.user import User


router = APIRouter(prefix="/api/routes", tags=["路径规划"])


@router.post("/plan", summary="手动触发路径规划")
async def plan_routes(
    request: RoutePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dispatcher),
):
    """
    手动触发路径规划（F006）
    
    为指定批次下的节点调度明细规划路径。
    """
    result = await RouteService.create_route_planning(
        batch_code=request.batch_code,
        dispatch_codes=request.dispatch_codes,
        db=db
    )
    
    # 记录埋点
    if result.get("code") == 0:  # 成功
        LogService.log_event(
            event_name="route_plan",
            user_id=current_user.id,
            role=current_user.role,
            event_data=build_route_plan_event_data(
                route_count=len(result["data"].get("routes", [])),
                vehicle_count=len(set([r.get("vehicle_code") for r in result["data"].get("routes", [])]))
            ),
            db=db
        )
    
    return result


@router.get("", summary="查询路线列表")
async def get_routes(
    batch_code: Optional[str] = Query(None, description="批次编码"),
    vehicle_code: Optional[str] = Query(None, description="车辆编码"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询路线列表
    
    可按批次编码、车辆编码筛选。
    """
    result = await RouteService.get_routes(
        batch_code=batch_code,
        vehicle_code=vehicle_code,
        page=page,
        page_size=page_size,
        db=db
    )
    return result


@router.get("/{route_code}", summary="查询路线详情")
async def get_route_detail(
    route_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询路线详情
    
    返回路线的完整信息，包括路径路段。
    """
    result = await RouteService.get_route_detail(
        route_code=route_code,
        db=db
    )
    return result


@router.get("/by-vehicle/{vehicle_code}/coordinates", summary="查询车辆路线坐标")
async def get_route_coordinates(
    vehicle_code: str,
    batch_code: Optional[str] = Query(None, description="批次编码"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询车辆路线坐标（供前端可视化）
    
    返回指定车辆的路线坐标数据，供前端SVG/Canvas绘制路线图。
    """
    result = await RouteService.get_route_coordinates(
        vehicle_code=vehicle_code,
        batch_code=batch_code,
        db=db
    )
    return result

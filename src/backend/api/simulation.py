"""
模拟送达 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from pydantic import BaseModel, Field

from schemas.simulation import DeliverRequest, DeliverResponse
from services.simulation_service import SimulationService
from config.database import get_db
from api.dependencies import require_permission_with_optional_idempotency
from models.user import User

router = APIRouter(prefix="/api/simulation", tags=["模拟送达"])


@router.post("/deliver", summary="模拟送达")
async def deliver_packages(
    request: DeliverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_with_optional_idempotency("simulation:write")),
):
    """
    模拟送达，驱动状态流转
    
    支持单个/批量送达：
    - 无参数：处理所有 in_transit 包裹
    - 仅 vehicle_code：处理该车辆所有 in_transit 包裹
    - 仅 package_code：处理指定包裹（必须 in_transit 状态）
    - 都传：处理指定车辆的指定包裹（必须 in_transit 状态）
    """
    result = await SimulationService.deliver_packages(
        vehicle_code=request.vehicle_code,
        package_code=request.package_code,
        db=db
    )
    return result

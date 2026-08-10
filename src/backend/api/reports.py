"""
报表分析 API（T5-3）

- GET /api/reports/sla?date_from&date_to — SLA 达成率（准点率、平均延迟）
- GET /api/reports/cost — 成本分析（按节点/线路汇总）
- GET /api/reports/exceptions — 异常统计
- GET /api/reports/capacity — 运力效率
- GET /api/reports/overview?date_from&date_to — 四类汇总（供 Dashboard）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from config.database import get_db
from models.user import User
from services.report_service import (
    get_sla_report,
    get_cost_report,
    get_exception_report,
    get_capacity_report,
    get_overview,
)

router = APIRouter(prefix="/api/reports", tags=["报表分析"])


@router.get("/sla", summary="SLA 达成率")
async def sla_report(
    date_from: Optional[str] = Query(None, description="起始日期（ISO，如 2026-06-15）"),
    date_to: Optional[str] = Query(None, description="截止日期（ISO）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SLA 达成率：准点率、平均延迟、订单分布"""
    return get_sla_report(date_from, date_to, db)


@router.get("/cost", summary="成本分析")
async def cost_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """成本分析：按车辆（线路）/ 节点汇总"""
    return get_cost_report(db)


@router.get("/exceptions", summary="异常统计")
async def exception_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """异常统计：类型 / 子类型分布"""
    return get_exception_report(db)


@router.get("/capacity", summary="运力效率")
async def capacity_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """运力效率：车辆状态、调度、包裹流转"""
    return get_capacity_report(db)


@router.get("/overview", summary="报表汇总（Dashboard）")
async def report_overview(
    date_from: Optional[str] = Query(None, description="起始日期（ISO）"),
    date_to: Optional[str] = Query(None, description="截止日期（ISO）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """四类报表数据汇总，一次拉取供看板展示"""
    return get_overview(date_from, date_to, db)

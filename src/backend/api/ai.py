"""
AI 助手路由模块

功能：
1. POST /api/ai/parse - 自然语言解析 + 自动执行调度（P0，F014）
2. POST /api/ai/explain - 方案解释（P1，F015，占位 501）
3. POST /api/ai/review - 方案审查（P1，F016，占位 501）
4. POST /api/ai/analyze-exception - 异常分析（P1，F017，占位 501）
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from config.database import get_db
from schemas.ai import AiParseRequest, AiParseResponse
from services.deepseek_service import DeepSeekService
from services.log_service import LogService, build_deepseek_call_event_data
from api.dependencies import get_current_user
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


@router.post("/parse", response_model=Dict[str, Any])
async def parse_natural_language(
    request: AiParseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    自然语言解析 → 调度执行（F014）
    
    流程：
    1. 获取系统上下文（订单数、车辆数、节点数）
    2. 调用 DeepSeek API 解析自然语言
    3. 如果 DeepSeek 失败，降级使用默认参数
    4. 如果 auto_execute=true，自动执行完整调度链路
    5. 记录埋点（deepseek_call 事件）
    6. 返回结果
    """
    try:
        # 1. 获取系统上下文
        from services.order_service import OrderService
        from services.vehicle_service import VehicleService
        from services.node_service import NodeService
        
        pending_orders = await OrderService.get_orders_by_status(status="pending", db=db)
        available_vehicles = await VehicleService.get_available_vehicles(db=db)
        nodes = await NodeService.get_all_nodes(db=db)
        
        system_context = {
            "order_count": len(pending_orders),
            "vehicle_count": len(available_vehicles),
            "node_count": len(nodes),
            "pending_orders": pending_orders
        }
        
        # 2. 调用 DeepSeek API
        deepseek_result = await DeepSeekService.parse_natural_language(
            user_message=request.message,
            system_context=system_context
        )
        
        algorithm_params = deepseek_result["algorithm_params"]
        degraded = not deepseek_result["success"]
        degraded_reason = deepseek_result.get("error")
        
        # 3. 记录埋点
        LogService.log_event(
            event_name="deepseek_call",
            user_id=current_user.id,
            role=current_user.role,
            event_data=build_deepseek_call_event_data(
                function_name="parse",
                success=deepseek_result["success"],
                degraded=degraded
            ),
            db=db
        )
        
        # 4. 如果 auto_execute=true，执行完整调度链路
        schedule_code = None
        if request.auto_execute:
            # 4.1 执行 F007 全局调度
            from services.schedule_service import ScheduleService
            
            schedule_result = await ScheduleService.create_global_schedule(
                db=db,
                current_user_id=current_user.id,
                current_user_role=current_user.role
            )
            schedule_code = schedule_result["schedule_code"]
            
            # 4.2 执行 F021 打包服务（由 ScheduleService 内部调用）
            # 已经在 create_global_schedule 中自动执行
            
            # 4.3 执行 F005 节点间调度（demo_mode=true，连续执行 L0→L1 和 L1→L2）
            from services.dispatch_service import DispatchService
            
            batch_result = await DispatchService.create_node_dispatch(
                db=db,
                schedule_code=schedule_code,
                demo_mode=True,  # 关键：跳过模拟送达，连续执行两次
                current_user_id=current_user.id,
                current_user_role=current_user.role
            )
            batch_code = batch_result["batch_code"]
            
            # 4.4 执行 F006 路径规划
            from services.route_service import RouteService
            
            await RouteService.create_routes(
                db=db,
                batch_code=batch_code,
                current_user_id=current_user.id,
                current_user_role=current_user.role
            )
        
        # 5. 返回结果
        return {
            "code": 0,
            "message": "success",
            "data": {
                "schedule_code": schedule_code,
                "algorithm_params": algorithm_params
            },
            "meta": {
                "degraded": degraded,
                "degraded_reason": degraded_reason
            }
        }
        
    except Exception as e:
        logger.error(f"AI 解析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def explain_schedule(
    current_user: User = Depends(get_current_user)
):
    """
    方案解释（F015，P1，返回 501）
    
    未来实现：
    1. 获取当前调度方案数据
    2. 调用 DeepSeek API 生成解释
    3. 返回自然语言解释
    """
    return {
        "code": 50100,
        "message": "F015 方案解释功能正在开发中（P1）",
        "data": None,
        "meta": {
            "degraded": False,
            "degraded_reason": None
        }
    }


@router.post("/review")
async def review_schedule(
    current_user: User = Depends(get_current_user)
):
    """
    方案审查（F016，P1，返回 501）
    """
    return {
        "code": 50100,
        "message": "F016 方案审查功能正在开发中（P1）",
        "data": None,
        "meta": {
            "degraded": False,
            "degraded_reason": None
        }
    }


@router.post("/analyze-exception")
async def analyze_exception(
    current_user: User = Depends(get_current_user)
):
    """
    异常分析（F017，P1，返回 501）
    """
    return {
        "code": 50100,
        "message": "F017 异常分析功能正在开发中（P1）",
        "data": None,
        "meta": {
            "degraded": False,
            "degraded_reason": None
        }
    }

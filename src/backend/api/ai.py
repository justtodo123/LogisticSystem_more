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
from typing import Dict, Any, List, Optional

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
    自然语言解析 → 生成 draft 方案（F014）

    三步模型：
    1. 确定参数来源 → AI解析 / 手动权重 / 混合 / 默认
    2. 确定执行目标 → schedule_codes 非空=重规划 / 空=新建
    3. 生成 draft 方案 → F007（仅预览，不执行 F021/F005/F006）
       （execute="dry-run" 时跳过步骤3，仅返回解析参数）
    """
    try:
        has_message = bool(request.message and request.message.strip())
        has_weights = bool(request.weights)

        # ── 步骤1：确定算法参数 ──
        algorithm_params, mode, degraded, degraded_reason = await _resolve_params(
            db=db, user_id=current_user.id, role=current_user.role,
            message=request.message if has_message else None,
            weights=request.weights,
            schedule_codes=request.schedule_codes,
        )

        # ── 步骤2：查询参考方案（供 prompt 和响应复用） ──
        reference_codes = None
        if request.schedule_codes:
            reference_codes = request.schedule_codes

        # ── 步骤3：执行 ──
        if request.execute == "dry-run":
            # dry-run 模式：仅返回解析出的参数，不落库
            return {
                "code": 0, "message": "success (dry-run)",
                "data": {
                    "algorithm_params": algorithm_params,
                    "mode": mode,
                },
                "meta": {"degraded": degraded, "degraded_reason": degraded_reason},
            }

        is_replan = bool(request.schedule_codes)
        if is_replan:
            # 重规划模式：对第一个指定方案生成 draft 版本化重规划
            # （AI 接口只生成一个 draft 方案，无论 schedule_codes 传入几个）
            target_code = request.schedule_codes[0]
            replan_reason = f"AI驱动重规划: {request.message}" if has_message else "手动权重重规划"
            result = await _execute_replan(
                db=db, original_code=target_code,
                replan_reason=replan_reason,
                algorithm_params=algorithm_params,
            )
            if result["code"] != 0:
                return result
            new_code = result["data"]["schedule_code"]

            return {
                "code": 0, "message": "success",
                "data": {
                    "schedule_code": new_code,
                    "algorithm_params": algorithm_params,
                    "mode": mode,
                    "is_replan": True,
                    "status": "draft",
                    "reference_codes": reference_codes,
                },
                "meta": {"degraded": degraded, "degraded_reason": degraded_reason},
            }
        else:
            # 新建模式：对全部 pending 订单创建 draft 方案
            schedule_code = await _execute_new_schedule(
                db=db, algorithm_params=algorithm_params,
            )
            return {
                "code": 0, "message": "success",
                "data": {
                    "schedule_code": schedule_code,
                    "algorithm_params": algorithm_params,
                    "mode": mode,
                    "is_replan": False,
                    "status": "draft",
                    "reference_codes": reference_codes,
                },
                "meta": {"degraded": degraded, "degraded_reason": degraded_reason},
            }

    except Exception as e:
        logger.error(f"AI 解析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════
# 辅助函数 — 三步模型
# ════════════════════════════════════════════════════════════


async def _resolve_params(
    db: Session,
    user_id: int,
    role: str,
    message: Optional[str],
    weights: Optional[Dict[str, Any]],
    schedule_codes: Optional[List[str]],
) -> tuple:
    """
    步骤1：确定算法参数 + 模式
    
    Returns:
        (algorithm_params, mode, degraded, degraded_reason)
    """
    degraded = False
    degraded_reason = None

    if message and not weights:
        # ai 模式：纯 DeepSeek 解析
        mode = "ai"
        system_context = await _build_context(db, schedule_codes)
        ds_result = await DeepSeekService.parse_natural_language(message, system_context)
        algorithm_params = ds_result["algorithm_params"]
        degraded = not ds_result["success"]
        degraded_reason = ds_result.get("error")
        _log_deepseek(user_id, role, ds_result["success"], degraded, db)

    elif not message and weights:
        # manual 模式：纯手动权重
        mode = "manual"
        algorithm_params = weights

    elif message and weights:
        # hybrid 模式：DeepSeek + 权重覆盖
        mode = "hybrid"
        system_context = await _build_context(db, schedule_codes)
        ds_result = await DeepSeekService.parse_natural_language(message, system_context)
        algorithm_params = _merge_weights(ds_result["algorithm_params"], weights)
        degraded = not ds_result["success"]
        degraded_reason = ds_result.get("error")
        _log_deepseek(user_id, role, ds_result["success"], degraded, db)

    else:
        # default 模式：无 message 无 weights → 默认参数
        mode = "default"
        algorithm_params = DeepSeekService._load_default_params()

    # 输出标准化：无论哪种模式，只保留 global_schedule
    # （DeepSeek 提示词已裁剪为只返回 global_schedule，
    #   此处兜底处理手动模式可能传入的多模块 weights）
    raw = algorithm_params
    algorithm_params = {"global_schedule": raw.get("global_schedule", {})}

    return algorithm_params, mode, degraded, degraded_reason


async def _build_context(
    db: Session,
    schedule_codes: Optional[List[str]],
) -> Dict[str, Any]:
    """构建 DeepSeek 系统上下文（含历史方案指标）"""
    from services.order_service import OrderService
    from services.vehicle_service import VehicleService
    from services.node_service import NodeService

    orders_result = await OrderService.get_orders(page=1, page_size=1000, status="pending", db=db)
    vehicles_result = await VehicleService.get_vehicles(page=1, page_size=1000, status="idle", db=db)
    nodes_result = await NodeService.get_nodes(page=1, page_size=1000, db=db)

    ctx = {
        "order_count": len(orders_result["data"]["items"]),
        "vehicle_count": len(vehicles_result["data"]["items"]),
        "node_count": len(nodes_result["data"]["items"]),
        "pending_orders": orders_result["data"]["items"],
    }

    if schedule_codes:
        from models.global_schedule import GlobalSchedule
        schedules = db.query(GlobalSchedule).filter(
            GlobalSchedule.schedule_code.in_(schedule_codes)
        ).all()
        if schedules:
            ctx["reference_schedules"] = [
                {
                    "schedule_code": s.schedule_code,
                    "total_distance": float(s.total_distance),
                    "total_time": float(s.total_time),
                    "total_goods": s.total_goods,
                    "score": float(s.score),
                    "version": s.version,
                    "is_replan": s.is_replan,
                    "replan_reason": s.replan_reason,
                }
                for s in schedules
            ]
            # 重规划时首个方案作为参考重点
            first = schedules[0]
            ctx["target_schedule"] = {
                "schedule_code": first.schedule_code,
                "total_distance": float(first.total_distance),
                "total_time": float(first.total_time),
                "total_goods": first.total_goods,
                "score": float(first.score),
                "algorithm_type": first.algorithm_type,
            }

    return ctx


def _merge_weights(ds_params: Dict[str, Any], weights: Dict[str, Any]) -> Dict[str, Any]:
    """DeepSeek 参数 + 手动权重合并（weights 优先级更高）"""
    merged = {**ds_params}
    for section in weights:
        if section in merged and isinstance(merged[section], dict) and isinstance(weights[section], dict):
            merged[section] = {**merged[section], **weights[section]}
        else:
            merged[section] = weights[section]
    return merged


def _log_deepseek(user_id: int, role: str, success: bool, degraded: bool, db: Session):
    """记录 DeepSeek 调用埋点"""
    LogService.log_event(
        event_name="deepseek_call",
        user_id=user_id, role=role,
        event_data=build_deepseek_call_event_data(
            function_name="parse", success=success, degraded=degraded,
        ),
        db=db,
    )


async def _execute_new_schedule(db: Session, algorithm_params: Dict[str, Any]) -> str:
    """步骤3-new：创建 draft 调度方案（仅 F007，不执行 F021/F005/F006）"""
    from services.schedule_service import ScheduleService

    result = await ScheduleService.create_global_schedule(
        order_codes=None,
        algorithm=algorithm_params.get("global_schedule", {}).get("algorithm", "traditional"),
        db=db,
        custom_weights=algorithm_params,
        # preview=True 为默认值（P1-2），仅生成 draft，不打包
    )
    if result["code"] != 0:
        raise RuntimeError(f"全局调度失败: {result['message']}")
    return result["data"]["schedule_code"]


async def _execute_replan(
    db: Session,
    original_code: str,
    replan_reason: str,
    algorithm_params: Dict[str, Any],
) -> Dict[str, Any]:
    """步骤3-replan：对指定方案生成 draft 版本化重规划（仅 F007，不执行 F021/F005/F006）"""
    from services.replan_service import ReplanService
    return await ReplanService.redispatch(
        db=db,
        original_schedule_code=original_code,
        replan_reason=replan_reason,
        custom_weights=algorithm_params,
        draft_only=True,
    )


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

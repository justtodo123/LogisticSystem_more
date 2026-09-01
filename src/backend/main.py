from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import json
import logging
from api.auth import router as auth_router
from api.orders import router as orders_router
from api.goods import router as goods_router
from api.packages import router as packages_router
from api.vehicles import router as vehicles_router
from api.drivers import router as drivers_router
from api.nodes import router as nodes_router
from api.schedule import router as schedule_router
from api.routes import router as routes_router
from api.simulation import router as simulation_router
from api.exception_events import router as exceptions_router
from api.ai import router as ai_router
from api.arrival_confirm import router as arrival_confirm_router
from api.audit_logs import router as audit_logs_router
from api.schedule_override import router as schedule_override_router
from api.notifications import router as notifications_router
from api.export import router as export_router
from api.erp_webhook import router as erp_webhook_router
from api.reports import router as reports_router
from api.ai_confirmation import router as ai_confirmation_router
from api.users import router as users_router
from config.redis import get_redis_client, is_redis_enabled
from config.settings import settings
from core.error_codes import (
    CODE_DATABASE_ERROR,
    CODE_INTERNAL_ERROR,
    CODE_PARAM_ERROR,
    get_error_definition,
)
from core.errors import DomainError
from core.exception_mapping import (
    request_log_context,
    resolve_legacy_http_error,
    safe_response_headers,
    validation_error_meta,
)
from middleware.idempotency import (
    IdempotencyMiddleware,
    IdempotencyProtocolError,
    IdempotencyReplay,
)
from middleware.timeout import TimeoutMiddleware
from middleware.audit_log import AuditLogMiddleware
from utils.response import error_response

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    code: int = 0
    message: str = "success"
    data: dict = {"status": "ok"}
    meta: dict = {"degraded": False, "degraded_reason": None}


# 创建FastAPI应用实例
app = FastAPI(
    title="智能物流平台",
    description="DeepSeek路径优化 - 智能物流平台后端API",
    version="0.1.0"
)

# 配置CORS中间件
cors_origins_str = settings.CORS_ORIGINS
# 支持逗号分隔的多个源，或JSON数组格式
if cors_origins_str.startswith("[") and cors_origins_str.endswith("]"):
    cors_origins = json.loads(cors_origins_str)
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册幂等控制中间件（T0-4 新增）
app.add_middleware(
    IdempotencyMiddleware,
    ttl_hours=settings.IDEMPOTENCY_TTL_HOURS,
)

# 注册全局超时中间件（T0-5 新增）
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
)

# 注册审计日志中间件（T0-3 新增）— 放在最后，限流后的请求才记录
app.add_middleware(AuditLogMiddleware)

# 注册认证路由
app.include_router(auth_router)
app.include_router(users_router)

# 注册基础数据管理路由
app.include_router(orders_router)
app.include_router(goods_router)
app.include_router(packages_router)
app.include_router(vehicles_router)
app.include_router(drivers_router)
app.include_router(nodes_router)
app.include_router(schedule_router)

# 注册路径规划路由
app.include_router(routes_router)
app.include_router(simulation_router)

# 注册异常管理路由
app.include_router(exceptions_router)

# 注册 AI 助手路由
app.include_router(ai_router)

# 注册到货确认路由
app.include_router(arrival_confirm_router)
app.include_router(audit_logs_router)

# 注册人工干预调度路由（T2-4）
app.include_router(schedule_override_router)

# 注册消息通知路由（T3-2）
app.include_router(notifications_router)

# 注册数据导出路由（T5-1）
app.include_router(export_router)

# 注册 ERP 对接路由（T5-1）
app.include_router(erp_webhook_router)

# 注册报表分析路由（T5-3）
app.include_router(reports_router)

# 注册 AI 建议确认闸门路由（T6-2）
app.include_router(ai_confirmation_router)


# ─── 全局异常处理器 ───────────────────────────────────────────────
# 所有 HTTPException（包括 dependencies.py 抛出、FastAPI 内置校验、HTTPBearer 等）
# 统一转为 {code, message, data, meta} 格式

@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    """渲染登记过的领域错误。"""
    if exc.cause is not None:
        logger.error(
            "领域操作失败: code=%s exception=%s context=%s",
            exc.code,
            type(exc.cause).__name__,
            request_log_context(request),
        )
    headers = {}
    retry_after = exc.meta.get("retry_after") if isinstance(exc.meta, dict) else None
    if isinstance(retry_after, (int, float)) and retry_after >= 0:
        headers["Retry-After"] = str(int(retry_after))
    return JSONResponse(
        status_code=exc.http_status,
        content=error_response(exc.code, exc.public_message, meta=exc.meta),
        headers=headers or None,
    )


@app.exception_handler(IdempotencyReplay)
async def idempotency_replay_handler(
    request: Request,
    exc: IdempotencyReplay,
):
    """Return a stored response only after route authorization succeeds."""
    return IdempotencyMiddleware.replay_response(exc.response)


@app.exception_handler(IdempotencyProtocolError)
async def idempotency_protocol_error_handler(
    request: Request,
    exc: IdempotencyProtocolError,
):
    """Render errors raised by the post-authorization claim protocol."""
    return IdempotencyMiddleware.protocol_error_response(
        exc.code,
        headers=exc.headers,
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常只对外返回安全文案。"""
    definition = get_error_definition(CODE_DATABASE_ERROR)
    logger.exception(
        "数据库请求失败: exception=%s context=%s",
        type(exc).__name__,
        request_log_context(request),
    )
    return JSONResponse(
        status_code=definition.http_status,
        content=error_response(definition.code, definition.message),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """未处理异常不向客户端泄露内部细节。"""
    definition = get_error_definition(CODE_INTERNAL_ERROR)
    logger.exception(
        "未处理请求异常: exception=%s context=%s",
        type(exc).__name__,
        request_log_context(request),
    )
    return JSONResponse(
        status_code=definition.http_status,
        content=error_response(definition.code, definition.message),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """将旧 HTTPException 安全转换为统一错误 envelope。"""
    definition, message, meta = resolve_legacy_http_error(exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(definition.code, message, meta=meta),
        headers=safe_response_headers(exc.headers),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将 Pydantic 参数校验错误转为统一、安全的响应格式。"""
    definition = get_error_definition(CODE_PARAM_ERROR)
    return JSONResponse(
        status_code=422,
        content=error_response(
            definition.code,
            definition.message,
            meta=validation_error_meta(exc.errors()),
        ),
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口（含 AI / Redis 状态）"""
    ai_status = "available" if settings.DEEPSEEK_API_KEY else "degraded"
    data = {
        "status": "ok",
        "environment": settings.ENV,
        "ai_service": ai_status,
    }
    if is_redis_enabled():
        try:
            await get_redis_client().ping()
            data["redis"] = "available"
        except Exception:
            data["redis"] = "degraded"
    return HealthResponse(data=data)


# 应用启动时初始化数据库（创建所有表）
@app.on_event("startup")
async def startup_event():
    """应用启动事件；schema 由发布前的 Alembic 步骤负责。"""
    from config.database_url import redact_database_url

    logger.info(
        "启动环境：ENV=%s，数据库=%s（schema 需由发布前 Alembic 管理）",
        settings.ENV,
        redact_database_url(settings.DATABASE_URL),
    )


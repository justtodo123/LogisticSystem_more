from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import os
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
from utils.response import error_response


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
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
# 支持逗号分隔的多个源，或JSON数组格式
if cors_origins_str.startswith("[") and cors_origins_str.endswith("]"):
    import json
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

# 注册认证路由
app.include_router(auth_router)

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


# ─── 全局异常处理器 ───────────────────────────────────────────────
# 所有 HTTPException（包括 dependencies.py 抛出、FastAPI 内置校验、HTTPBearer 等）
# 统一转为 {code, message, data, meta} 格式

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """将 HTTPException 转为统一响应格式"""
    status_code = exc.status_code
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    if status_code == 401:
        # 根据 detail 区分 Token 过期 vs 无效/未登录
        if "过期" in detail or "expired" in detail.lower():
            code = 40101
            message = "Token 已过期，请重新登录"
        else:
            code = 40100
            message = "未登录或 Token 无效"
    elif status_code == 403:
        code = 40300
        message = detail
    elif status_code == 404:
        code = 40400
        message = "资源不存在"
    elif status_code == 422:
        code = 40000
        message = "参数校验失败"
        return JSONResponse(
            status_code=status_code,
            content=error_response(code, message, {"detail": detail}),
        )
    elif status_code == 500:
        code = 50000
        message = "服务器内部错误"
    else:
        code = status_code * 100
        message = detail

    return JSONResponse(
        status_code=status_code,
        content=error_response(code, message),
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return HealthResponse()


# 应用启动时初始化数据库（创建所有表）
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    from config.database import init_db
    init_db()


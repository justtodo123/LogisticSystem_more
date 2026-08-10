"""
审计日志中间件

拦截所有 POST/PUT/PATCH/DELETE 请求，自动记录操作到 log_events 表。
异步写入不阻塞请求响应。
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from services.log_service import LogService, VALID_EVENTS

logger = logging.getLogger(__name__)

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
EXCLUDED_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc", "/api/auth/login", "/api/auth/logout"}


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件

    拦截写操作，从请求中提取用户信息和元数据，写入审计日志。
    异步执行不阻塞正常响应流。
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 先执行正常请求
        response = await call_next(request)

        # 仅记录写操作（排除登录登出/健康检查等）
        if request.method.upper() not in WRITE_METHODS:
            return response

        if request.url.path in EXCLUDED_PATHS:
            return response

        # 从 request.state 中获取当前用户（由 get_current_user 依赖注入）
        user = getattr(request.state, "current_user", None)
        if user is None:
            # 尝试从 PATCH/PUT 的依赖中推断（某些端点可能未设置 state）
            return response

        # 提取请求元数据
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:512]

        # 构建事件数据
        event_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        }

        # 根据路径推断事件类型
        event_name = self._infer_event_type(request.url.path, request.method)

        try:
            LogService.log_event(
                event_name=event_name,
                user_id=user.id,
                role=user.role,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"审计日志写入失败：{e}")

        return response

    @staticmethod
    def _infer_event_type(path: str, method: str) -> str:
        """根据请求路径和方法推断事件类型"""
        if "/schedule/global" in path:
            return "global_schedule"
        if "/schedule/node-dispatch" in path:
            return "node_dispatch"
        if "/routes" in path:
            return "route_plan"
        if "/exceptions" in path and "/replan" in path:
            return "replan"
        if "/exceptions" in path:
            return "exception_resolve"
        if "/orders" in path:
            return "orders"
        if "/vehicles" in path:
            return "vehicles"
        if "/drivers" in path:
            return "drivers"
        if "/nodes" in path:
            return "nodes"
        if "/ai" in path:
            return "deepseek_call"
        if "/simulation" in path:
            return "simulation"
        if "/arrival" in path:
            return "arrival_confirm"
        # 默认用路径首段
        parts = [p for p in path.strip("/").split("/") if p]
        return parts[0] if parts else "unknown"

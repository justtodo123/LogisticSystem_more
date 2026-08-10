"""
全局超时中间件

所有请求在超时时间后自动返回 504 Gateway Timeout，
防止长时间阻塞工作线程。
"""
import asyncio
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from config.settings import settings

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """全局请求超时中间件

    使用 asyncio.wait_for 包装请求处理，超时后返回 504。
    排除路径（如 health）不受超时限制。
    """

    EXCLUDED_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, timeout_seconds: int = 30):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 健康检查等路径不限制超时
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"请求超时 ({self.timeout_seconds}s): "
                f"{request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=504,
                content={
                    "code": 50400,
                    "message": f"请求超时（>{self.timeout_seconds}s），请重试或缩小查询范围",
                    "data": None,
                    "meta": {"degraded": False, "degraded_reason": None},
                },
            )

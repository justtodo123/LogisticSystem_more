"""
幂等键中间件

通过 X-Idempotency-Key 请求头实现写操作幂等：
- POST/PUT/PATCH 请求携带 X-Idempotency-Key 时，最多执行一次
- 重复请求在 TTL 内返回第一次的缓存响应（HTTP 200）
- TTL 过期后视为新请求

存储（T4-3）：从 SQLite 迁移到 Redis，Redis 不可用时降级到进程内内存缓存；
过期清理依赖缓存 TTL 自动完成，无需 DB 记录。
"""
import json
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from utils.idempotency_store import (
    get_idempotency_response,
    save_idempotency_response,
)

logger = logging.getLogger(__name__)

IDEMPOTENCY_HEADER = "X-Idempotency-Key"
WRITE_METHODS = {"POST", "PUT", "PATCH"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """幂等键中间件

    仅对 POST/PUT/PATCH 方法生效；GET/DELETE 直接放行。
    """

    def __init__(self, app, ttl_hours: int = 24):
        super().__init__(app)
        self.ttl_hours = ttl_hours

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 只拦截写请求
        if request.method.upper() not in WRITE_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return await call_next(request)

        try:
            # 1. 查询是否已存在该键的记录（Redis → 内存降级）
            existing = await get_idempotency_response(idempotency_key, self.ttl_hours)

            if existing is not None:
                logger.info("命中幂等缓存 key=%s...", idempotency_key[:20])
                return Response(
                    content=json.dumps(existing, ensure_ascii=False),
                    status_code=200,
                    media_type="application/json",
                )

            # 2. 正常执行请求
            response: Response = await call_next(request)

            # 3. 仅缓存成功响应（2xx）
            if 200 <= response.status_code < 300:
                response = await self._capture_and_cache(idempotency_key, response)

            return response

        except Exception:
            logger.exception("幂等中间件异常，放行请求")
            return await call_next(request)  # 幂等中间件异常不阻断正常流程

    @staticmethod
    async def _read_body(response: Response) -> bytes:
        """读取响应体（BaseHTTPMiddleware 返回 _StreamingResponse，需消费 body_iterator）"""
        if hasattr(response, "body_iterator"):
            chunks = [chunk async for chunk in response.body_iterator]
            return b"".join(chunks)
        body = response.body
        return body if isinstance(body, bytes) else str(body).encode("utf-8")

    async def _capture_and_cache(self, key: str, response: Response) -> Response:
        """读取响应体并缓存到缓存存储（Redis / 内存），返回带原始 body 的重建响应

        注意：读取 body_iterator 会消费响应流，必须重建 Response 以保留响应体。
        """
        body_bytes = await self._read_body(response)

        try:
            body_str = body_bytes.decode("utf-8", errors="replace")
            response_json = json.loads(body_str) if body_str else {}
        except Exception:
            response_json = {"_raw": body_bytes.decode("utf-8", errors="replace")}

        await save_idempotency_response(key, response_json, self.ttl_hours)
        logger.debug("已缓存幂等响应 key=%s..., TTL=%sh", key[:20], self.ttl_hours)

        headers = {
            k: v for k, v in response.headers.items() if k.lower() != "content-length"
        }
        return Response(
            content=body_bytes,
            status_code=response.status_code,
            media_type=response.media_type,
            headers=headers,
        )

"""
幂等键中间件

通过 X-Idempotency-Key 请求头实现写操作幂等：
- POST/PUT/PATCH 请求携带 X-Idempotency-Key 时，最多执行一次
- 重复请求在 TTL 内返回第一次的缓存响应（HTTP 200）
- TTL 过期后视为新请求（通过 expires_at 判断）
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from sqlalchemy.orm import Session

from config.database import SessionLocal
from models.idempotency_record import IdempotencyRecord

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

        db: Session = SessionLocal()
        try:
            # 1. 查询是否已存在该键的记录
            existing = (
                db.query(IdempotencyRecord)
                .filter(IdempotencyRecord.idempotency_key == idempotency_key)
                .first()
            )

            if existing:
                # 检查是否过期
                if existing.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                    logger.info(f"命中幂等缓存 key={idempotency_key[:20]}...")
                    response_data = existing.response_data or {}
                    return Response(
                        content=json.dumps(response_data, ensure_ascii=False),
                        status_code=200,
                        media_type="application/json",
                    )
                else:
                    # TTL 过期，删除旧记录
                    db.delete(existing)
                    db.commit()

            # 2. 正常执行请求
            response: Response = await call_next(request)

            # 3. 仅缓存成功响应（2xx）
            if 200 <= response.status_code < 300:
                self._cache_response(db, idempotency_key, response)

            return response

        except Exception:
            db.rollback()
            return await call_next(request)  # 幂等中间件异常不阻断正常流程
        finally:
            db.close()

    def _cache_response(self, db: Session, key: str, response: Response) -> None:
        """缓存成功响应到幂等记录表"""
        try:
            # 读取响应体（FastAPI Response.body 可能是 bytes / 协程）
            body = response.body
            if isinstance(body, bytes):
                body_str = body.decode("utf-8", errors="replace")
            else:
                body_str = str(body)

            response_json = json.loads(body_str) if body_str else {}
        except (json.JSONDecodeError, Exception):
            response_json = {"_raw": body_str}

        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours)

        record = IdempotencyRecord(
            idempotency_key=key,
            response_data=response_json,
            expires_at=expires_at,
        )
        db.add(record)
        db.commit()
        logger.debug(f"已缓存幂等响应 key={key[:20]}..., TTL={self.ttl_hours}h")


def cleanup_expired_idempotency_records(db: Optional[Session] = None) -> int:
    """清理过期的幂等记录（可由定时任务调用）"""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        now_utc = datetime.now(timezone.utc)
        expired = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.expires_at < now_utc
        )
        count = expired.count()
        expired.delete()
        db.commit()
        if count:
            logger.info(f"清理了 {count} 条过期幂等记录")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"清理过期幂等记录失败：{e}")
        raise
    finally:
        if close_db:
            db.close()

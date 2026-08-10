"""
幂等键存储（T4-3：从 SQLite 迁移到 Redis，dev 降级到内存缓存）

配合 middleware/idempotency.py 使用：
- 存：key → {response_data, expires_at}
- 取：命中且未过期返回 response_data，否则 None
- 清理：依赖缓存 TTL 自动过期，无需定时任务

存储位置：
- Redis 可用 → Redis（跨实例共享，生产推荐）
- Redis 不可用 → 进程内内存缓存（dev 降级，进程重启后失效）
"""
import logging
from datetime import datetime, timedelta, timezone

from utils.cache import cache_delete, cache_get, cache_set

logger = logging.getLogger(__name__)

IDEMPOTENCY_PREFIX = "idem"


def _store_key(idempotency_key: str) -> str:
    return f"{IDEMPOTENCY_PREFIX}:{idempotency_key}"


async def get_idempotency_response(key: str, ttl_hours: int = 24):
    """读取幂等键对应的响应数据；不存在或已过期返回 None"""
    data = await cache_get(_store_key(key))
    if data is None:
        return None
    # 二次校验 TTL（内存/Redis 本身按秒 TTL 过期，此处防御性校验）
    expires_at = data.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at)
            if exp.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
                await cache_delete(_store_key(key))
                return None
        except (ValueError, TypeError):
            pass
    return data.get("response_data")


async def save_idempotency_response(key: str, response_data: dict, ttl_hours: int = 24) -> None:
    """保存幂等键对应的响应数据"""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    payload = {
        "response_data": response_data,
        "expires_at": expires_at.isoformat(),
    }
    await cache_set(_store_key(key), payload, ttl=ttl_hours * 3600)


async def delete_idempotency_key(key: str) -> None:
    """删除指定幂等键（键已过期或被替换时调用）"""
    await cache_delete(_store_key(key))

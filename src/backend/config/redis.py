"""
Redis 连接配置（T4-3）

- REDIS_ENABLED=true 且 REDIS_URL 非空时启用 Redis
- 未启用、未配置或连接失败时，由 utils/cache 自动降级到进程内内存缓存（dev 友好）
"""
import logging
from typing import Optional

import redis.asyncio as aioredis

from config.settings import settings

logger = logging.getLogger(__name__)

_client: Optional[aioredis.Redis] = None


def is_redis_enabled() -> bool:
    """Redis 是否启用（ENV=dev 可通过 REDIS_ENABLED=false 显式关闭）"""
    return bool(settings.REDIS_ENABLED and settings.REDIS_URL)


def get_redis_client() -> aioredis.Redis:
    """获取 Redis 客户端（惰性单例）"""
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def reset_redis_client() -> None:
    """重置客户端（测试隔离用）"""
    global _client
    _client = None

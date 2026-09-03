"""
缓存工具（T4-3）：Redis 优先，不可用时降级到进程内内存缓存

- `@cached(ttl=300)` 装饰器：函数级缓存（支持 async / sync）
- `cache_get` / `cache_set` / `cache_delete` / `cache_delete_prefix`：底层读写接口
- Redis 失败后降级内存缓存；冷却后探测恢复，避免进程内永久卡在 degraded
- 缓存未命中使用 per-key single-flight，避免恢复瞬间无界回源

设计约定：
- 缓存值必须是 JSON 可序列化的 dict/list/标量（端点返回的 ResponseSchema dict 均满足）
- 同步函数装饰后仅使用内存缓存（Redis 客户端为 asyncio 实现，同步场景不接入）
"""
import asyncio
import functools
import inspect
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple

from config.redis import get_redis_client, is_redis_enabled, reset_redis_client
from config.settings import settings
from core.dependency import observe_dependency
from core.metrics import observe_cache

logger = logging.getLogger(__name__)


class MemoryCache:
    """进程内 TTL 缓存（Redis 不可用时的降级方案）"""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, str]] = {}

    def get(self, key: str) -> Any:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None
        try:
            return json.loads(value)
        except Exception:
            self._store.pop(key, None)
            return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        self._store[key] = (time.time() + ttl, payload)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        """删除指定前缀的所有键"""
        for key in [k for k in self._store if k.startswith(f"{prefix}:")]:
            self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


memory_cache = MemoryCache()
_redis: Optional[Any] = None
_redis_usable: Optional[bool] = None  # None=未检测；False=已降级内存缓存
_degraded_until: float = 0.0
_probe_lock = asyncio.Lock()
_inflight: dict[str, asyncio.Future] = {}
_inflight_guard = asyncio.Lock()


def _mark_degraded(exc: BaseException) -> None:
    global _redis_usable, _degraded_until
    was = _redis_usable
    _redis_usable = False
    _degraded_until = time.monotonic() + float(settings.REDIS_RECOVER_SECONDS)
    if was is not False:
        logger.warning("redis_status=degraded error=%s", type(exc).__name__)
        observe_cache(degraded=True)


def _mark_available() -> None:
    global _redis_usable
    if _redis_usable is False:
        logger.info("redis_status=recovered")
    elif _redis_usable is not True:
        logger.info("redis_status=available")
    _redis_usable = True


def redis_runtime_status() -> str | None:
    """None if Redis is disabled; otherwise available or degraded."""
    if not is_redis_enabled():
        return None
    if _redis_usable is False:
        return "degraded"
    return "available"


def reset_cache_runtime() -> None:
    """Reset process-local Redis/memory cache state for tests."""
    global _redis, _redis_usable, _degraded_until
    _redis = None
    _redis_usable = None
    _degraded_until = 0.0
    memory_cache.clear()
    reset_redis_client()


def resolve_redis():
    """返回可用的 Redis 客户端，或 None（未启用 / 冷却期内降级内存）。"""
    global _redis, _redis_usable
    if not is_redis_enabled():
        _redis_usable = False
        return None
    now = time.monotonic()
    if _redis_usable is False and now < _degraded_until:
        return None
    if _redis is None:
        try:
            _redis = get_redis_client()
        except Exception as exc:  # pragma: no cover - 依赖外部 Redis
            logger.warning("Redis 初始化失败，降级到内存缓存：%s", exc)
            _mark_degraded(exc)
            return None
    return _redis


async def probe_redis() -> str | None:
    """Ping Redis and update runtime status. Used by /api/health."""
    if not is_redis_enabled():
        return None
    async with _probe_lock:
        client = resolve_redis()
        if client is None:
            client = get_redis_client()
        try:
            await client.ping()
            _mark_available()
            return "available"
        except Exception as exc:
            _mark_degraded(exc)
            return "degraded"


async def cache_get(key: str) -> Any:
    """读取缓存；未命中/失败时返回 None"""
    started = time.perf_counter()
    status = "ok"
    error_type = None
    client = resolve_redis()
    try:
        if client is not None:
            try:
                raw = await client.get(key)
                _mark_available()
                if raw is None:
                    observe_cache(hit=False)
                    status = "miss"
                    return None
                observe_cache(hit=True)
                status = "hit"
                return json.loads(raw)
            except Exception as exc:  # pragma: no cover - 依赖外部 Redis
                logger.warning("Redis GET 失败，降级到内存缓存：%s", exc)
                _mark_degraded(exc)
                status = "degraded"
                error_type = type(exc).__name__
        value = memory_cache.get(key)
        observe_cache(hit=value is not None)
        if status == "ok":
            status = "hit" if value is not None else "miss"
        return value
    finally:
        observe_dependency(
            dependency="redis",
            operation="get",
            status=status,
            duration_ms=(time.perf_counter() - started) * 1000,
            error_type=error_type,
        )


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """写入缓存（默认 TTL 取 settings.REDIS_CACHE_TTL）"""
    started = time.perf_counter()
    status = "ok"
    error_type = None
    client = resolve_redis()
    ttl = ttl if ttl is not None else settings.REDIS_CACHE_TTL
    payload = json.dumps(value, ensure_ascii=False, default=str)
    try:
        if client is not None:
            try:
                await client.setex(key, ttl, payload)
                _mark_available()
                return
            except Exception as exc:  # pragma: no cover - 依赖外部 Redis
                logger.warning("Redis SET 失败，降级到内存缓存：%s", exc)
                _mark_degraded(exc)
                status = "degraded"
                error_type = type(exc).__name__
        memory_cache.set(key, value, ttl)
    finally:
        observe_dependency(
            dependency="redis",
            operation="set",
            status=status,
            duration_ms=(time.perf_counter() - started) * 1000,
            error_type=error_type,
        )


async def cache_delete(key: str) -> None:
    """删除单个缓存键"""
    client = resolve_redis()
    if client is not None:
        try:
            await client.delete(key)
            _mark_available()
        except Exception as exc:  # pragma: no cover - 依赖外部 Redis
            _mark_degraded(exc)
    memory_cache.delete(key)


async def cache_delete_prefix(prefix: str) -> None:
    """删除指定前缀的所有缓存键（写操作后的缓存失效）"""
    client = resolve_redis()
    if client is not None:
        try:
            async for key in client.scan_iter(match=f"{prefix}:*"):
                await client.delete(key)
            _mark_available()
        except Exception as exc:  # pragma: no cover - 依赖外部 Redis
            _mark_degraded(exc)
    memory_cache.delete_prefix(prefix)


def build_key(prefix: str, *parts: Any) -> str:
    """构造缓存键：prefix:p1|p2|..."""
    segments = [str(p) for p in parts]
    return f"{prefix}:{'|'.join(segments)}" if segments else prefix


def _make_key(func: Callable, key_prefix: str, keys: Optional[Tuple[str, ...]], args, kwargs) -> str:
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    if keys is not None:
        seg = [str(bound.arguments[k]) for k in keys]
    else:
        seg = [f"{name}={bound.arguments[name]}" for name in bound.arguments]
    return build_key(key_prefix or func.__name__, *seg)


async def _singleflight(key: str, loader):
    started = time.perf_counter()
    status = "ok"
    error_type = None
    async with _inflight_guard:
        existing = _inflight.get(key)
        if existing is not None:
            waiter = existing
        else:
            loop = asyncio.get_running_loop()
            waiter = loop.create_future()
            _inflight[key] = waiter
            existing = None
    try:
        if existing is not None:
            return await waiter
        try:
            result = await loader()
            if not waiter.done():
                waiter.set_result(result)
            return result
        except Exception as exc:
            status = "error"
            error_type = type(exc).__name__
            if not waiter.done():
                waiter.set_exception(exc)
            raise
        finally:
            async with _inflight_guard:
                _inflight.pop(key, None)
    finally:
        observe_dependency(
            dependency="redis",
            operation="singleflight",
            status=status,
            duration_ms=(time.perf_counter() - started) * 1000,
            error_type=error_type,
        )


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    keys: Optional[Tuple[str, ...]] = None,
):
    """函数级缓存装饰器

    - ttl: 缓存秒数，默认 300
    - key_prefix: 缓存键前缀（建议显式指定，避免同名函数冲突）
    - keys: 参与缓存键的 kwargs 名；缺省时自动使用全部签名参数
      （端点依赖 db/current_user 等不可序列化对象时，用 keys 限定查询参数）

    支持 async 函数（走 Redis + 内存降级）与 sync 函数（仅内存缓存）。
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = _make_key(func, key_prefix, keys, args, kwargs)
                hit = await cache_get(key)
                if hit is not None:
                    return hit

                async def load():
                    result = await func(*args, **kwargs)
                    await cache_set(key, result, ttl)
                    return result

                return await _singleflight(key, load)

            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_key(func, key_prefix, keys, args, kwargs)
            hit = memory_cache.get(key)
            observe_cache(hit=hit is not None)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            memory_cache.set(key, result, ttl)
            return result

        return wrapper
    return decorator

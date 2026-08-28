"""
T4-3 缓存层测试（Redis 不可用时降级到内存缓存）

验证：
1. cache_get/cache_set/cache_delete/cache_delete_prefix 基础读写
2. @cached 装饰器：async/sync 函数缓存、参数区分、keys 限定
3. TTL 过期
"""
import pytest

from utils import cache
from utils.cache import (
    cache_delete,
    cache_delete_prefix,
    cache_get,
    cache_set,
    cached,
    memory_cache,
)


@pytest.fixture(autouse=True)
def _clear_memory_cache():
    """每个测试前后清空内存缓存，避免跨测试污染"""
    memory_cache.clear()
    yield
    memory_cache.clear()


@pytest.mark.unit
class TestCacheOps:
    async def test_set_get_roundtrip(self):
        await cache_set("k1", {"a": 1, "b": ["x", "y"]})
        assert await cache_get("k1") == {"a": 1, "b": ["x", "y"]}

    async def test_get_miss_returns_none(self):
        assert await cache_get("missing-key") is None

    async def test_delete_single_key(self):
        await cache_set("k1", 1)
        await cache_delete("k1")
        assert await cache_get("k1") is None

    async def test_delete_prefix(self):
        await cache_set("nodes:list:1", {"a": 1})
        await cache_set("nodes:list:2", {"a": 2})
        await cache_set("vehicles:list:1", {"a": 3})
        await cache_delete_prefix("nodes:list")
        assert await cache_get("nodes:list:1") is None
        assert await cache_get("nodes:list:2") is None
        assert await cache_get("vehicles:list:1") == {"a": 3}

    async def test_ttl_expiry(self):
        await cache_set("k1", {"a": 1}, ttl=-1)  # 立即过期
        assert await cache_get("k1") is None

    async def test_redis_disabled_uses_memory(self):
        """REDIS_ENABLED 默认 False 时走内存缓存"""
        assert cache.resolve_redis() is None
        await cache_set("k1", 42)
        assert await cache_get("k1") == 42


@pytest.mark.unit
class TestCachedDecorator:
    async def test_async_decorator_caches(self):
        calls = []

        @cached(ttl=300, key_prefix="test:async")
        async def fn(x):
            calls.append(x)
            return {"x": x}

        assert await fn(1) == {"x": 1}
        assert await fn(1) == {"x": 1}
        assert calls == [1]  # 第二次命中缓存，函数只执行一次

    async def test_async_decorator_varies_by_arg(self):
        calls = []

        @cached(ttl=300, key_prefix="test:async")
        async def fn(x):
            calls.append(x)
            return {"x": x}

        await fn(1)
        await fn(2)
        assert calls == [1, 2]

    async def test_async_decorator_keys_limits_cache_key(self):
        """keys 限定后，未列出的参数不进缓存键"""
        calls = []

        @cached(ttl=300, key_prefix="test:keys", keys=("x",))
        async def fn(x, db):
            calls.append(x)
            return {"x": x}

        await fn(1, "db-a")
        await fn(1, "db-b")
        assert calls == [1]  # 不同 db 命中同一缓存

    async def test_async_decorator_ttl(self):
        calls = []

        @cached(ttl=-1, key_prefix="test:ttl")
        async def fn(x):
            calls.append(x)
            return {"x": x}

        await fn(1)
        await fn(1)
        assert calls == [1, 1]  # 立即过期，每次都执行

    def test_sync_decorator_caches(self):
        calls = []

        @cached(ttl=300, key_prefix="test:sync")
        def fn(x):
            calls.append(x)
            return x * 2

        assert fn(2) == 4
        assert fn(2) == 4
        assert calls == [2]

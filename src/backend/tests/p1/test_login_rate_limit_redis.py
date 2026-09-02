"""Real Redis Lua checks for the login rate limiter."""
from uuid import uuid4

import pytest
import redis

from core.error_codes import CODE_LOGIN_RATE_LIMITED
from core.errors import DomainError
from core.login_rate_limit import (
    LoginRateLimiter,
    login_rate_limit_key,
    redis_login_rate_limit_key,
)


def test_redis_lua_window_threshold_ttl_and_unlock(p1_redis_url: str):
    client = redis.Redis.from_url(p1_redis_url, decode_responses=True)
    limiter = LoginRateLimiter(3, 12, redis_factory=lambda: client, recover_seconds=0.2)
    subject = login_rate_limit_key(f"p1-lua-{uuid4().hex}", "203.0.113.10")
    redis_key = redis_login_rate_limit_key(subject)
    try:
        client.delete(redis_key)
        limiter.check(subject)
        limiter.record_failure(subject)
        limiter.record_failure(subject)
        limiter.record_failure(subject)
        assert limiter.last_backend == "redis"
        with pytest.raises(DomainError) as blocked:
            limiter.check(subject)
        assert blocked.value.code == CODE_LOGIN_RATE_LIMITED
        assert blocked.value.meta["degraded"] is False
        ttl_ms = client.pttl(redis_key)
        assert 0 < ttl_ms <= 12000
        assert client.get(redis_key) == "3"
        limiter.record_success(subject)
        assert client.get(redis_key) is None
        limiter.check(subject)
    finally:
        client.delete(redis_key)
        client.close()

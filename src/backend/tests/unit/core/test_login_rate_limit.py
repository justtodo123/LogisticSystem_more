from __future__ import annotations

import math
from typing import Any

import pytest

from core.error_codes import CODE_LOGIN_RATE_LIMITED
from core.errors import DomainError
from core.login_rate_limit import (
    LOGIN_RATE_LIMIT_LUA,
    LOGIN_RATE_LIMIT_REDIS_PREFIX,
    LoginRateLimiter,
    login_rate_limit_key,
    redis_login_rate_limit_key,
)


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeRedis:
    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.fail = False
        self.calls: list[str] = []
        self._store: dict[str, tuple[int, float | None]] = {}

    def eval(self, script: str, num_keys: int, *args: Any) -> list[int]:
        if self.fail:
            raise ConnectionError("redis down")
        if script != LOGIN_RATE_LIMIT_LUA:
            raise AssertionError("unexpected lua script")
        key = str(args[0])
        window = int(args[1])
        max_attempts = int(args[2])
        action = str(args[3])
        self.calls.append(action)
        return self._apply(key, window, max_attempts, action)

    def close(self) -> None:
        return None

    def _current(self, key: str) -> tuple[int, float | None] | None:
        item = self._store.get(key)
        if item is None:
            return None
        count, expires_at = item
        if expires_at is not None and self.clock() >= expires_at:
            self._store.pop(key, None)
            return None
        return count, expires_at

    def _apply(self, key: str, window: int, max_attempts: int, action: str) -> list[int]:
        if action == "success":
            self._store.pop(key, None)
            return [0, 0, 0]
        current = self._current(key)
        if action == "check":
            if current is None:
                return [0, 0, 0]
            count, expires_at = current
            if count >= max_attempts:
                retry_after = window
                if expires_at is not None:
                    retry_after = max(1, int(math.ceil(expires_at - self.clock())))
                return [count, retry_after, 1]
            return [count, 0, 0]
        if action == "fail":
            if current is None:
                self._store[key] = (1, self.clock() + window)
                return [1, window, 0]
            count, expires_at = current
            count += 1
            self._store[key] = (count, expires_at)
            retry_after = window
            if expires_at is not None:
                retry_after = max(1, int(math.ceil(expires_at - self.clock())))
            return [count, retry_after, 0]
        raise ValueError(action)


def test_login_rate_limit_key_is_hmac_and_hides_username():
    key = login_rate_limit_key("Alice", "127.0.0.1")
    assert "alice" not in key.lower()
    assert "127.0.0.1" not in key
    assert len(key) == 64
    assert redis_login_rate_limit_key(key).startswith(f"{LOGIN_RATE_LIMIT_REDIS_PREFIX}:")
    assert login_rate_limit_key("Alice", "127.0.0.1") == key
    assert login_rate_limit_key("alice", "127.0.0.1") == key
    assert login_rate_limit_key("alice", "10.0.0.2") != key
    assert login_rate_limit_key("bob", "127.0.0.1") != key


def test_memory_window_threshold_ttl_and_unlock():
    clock = FakeClock()
    limiter = LoginRateLimiter(2, 10, clock=clock)
    limiter.record_failure("k")
    limiter.check("k")
    limiter.record_failure("k")
    with pytest.raises(DomainError) as blocked:
        limiter.check("k")
    assert blocked.value.code == CODE_LOGIN_RATE_LIMITED
    assert blocked.value.meta["retry_after"] == 10
    assert blocked.value.meta["degraded"] is False
    clock.advance(10)
    limiter.check("k")
    limiter.record_failure("k")
    limiter.record_success("k")
    limiter.check("k")


def test_redis_backend_counts_ttl_and_unlock():
    clock = FakeClock()
    fake = FakeRedis(clock)
    limiter = LoginRateLimiter(2, 8, redis_factory=lambda: fake, clock=clock)
    limiter.record_failure("k")
    limiter.record_failure("k")
    assert limiter.last_backend == "redis"
    with pytest.raises(DomainError) as blocked:
        limiter.check("k")
    assert blocked.value.meta["retry_after"] == 8
    limiter.record_success("k")
    limiter.check("k")
    clock.advance(8)
    limiter.record_failure("k")
    limiter.record_failure("k")
    clock.advance(8)
    limiter.check("k")


def test_redis_exception_degrades_to_memory_then_recovers():
    clock = FakeClock()
    fake = FakeRedis(clock)
    fake.fail = True
    limiter = LoginRateLimiter(
        2,
        10,
        redis_factory=lambda: fake,
        recover_seconds=2,
        clock=clock,
    )
    limiter.record_failure("k")
    assert limiter.last_backend == "memory"
    assert limiter.public_meta() == {"degraded": True, "degraded_reason": "redis"}
    limiter.record_failure("k")
    with pytest.raises(DomainError) as blocked:
        limiter.check("k")
    assert blocked.value.meta["degraded"] is True
    fake.fail = False
    clock.advance(2)
    limiter.record_success("k")
    limiter.check("k")
    assert limiter.last_backend == "redis"
    assert limiter.public_meta()["degraded"] is False


def test_lua_script_is_atomic_count_ttl_and_unlock():
    for token in ("INCR", "EXPIRE", "PTTL", "DEL", "GET"):
        assert token in LOGIN_RATE_LIMIT_LUA

"""Login rate limiter: Redis shared state with process-local fallback.

R2-04B defined the login contract. R2-05 shares the counter across workers
when Redis is available. Redis outages fall back to process-local counts and
must advertise degraded so callers do not treat the limiter as global.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import math
import threading
import time
from collections.abc import Callable

from core.error_codes import CODE_LOGIN_RATE_LIMITED
from core.errors import DomainError

logger = logging.getLogger(__name__)

LOGIN_RATE_LIMIT_REDIS_PREFIX = "loginrl"
_REDIS_SOCKET_TIMEOUT_SECONDS = 1.0

LOGIN_RATE_LIMIT_LUA = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local max_attempts = tonumber(ARGV[2])
local action = ARGV[3]

if action == "success" then
  redis.call("DEL", key)
  return {0, 0, 0}
end

if action == "check" then
  local count = tonumber(redis.call("GET", key) or "0")
  local ttl_ms = tonumber(redis.call("PTTL", key))
  local blocked = 0
  local retry_after = 0
  if count >= max_attempts then
    blocked = 1
    if ttl_ms > 0 then
      retry_after = math.max(1, math.ceil(ttl_ms / 1000.0))
    else
      retry_after = window
    end
  end
  return {count, retry_after, blocked}
end

if action == "fail" then
  local count = tonumber(redis.call("INCR", key))
  local ttl_ms = tonumber(redis.call("PTTL", key))
  if count == 1 or ttl_ms < 0 then
    redis.call("EXPIRE", key, window)
    ttl_ms = window * 1000
  end
  return {count, math.max(1, math.ceil(ttl_ms / 1000.0)), 0}
end

return redis.error_reply("unknown login rate limit action")
"""


class MemoryLoginRateStore:
    """Fixed-window counter used when Redis is disabled or degraded."""

    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        clock: Callable[[], float],
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._windows: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._windows.clear()

    def _current_locked(self, key: str, now: float) -> tuple[int, float] | None:
        window = self._windows.get(key)
        if window is None:
            return None
        count, expires_at = window
        if now >= expires_at:
            self._windows.pop(key, None)
            return None
        return count, expires_at

    def check(self, key: str) -> int | None:
        now = self._clock()
        with self._lock:
            window = self._current_locked(key, now)
            if window is None:
                return None
            count, expires_at = window
            if count >= self.max_attempts:
                return max(1, int(math.ceil(expires_at - now)))
            return None

    def record_failure(self, key: str) -> None:
        now = self._clock()
        with self._lock:
            window = self._current_locked(key, now)
            if window is None:
                self._windows[key] = (1, now + self.window_seconds)
                return
            count, expires_at = window
            self._windows[key] = (count + 1, expires_at)

    def record_success(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        *,
        redis_factory: Callable[[], object] | None = None,
        recover_seconds: float = 2.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.recover_seconds = recover_seconds
        self._redis_factory = redis_factory
        self._clock = clock
        self.memory = MemoryLoginRateStore(max_attempts, window_seconds, clock)
        self._redis: object | None = None
        self._redis_usable: bool | None = None
        self._degraded_until = 0.0
        self._lock = threading.Lock()
        self.degraded = False
        self.degraded_reason: str | None = None
        self.last_backend = "memory"

    def public_meta(self) -> dict[str, object]:
        with self._lock:
            if self.degraded:
                return {"degraded": True, "degraded_reason": "redis"}
            return {"degraded": False, "degraded_reason": None}

    def reset(self) -> None:
        self.memory.reset()
        with self._lock:
            self.degraded = False
            self.degraded_reason = None
            self._redis_usable = None
            self._degraded_until = 0.0
            self.last_backend = "memory"
            client = self._redis
            self._redis = None
        _close_redis_client(client)

    def close(self) -> None:
        self.reset()

    def check(self, key: str) -> None:
        result = self._redis_eval("check", key)
        if result is None:
            self.last_backend = "memory"
            retry_after = self.memory.check(key)
            if retry_after is not None:
                self._raise_limited(retry_after)
            return
        self.last_backend = "redis"
        _count, retry_after, blocked = result
        if blocked:
            self._raise_limited(retry_after)

    def record_failure(self, key: str) -> None:
        result = self._redis_eval("fail", key)
        if result is None:
            self.last_backend = "memory"
            self.memory.record_failure(key)
            return
        self.last_backend = "redis"

    def record_success(self, key: str) -> None:
        result = self._redis_eval("success", key)
        if result is None:
            self.last_backend = "memory"
            self.memory.record_success(key)
            return
        self.last_backend = "redis"
        self.memory.record_success(key)

    def _raise_limited(self, retry_after: int) -> None:
        meta = {"retry_after": int(retry_after), **self.public_meta()}
        raise DomainError(CODE_LOGIN_RATE_LIMITED, meta=meta)

    def _redis_eval(self, action: str, key: str) -> tuple[int, int, int] | None:
        client = self._usable_redis_client()
        if client is None:
            return None
        eval_script = getattr(client, "eval", None)
        if not callable(eval_script):
            self._mark_degraded(TypeError("redis client missing eval"))
            return None
        try:
            raw = eval_script(
                LOGIN_RATE_LIMIT_LUA,
                1,
                redis_login_rate_limit_key(key),
                self.window_seconds,
                self.max_attempts,
                action,
            )
            parsed = _parse_lua_result(raw)
            self._mark_available()
            return parsed
        except Exception as exc:
            logger.warning(
                "login_rate_limit redis_status=degraded action=%s error=%s",
                action,
                type(exc).__name__,
            )
            self._mark_degraded(exc)
            return None

    def _usable_redis_client(self) -> object | None:
        if self._redis_factory is None:
            return None
        now = self._clock()
        with self._lock:
            if self._redis_usable is False and now < self._degraded_until:
                return None
        if self._redis is None:
            try:
                client = self._redis_factory()
            except Exception as exc:
                self._mark_degraded(exc)
                return None
            with self._lock:
                self._redis = client
        return self._redis

    def _mark_degraded(self, exc: BaseException) -> None:
        with self._lock:
            was = self._redis_usable
            self._redis_usable = False
            self._degraded_until = self._clock() + float(self.recover_seconds)
            self.degraded = True
            self.degraded_reason = "redis"
            client = self._redis
            self._redis = None
        if was is not False:
            logger.warning("login_rate_limit redis_status=degraded error=%s", type(exc).__name__)
        _close_redis_client(client)

    def _mark_available(self) -> None:
        with self._lock:
            was = self._redis_usable
            self._redis_usable = True
            self.degraded = False
            self.degraded_reason = None
        if was is False:
            logger.info("login_rate_limit redis_status=recovered")
        elif was is not True:
            logger.info("login_rate_limit redis_status=available")


def _parse_lua_result(raw: object) -> tuple[int, int, int]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        raise ValueError("unexpected login rate limit lua result")
    return int(raw[0]), int(raw[1]), int(raw[2])


def _close_redis_client(client: object | None) -> None:
    if client is None:
        return
    close = getattr(client, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def login_rate_limit_key(username: str, client_ip: str | None) -> str:
    """Return an HMAC subject. Never embed the raw username or IP in Redis keys."""
    from config.settings import settings

    ip = (client_ip or "unknown").strip() or "unknown"
    user = (username or "").strip().lower()
    material = f"{ip}\0{user}".encode("utf-8")
    digest = hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        material,
        hashlib.sha256,
    ).hexdigest()
    return digest


def redis_login_rate_limit_key(subject: str) -> str:
    return f"{LOGIN_RATE_LIMIT_REDIS_PREFIX}:{subject}"


def _redis_factory_from_settings() -> Callable[[], object] | None:
    from config.redis import is_redis_enabled
    from config.settings import settings

    if not is_redis_enabled():
        return None

    def factory() -> object:
        import redis

        return redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=_REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_timeout=_REDIS_SOCKET_TIMEOUT_SECONDS,
        )

    return factory


_limiter: LoginRateLimiter | None = None
_limiter_lock = threading.Lock()


def get_login_rate_limiter() -> LoginRateLimiter:
    global _limiter
    from config.settings import settings

    with _limiter_lock:
        if _limiter is None:
            _limiter = LoginRateLimiter(
                settings.LOGIN_RATE_LIMIT_ATTEMPTS,
                settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
                redis_factory=_redis_factory_from_settings(),
                recover_seconds=float(settings.REDIS_RECOVER_SECONDS),
            )
        return _limiter


def reset_login_rate_limiter() -> None:
    global _limiter
    with _limiter_lock:
        if _limiter is not None:
            _limiter.close()
        _limiter = None

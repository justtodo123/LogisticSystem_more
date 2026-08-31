"""Process-local login rate limiter for R2-04B.

P0 only guarantees a single worker. Cross-worker behaviour is R2-05.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict

from core.error_codes import CODE_LOGIN_RATE_LIMITED
from core.errors import DomainError


class LoginRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()

    def _prune_locked(self, key: str, now: float) -> list[float]:
        cutoff = now - self.window_seconds
        recent = [stamp for stamp in self._failures.get(key, []) if stamp > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            recent = self._prune_locked(key, now)
            if len(recent) >= self.max_attempts:
                retry_after = max(1, int(self.window_seconds - (now - recent[0])))
                raise DomainError(
                    CODE_LOGIN_RATE_LIMITED,
                    meta={"retry_after": retry_after},
                )

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            recent = self._prune_locked(key, now)
            recent.append(now)
            self._failures[key] = recent

    def record_success(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


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
            )
        return _limiter


def reset_login_rate_limiter() -> None:
    limiter = get_login_rate_limiter()
    limiter.reset()


def login_rate_limit_key(username: str, client_ip: str | None) -> str:
    ip = (client_ip or "unknown").strip() or "unknown"
    return f"{ip}:{(username or "").strip().lower()}"

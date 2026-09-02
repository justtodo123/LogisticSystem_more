"""Cross-worker HTTP login rate limit using shared Redis state."""
import os
from uuid import uuid4

import httpx
import pytest

from core.error_codes import CODE_LOGIN_RATE_LIMITED
from models.user import User
from services.auth_service import get_password_hash


def _worker_url(name: str) -> str:
    url = os.environ.get(name, "").strip().rstrip("/")
    if not url:
        pytest.skip(f"requires {name}")
    return url


@pytest.mark.integration
def test_two_workers_share_login_rate_limit(p1_postgres, p1_redis_url, p1_row_cleanup):
    from config.settings import settings

    _engine, factory = p1_postgres
    worker_a = _worker_url("P1_WORKER_A_URL")
    worker_b = _worker_url("P1_WORKER_B_URL")
    suffix = uuid4().hex
    username = f"p1-rl-{suffix}"
    other_name = f"p1-rl-other-{suffix}"
    password = f"P1-{suffix}"

    seed = factory()
    try:
        users = [
            User(
                username=username,
                password_hash=get_password_hash(password),
                role="dispatcher",
                display_name="P1 login rate limit",
                is_active=True,
            ),
            User(
                username=other_name,
                password_hash=get_password_hash(password),
                role="dispatcher",
                display_name="P1 login rate other",
                is_active=True,
            ),
        ]
        seed.add_all(users)
        seed.commit()
    finally:
        seed.close()

    p1_row_cleanup(
        User,
        filters={User: User.username.in_((username, other_name))},
    )

    with httpx.Client(timeout=30) as client:
        for index in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
            base = worker_a if index % 2 == 0 else worker_b
            response = client.post(
                f"{base}/api/auth/login",
                json={"username": username, "password": "wrong"},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["code"] == 40100
            assert body["meta"]["degraded"] is False

        blocked = client.post(
            f"{worker_b}/api/auth/login",
            json={"username": username, "password": password},
        )
        assert blocked.status_code == 429
        blocked_body = blocked.json()
        assert blocked_body["code"] == CODE_LOGIN_RATE_LIMITED
        assert "retry_after" in blocked_body["meta"]
        assert blocked_body["meta"]["degraded"] is False
        assert "Retry-After" in blocked.headers

        other_failed = client.post(
            f"{worker_a}/api/auth/login",
            json={"username": other_name, "password": "wrong"},
        )
        assert other_failed.status_code == 200
        assert other_failed.json()["code"] == 40100

        other_ok = client.post(
            f"{worker_a}/api/auth/login",
            json={"username": other_name, "password": password},
        )
        assert other_ok.status_code == 200
        assert other_ok.json()["code"] == 0
        assert other_ok.json()["meta"]["degraded"] is False

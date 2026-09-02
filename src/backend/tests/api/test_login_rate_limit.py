import pytest
from core.error_codes import CODE_LOGIN_RATE_LIMITED
from models.user import User
from services.auth_service import get_password_hash


@pytest.mark.api
def test_login_rate_limit_after_repeated_failures(client, db_session):
    from config.settings import settings

    user = User(
        username="rate_user",
        password_hash=get_password_hash("123456"),
        role="dispatcher",
        display_name="rate",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    last_ok = None
    for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
        last_ok = client.post(
            "/api/auth/login",
            json={"username": "rate_user", "password": "wrong"},
        )
        assert last_ok.status_code == 200
        assert last_ok.json()["code"] == 40100

    blocked = client.post(
        "/api/auth/login",
        json={"username": "rate_user", "password": "wrong"},
    )
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["code"] == CODE_LOGIN_RATE_LIMITED
    assert body["data"] is None
    assert "retry_after" in body["meta"]
    assert "Retry-After" in blocked.headers


@pytest.mark.api
def test_login_rate_limit_does_not_leak_password(client):
    from config.settings import settings

    for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
        client.post("/api/auth/login", json={"username": "missing_rate", "password": "wrong"})
    blocked = client.post("/api/auth/login", json={"username": "missing_rate", "password": "wrong"})
    assert blocked.status_code == 429
    assert "password" not in blocked.json()["message"].lower()
    assert "sql" not in blocked.json()["message"].lower()

@pytest.mark.api
def test_login_rate_limit_success_resets_and_other_users_are_isolated(client, db_session):
    from config.settings import settings

    user = User(
        username="rate_reset",
        password_hash=get_password_hash("123456"),
        role="dispatcher",
        display_name="rate-reset",
        is_active=True,
    )
    other = User(
        username="rate_other",
        password_hash=get_password_hash("123456"),
        role="dispatcher",
        display_name="rate-other",
        is_active=True,
    )
    db_session.add_all([user, other])
    db_session.commit()

    for _ in range(2):
        failed = client.post(
            "/api/auth/login",
            json={"username": "rate_reset", "password": "wrong"},
        )
        assert failed.status_code == 200
        assert failed.json()["code"] == 40100
        assert failed.json()["meta"]["degraded"] is False

    success = client.post(
        "/api/auth/login",
        json={"username": "rate_reset", "password": "123456"},
    )
    assert success.status_code == 200
    assert success.json()["code"] == 0
    assert success.json()["meta"]["degraded"] is False

    for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
        failed = client.post(
            "/api/auth/login",
            json={"username": "rate_reset", "password": "wrong"},
        )
        assert failed.status_code == 200
        assert failed.json()["code"] == 40100

    blocked = client.post(
        "/api/auth/login",
        json={"username": "rate_reset", "password": "123456"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == CODE_LOGIN_RATE_LIMITED
    assert blocked.json()["meta"]["degraded"] is False

    other_failed = client.post(
        "/api/auth/login",
        json={"username": "rate_other", "password": "wrong"},
    )
    assert other_failed.status_code == 200
    assert other_failed.json()["code"] == 40100

    other_ok = client.post(
        "/api/auth/login",
        json={"username": "rate_other", "password": "123456"},
    )
    assert other_ok.status_code == 200
    assert other_ok.json()["code"] == 0

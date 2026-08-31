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

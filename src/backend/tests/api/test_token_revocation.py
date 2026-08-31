import pytest
from models.user import User
from services.auth_service import get_password_hash


def _create_and_login(client, db_session, username="revoke_user", role="dispatcher"):
    user = User(
        username=username,
        password_hash=get_password_hash("123456"),
        role=role,
        display_name=username,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"username": username, "password": "123456"})
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return user, {"Authorization": f"Bearer {token}"}


@pytest.mark.api
def test_login_expires_in_matches_settings(client, db_session):
    from config.settings import settings

    _, headers = _create_and_login(client, db_session, username="expire_user")
    login = client.post("/api/auth/login", json={"username": "expire_user", "password": "123456"})
    assert login.json()["data"]["expires_in"] == settings.JWT_EXPIRE_SECONDS


@pytest.mark.api
def test_logout_rejects_old_token(client, db_session):
    _, headers = _create_and_login(client, db_session, username="logout_user")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    rejected = client.get("/api/auth/me", headers=headers)
    assert rejected.status_code == 401
    assert rejected.json()["code"] == 40100


@pytest.mark.api
def test_disable_user_rejects_old_token(client, db_session):
    admin = User(
        username="admin_revoker",
        password_hash=get_password_hash("123456"),
        role="admin",
        display_name="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    target, target_headers = _create_and_login(client, db_session, username="disable_target")
    admin_login = client.post("/api/auth/login", json={"username": "admin_revoker", "password": "123456"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}
    patched = client.patch(
        f"/api/users/{target.username}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert patched.status_code == 200
    rejected = client.get("/api/auth/me", headers=target_headers)
    assert rejected.status_code == 401
    assert rejected.json()["code"] == 40100


@pytest.mark.api
def test_role_change_rejects_old_token(client, db_session):
    admin = User(
        username="admin_role",
        password_hash=get_password_hash("123456"),
        role="admin",
        display_name="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    target, target_headers = _create_and_login(client, db_session, username="role_target", role="dispatcher")
    before = client.get("/api/schedule/global", headers=target_headers)
    assert before.status_code != 403
    admin_login = client.post("/api/auth/login", json={"username": "admin_role", "password": "123456"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}
    patched = client.patch(
        f"/api/users/{target.username}",
        json={"role": "viewer"},
        headers=admin_headers,
    )
    assert patched.status_code == 200
    rejected = client.get("/api/schedule/global", headers=target_headers)
    assert rejected.status_code == 401
    assert rejected.json()["code"] == 40100


@pytest.mark.api
def test_independent_sessions_increment_token_version(client, db_session, test_db):
    from services.auth_service import bump_token_version, get_user_by_username

    _engine, TestingSessionLocal = test_db
    user, headers = _create_and_login(client, db_session, username="concurrent_tv")

    for _ in range(2):
        session = TestingSessionLocal()
        try:
            fresh = get_user_by_username(session, user.username)
            bump_token_version(session, fresh, commit=True)
        finally:
            session.close()

    db_session.commit()
    db_session.refresh(user)
    assert user.token_version >= 2
    rejected = client.get("/api/auth/me", headers=headers)
    assert rejected.status_code == 401

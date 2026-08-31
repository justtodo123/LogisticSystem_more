import pytest
from models.user import User
from services.auth_service import get_password_hash


ROLES = ("admin", "dispatcher", "viewer", "manager", "warehouse_operator", "ghost")

# method, path, permission, extra kwargs
CASES = [
    ("GET", "/api/orders", "orders:read", {}),
    ("GET", "/api/schedule/global", "schedule:read", {}),
    ("GET", "/api/reports/overview", "reports:read", {}),
    ("GET", "/api/audit-logs", "audit:read", {}),
    ("GET", "/api/simulation/arrival-packages", "arrivals:confirm", {}),
    ("POST", "/api/export/orders", "export:read", {}),
]


def _login(client, db_session, role, suffix=""):
    username = f"rbac_{role}{suffix}"
    user = User(
        username=username,
        password_hash=get_password_hash("123456"),
        role=role,
        display_name=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    response = client.post("/api/auth/login", json={"username": username, "password": "123456"})
    assert response.status_code == 200
    assert response.json()["code"] == 0
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.api
@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("method,path,permission,kwargs", CASES)
def test_role_matrix_http(client, db_session, role, method, path, permission, kwargs):
    from core.permissions import ROLE_PERMISSIONS

    headers = _login(client, db_session, role, suffix="_" + permission.replace(":", "_"))
    response = client.request(method, path, headers=headers, **kwargs)
    allowed = permission in ROLE_PERMISSIONS.get(role, [])
    if allowed:
        assert response.status_code not in (401, 403)
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            assert response.json().get("code") != 40300
    else:
        assert response.status_code == 403
        assert response.json()["code"] == 40300


@pytest.mark.api
def test_me_permissions_match_role(client, db_session):
    from core.permissions import get_user_permissions

    headers = _login(client, db_session, "dispatcher", suffix="_me")
    response = client.get("/api/auth/me", headers=headers)
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    user = db_session.query(User).filter_by(username="rbac_dispatcher_me").one()
    assert body["data"]["permissions"] == get_user_permissions(user)


@pytest.mark.api
def test_unknown_role_me_has_empty_permissions(client, db_session):
    headers = _login(client, db_session, "ghost")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["permissions"] == []

from types import SimpleNamespace

import pytest

from core.permissions import (
    PERMISSIONS,
    ROLE_PERMISSIONS,
    get_user_permissions,
    user_has_permission,
)


EXPECTED_GRANTS = {
    "admin": set(PERMISSIONS),
    "dispatcher": set(PERMISSIONS) - {"admin:users"},
    "viewer": {
        "orders:read", "goods:read", "schedule:read",
        "vehicles:read", "drivers:read", "nodes:read",
        "packages:read", "exceptions:read", "reports:read",
        "notifications:read",
    },
    "manager": {
        "orders:read", "orders:write", "orders:import",
        "goods:read", "packages:read", "nodes:read",
        "vehicles:read", "drivers:read", "reports:read",
        "notifications:read",
    },
    "warehouse_operator": {
        "orders:read", "orders:write", "orders:import",
        "goods:read", "packages:read", "nodes:read",
        "vehicles:read", "drivers:read", "reports:read",
        "notifications:read",
    },
}


@pytest.mark.parametrize("role", sorted(EXPECTED_GRANTS))
def test_role_permission_matrix(role):
    user = SimpleNamespace(role=role)
    assert set(get_user_permissions(user)) == EXPECTED_GRANTS[role]


def test_unknown_role_fails_closed():
    user = SimpleNamespace(role="ghost")
    assert get_user_permissions(user) == []
    assert user_has_permission(user, "orders:read") is False


def test_manager_cannot_confirm_arrivals():
    user = SimpleNamespace(role="manager")
    assert user_has_permission(user, "arrivals:confirm") is False
    assert user_has_permission(user, "schedule:confirm") is False


def test_dispatcher_matrix_matches_role_permissions():
    assert set(ROLE_PERMISSIONS["dispatcher"]) == set(PERMISSIONS) - {"admin:users"}

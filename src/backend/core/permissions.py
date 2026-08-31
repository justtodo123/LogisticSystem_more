"""Permission catalog and role mapping for R2-04B."""
from __future__ import annotations

from typing import Iterable

from models.user import User


PERMISSIONS: dict[str, str] = {
    "orders:read": "view orders",
    "orders:write": "create or edit orders",
    "orders:import": "import orders",
    "goods:read": "view goods",
    "goods:write": "edit goods",
    "schedule:read": "view schedules",
    "schedule:execute": "execute schedules",
    "schedule:confirm": "confirm schedules",
    "arrivals:confirm": "confirm arrivals",
    "vehicles:read": "view vehicles",
    "vehicles:write": "manage vehicles",
    "drivers:read": "view drivers",
    "drivers:write": "manage drivers",
    "nodes:read": "view nodes",
    "nodes:write": "manage nodes",
    "packages:read": "view packages",
    "packages:write": "repack packages",
    "exceptions:read": "view exceptions",
    "exceptions:write": "handle exceptions and replans",
    "simulation:write": "run simulation",
    "ai:use": "use AI assistant",
    "audit:read": "view audit logs",
    "export:read": "export reports",
    "reports:read": "view reports",
    "notifications:read": "view notification config",
    "notifications:write": "change notification config",
    "admin:users": "manage users",
}

WAREHOUSE_OPERATOR_PERMISSIONS: list[str] = [
    "orders:read",
    "orders:write",
    "orders:import",
    "goods:read",
    "packages:read",
    "nodes:read",
    "vehicles:read",
    "drivers:read",
    "reports:read",
    "notifications:read",
]

VIEWER_PERMISSIONS: list[str] = [
    "orders:read",
    "goods:read",
    "schedule:read",
    "vehicles:read",
    "drivers:read",
    "nodes:read",
    "packages:read",
    "exceptions:read",
    "reports:read",
    "notifications:read",
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": list(PERMISSIONS.keys()),
    "dispatcher": [perm for perm in PERMISSIONS if perm != "admin:users"],
    "viewer": VIEWER_PERMISSIONS,
    "warehouse_operator": WAREHOUSE_OPERATOR_PERMISSIONS,
    "manager": list(WAREHOUSE_OPERATOR_PERMISSIONS),
}

KNOWN_ROLES = frozenset(ROLE_PERMISSIONS)


def normalize_permissions(permissions: Iterable[str]) -> list[str]:
    return sorted(set(permissions))


def get_user_permissions(user: User) -> list[str]:
    return normalize_permissions(ROLE_PERMISSIONS.get(user.role, []))


def user_has_permission(user: User, permission: str) -> bool:
    return permission in get_user_permissions(user)

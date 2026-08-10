"""
权限控制模块

定义权限位、角色-权限映射。

FastAPI 权限依赖工厂（require_role / require_permission）
位于 api/dependencies.py 中，避免循环导入。
"""
from typing import List
from models.user import User


# ── 权限位定义 ──

PERMISSIONS: dict[str, str] = {
    "orders:read":       "查看订单",
    "orders:write":      "创建/编辑订单",
    "orders:import":     "批量导入订单",
    "schedule:read":     "查看调度方案",
    "schedule:execute":  "执行调度",
    "schedule:confirm":  "确认调度方案",
    "vehicles:read":     "查看车辆",
    "vehicles:write":    "管理车辆",
    "drivers:read":      "查看司机",
    "drivers:write":     "管理司机",
    "nodes:read":        "查看节点",
    "nodes:write":       "管理节点",
    "packages:read":     "查看包裹",
    "exceptions:read":   "查看异常",
    "exceptions:write":  "操作异常/重规划",
    "simulation:write":  "执行模拟",
    "ai:use":            "调用 AI 助手",
    "audit:read":        "查看审计日志",
    "admin:users":       "管理用户",
}


# ── 角色-权限映射 ──

ROLE_PERMISSIONS: dict[str, List[str]] = {
    "admin": list(PERMISSIONS.keys()),
    "dispatcher": [
        "orders:read", "orders:write", "orders:import",
        "schedule:read", "schedule:execute", "schedule:confirm",
        "vehicles:read", "vehicles:write",
        "drivers:read", "drivers:write",
        "nodes:read",
        "packages:read",
        "exceptions:read", "exceptions:write",
        "simulation:write",
        "ai:use",
        "audit:read",
    ],
    "viewer": [
        "orders:read", "schedule:read",
        "vehicles:read", "drivers:read",
        "nodes:read", "packages:read",
        "exceptions:read",
    ],
    "warehouse_operator": [
        "orders:read", "orders:write", "orders:import",
        "packages:read", "nodes:read",
        "vehicles:read", "drivers:read",
    ],
}


def get_user_permissions(user: User) -> List[str]:
    """获取用户的有效权限列表"""
    return ROLE_PERMISSIONS.get(user.role, [])

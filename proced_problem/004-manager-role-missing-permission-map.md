---
problem_id: "004"
slug: manager-role-missing-permission-map
date: 2026-08-14
tags: [rbac, permissions, seed-data, silent-failure, auth]
severity: critical
status: fixed
related_files:
  - src/backend/core/permissions.py
  - src/backend/scripts/init_users.py
  - src/backend/scripts/init_demo_data.py
related_pr: ""
---

# manager 角色在 ROLE_PERMISSIONS 无映射，仓库类操作全部 403

## 1. 症状（表现形式）

用 `manager` / `123456` 登录后，调用任何受 `require_permission` 保护的写端点，均返回 403：

| 操作 | 结果 |
| --- | --- |
| `manager` 创建订单（TC-011） | `code=40300` 无权限 |
| `manager` 查询审计日志（TC-076） | `code=40301` 无权限 |

实测权限数：

```
ROLE_PERMISSIONS keys = ['admin','dispatcher','viewer','warehouse_operator']
'manager' in keys -> False
manager perms (get_user_permissions) -> 0
warehouse_operator perms -> 7
```

文档/前端演示账号表声称 `manager` 可执行仓库相关操作，但实际权限数为 0。

## 2. 复现条件

1. `python scripts/init_users.py` 创建 `manager` 角色账号（`role="manager"`）
2. `manager` / `123456` 登录
3. 调用任意 `require_permission` 写端点
4. **稳定复现**——每次都 403

## 3. 定位过程

**Step 1 — 确认是"权限计算"而非"鉴权"问题**：`manager` 登录能拿到合法 JWT（`role=manager`），说明 `authenticate_user` 链路正常，问题在鉴权后的权限映射。

**Step 2 — 直读 `ROLE_PERMISSIONS` 键集合**：[permissions.py:40-65](../src/backend/core/permissions.py) 的 `ROLE_PERMISSIONS` 只有 `admin/dispatcher/viewer/warehouse_operator` 四个键，**没有 `manager`**。

**Step 3 — 定位权限计算兜底**：[permissions.py:70](../src/backend/core/permissions.py) `get_user_permissions` 走 `ROLE_PERMISSIONS.get(user.role, [])`，`manager` 命中默认空列表 → 0 权限。

**起初以为**：`manager` 与 `warehouse_operator` 可能是两个独立角色，只是权限没配全。**后来确认**：`init_users.py` 里 `manager` 分支的注释/文档语义就是"仓库管理员"，理应与 `warehouse_operator` 等价——是角色名不统一导致映射缺失。

## 4. 根因

`ROLE_PERMISSIONS` 缺少 `manager` 键，`get_user_permissions` 对 `manager` 返回空列表；而种子脚本用 `role="manager"` 创建账号，与权限体系里实际注册的角色名 `warehouse_operator` 不一致。

## 5. 解决方案

**状态：fixed（2026-08-17）**。实施方案 A：

- [permissions.py](../src/backend/core/permissions.py) 增加 `WAREHOUSE_OPERATOR_PERMISSIONS` 常量，`warehouse_operator` 和 `manager` 均引用该常量（避免两处漂移）。
- `get_user_permissions` 对 `manager` 返回 7 项权限（与 `warehouse_operator` 完全一致），不动种子/文档。

## 6. 验证

**已执行（2026-08-17）**：

```python
ROLE_PERMISSIONS keys = ['admin', 'dispatcher', 'viewer', 'warehouse_operator', 'manager']
manager perms (get_user_permissions) -> 7
warehouse_operator perms -> 7
manager == warehouse_operator -> True
```

全量 `pytest` → **635 passed**，0 failed。✅

## 7. 通用经验

1. **角色名是跨模块约定，必须先对齐再散开**：`ROLE_PERMISSIONS` 的键、种子脚本的 `role=`、前端演示账号表、文档四处必须用同一枚举；任一处分叉都会静默产出"能登录但 0 权限"的账号。
2. **`dict.get(key, [])` 的默认空列表是静默陷阱**：权限计算用 `.get(user.role, [])` 会把"未注册角色"与"无权限角色"混为一谈，都不会报错。建议对未注册角色打 warning 日志。
3. **权限测试要覆盖"每个种子角色跑一遍写端点"**：仅测 `admin/dispatcher` 会漏掉 `manager` 这类映射缺失。

---
problem_id: "001"
slug: seed-users-missing-admin
date: 2026-08-12
tags: [seed-data, init-script, docs-drift, silent-failure, auth]
severity: major
status: fixed
related_files:
  - src/backend/scripts/init_users.py
  - src/backend/scripts/init_demo_data.py
  - docs/06-启动说明.md
  - README.md
related_pr: ""
---

# 种子脚本缺失 admin 用户，文档声明的 admin/123456 登录失败

## 1. 症状（表现形式）

按 [docs/06-启动说明.md](../docs/06-启动说明.md) 完成初始化（`init_users.py` + `init_demo_data.py`）后，用文档声称的账号登录：

| 账号 | 结果 |
| --- | --- |
| `admin` / `123456` | **401 登录失败** |
| `dispatcher` / `123456` | 正常，JWT 签发成功 |
| `manager` / `123456` | 正常 |

README / [docs/06-启动说明.md](../docs/06-启动说明.md) 的"演示账号"表均声明 `admin` 为全权限管理员，但实测无法登录。整个初始化过程**无任何报错或警告**，脚本正常退出。

## 2. 复现条件

对全新 SQLite 数据库：

1. 运行 `python scripts/init_users.py`
2. 运行 `python scripts/init_demo_data.py`
3. 用 `admin` / `123456` 调用 `POST /api/auth/login`
4. **稳定复现**——每次都是 401

## 3. 定位过程

**Step 1 — 排除密码/BCrypt 链路问题**：
`dispatcher` / `123456` 登录成功，说明 `verify_password`（bcrypt.checkpw）链路正常，不是哈希算法或密码预处理问题。

**Step 2 — 直接查库确认账号是否存在**：
```sql
SELECT username, role, is_active FROM users;
-- 结果只有两行：('dispatcher','dispatcher',1) 和 ('manager','manager',1)
```
DB 中根本没有 `admin` 用户——登录失败是"账号不存在"，不是"密码错误"。

**Step 3 — 通读一次性种子脚本，排除 demo 脚本补建的可能**：
检查 [init_users.py](../src/backend/scripts/init_users.py)：第 28~51 行**只**创建 `dispatcher` 与 `manager`，无 `admin` 分支；[init_demo_data.py](../src/backend/scripts/init_demo_data.py) 同样只补这两个账号。

**Step 4 — 全局检索是否有人在别处建 admin**：
`grep -r "admin" src/backend/scripts/` → 无任何脚本创建 `role="admin"` 的用户。

**起初以为**：文档可能写的是计划中的账号，只是描述超前。**后来确认**：角色模型（[core/permissions.py](../src/backend/core/permissions.py)）中 `admin` 是真实存在且拥有全部权限的角色——只是没有种子账号实例化它。

## 4. 根因

初始化脚本（`init_users.py` / `init_demo_data.py`）漏建 `admin` 用户，且代码库中没有任何脚本创建该角色账号，与 README / docs/06 的演示账号说明不一致——文档描述了系统中并不存在的账号，且无报错掩盖了差异。

## 5. 解决方案

**状态：fixed（2026-08-13）**。已实施方案：

1. [init_users.py](../src/backend/scripts/init_users.py) 增加 `admin` 种子分支（`role="admin"`、`display_name="管理员"`、`is_active=True`，复用 `get_password_hash`），与 `dispatcher`/`manager` 并列 ✅
2. [init_demo_data.py](../src/backend/scripts/init_demo_data.py) 同步补建 admin（`_create_users` 加分支 + 清理过滤器 `username.in_` 加入 `"admin"`）✅
3. 核对 docs/06 与 README 演示账号表 → 文档**原本已含** admin 行，无需改动，仅代码缺失 ✅

## 6. 验证

**已执行（2026-08-14）**，真实验证输出：

1. 临时库验证（`DATABASE_URL` 指向临时目录 `verify_t01_lj6dr_vo/verify_t01.db`，验证后已删除）：
   - 重跑 `init_users.py` + `init_demo_data.py` → 输出 `创建admin账号`、`用户创建完成`
   - `SELECT count(*) FROM users WHERE role='admin'` → **1**（`username=admin, role=admin, is_active=True`）
   - `authenticate_user(db, "admin", "123456")` → 成功返回用户对象
   - JWT 解码 payload → `{'sub': 'admin', 'role': 'admin'}` ✅
2. 鉴权回归：`tests/api/test_arrival_confirm.py` + `tests/api/test_erp_webhook.py` → **15 passed**
3. 全量回归：`python -m pytest -q` → **635 passed**（原 626 + 新增 9 个鉴权用例）✅

## 7. 通用经验

1. **演示账号清单必须与种子脚本强一致**：文档声明的每个账号应在集成测试中逐一对 `users` 表断言存在，杜绝"文档超前于实现"。
2. **登录失败先查库再查码**：401 时第一步永远是 `SELECT * FROM users`，区分"账号不存在"与"密码错误"，能省掉一半排查时间。
3. **"能跑通无报错"不等于"行为符合预期"**：种子脚本是静默失败的典型温床——它不抛错，只产出与文档不符的数据。初始化后应做一次"按文档登录所有演示账号"的冒烟。
4. **角色模型与种子数据是两条线**：先确认权限体系里定义了 `admin` 角色，再确认有账号实例化它，两者缺一不可。

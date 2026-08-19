---
problem_id: "006"
slug: auth-expires-in-hardcoded
date: 2026-08-14
tags: [auth, jwt, config, docs-drift, frontend]
severity: major
status: fixed
related_files:
  - src/backend/api/auth.py
  - src/backend/config/settings.py
related_pr: ""
---

# auth 登录返回 expires_in 硬编码 86400，与实际 JWT 有效期 172800 不符

## 1. 症状（表现形式）

登录成功后返回的 `data.expires_in` 与 JWT 实际有效期错位 2 倍：

| 项 | 值 |
| --- | --- |
| 登录返回 `data.expires_in` | `86400`（24h） |
| JWT 实际 `exp`（由 `settings.JWT_EXPIRE_SECONDS` 计算） | `172800`（48h） |
| JWT payload | 仅 `sub/role/exp`，无 `iat` |

前端据此做提前刷新/过期提示会与实际有效期错位。

## 2. 复现条件

1. `POST /api/auth/login` 登录成功
2. 比对返回体 `expires_in` 与解码 JWT 的 `exp - 签发时刻`
3. **稳定复现**——每次 `expires_in` 都固定返回 `86400`

## 3. 定位过程

**Step 1 — 确认是"返回体"而非"签发逻辑"问题**：解码 JWT，`exp` 距签发为 172800s，说明 JWT 本身按 `settings.JWT_EXPIRE_SECONDS` 正确签发。

**Step 2 — 定位返回体取值来源**：[auth.py:59](../src/backend/api/auth.py) 直接写 `"expires_in": 86400`，是字面量，未从 settings 读取。

**Step 3 — 确认 settings 实际值**：dev `.env.dev` 下 `JWT_EXPIRE_SECONDS = 172800`（48h）。

**起初以为**：可能 JWT 签发也用了 86400，返回体是"如实反映"。**后来确认**：签发用的是 settings（172800），只有返回体是硬编码 86400，两者源头不一致。

## 4. 根因

`api/auth.py` 返回的 `expires_in` 未从 `settings.JWT_EXPIRE_SECONDS` 读取，而是硬编码字面量 `86400`，与 JWT 实际签发时长脱钩。

## 5. 解决方案

**状态：fixed（2026-08-17）**。

[auth.py:5](../src/backend/api/auth.py) 新增 `from config.database import get_db, settings`；[auth.py:59](../src/backend/api/auth.py) `"expires_in": 86400` → `"expires_in": settings.JWT_EXPIRE_SECONDS`。

## 6. 验证

**已执行（2026-08-17）**：

```python
from config.settings import settings
settings.JWT_EXPIRE_SECONDS -> 172800
```

全量 `pytest` → **635 passed**，0 failed。✅

## 7. 通用经验

1. **"有效期/阈值/默认值"这类常量不要在业务层重复声明**：签发时长只应有一个权威来源（settings），返回体直接引用它，避免两处漂移。
2. **"返回给前端的元数据"要和"后端实际行为"做一致性断言**：本例 JWT 签得对、返回体说得错，只在黑盒比对 `expires_in` vs 解码 `exp` 时才会暴露。

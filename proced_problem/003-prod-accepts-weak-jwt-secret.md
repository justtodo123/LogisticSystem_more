---
problem_id: "003"
slug: prod-accepts-weak-jwt-secret
date: 2026-08-14
tags: [security, jwt, config, silent-failure, fail-fast]
severity: major
status: fixed
related_files:
  - src/backend/config/settings.py
  - src/backend/config/database.py
  - docker-compose.yml
  - Dockerfile.backend
related_pr: ""
---

# 生产环境可用弱 JWT_SECRET 静默启动，JWT 可被伪造

## 1. 症状（表现形式）

`settings.JWT_SECRET` 有三个弱默认来源，且后端在非 dev 环境下**不会拒绝、只会警告（甚至不警告）**：

| 来源 | 弱值 | 触发环境 |
| --- | --- | --- |
| `config/settings.py:31` 字段默认值 | `default-secret-key-change-in-env` | 未设置任何 `JWT_SECRET` 时 |
| `docker-compose.yml:13` 兜底 | `change-me-in-prod` | compose 未注入 `JWT_SECRET` 时 |
| `Dockerfile.backend` | `ENV=prod` | 镜像直接 `docker run` 时 |

可观测后果：

- `Dockerfile.backend` 里 `ENV=prod`，但没有任何 `ENV JWT_SECRET`；直接 `docker run` 启动容器时，`ENV=prod` 落到 settings，`JWT_SECRET` 落回字段默认 `default-secret-key-change-in-env`——**生产进程用公开默认密钥签发/校验 JWT，攻击者可用同一密钥自签任意角色 token 直接冒充 admin**。
- 现有的"安全检查" [database.py:47-54](../src/backend/config/database.py) 只在 `JWT_SECRET == "default-secret-key-change-in-env"` 时 `warnings.warn`：① 它**只 warn 不 raise**，进程照常启动；② 它**漏掉**了 `change-me-in-prod`（compose 兜底）和 `dev-secret-key-do-not-use-in-production`（`.env.dev`）两个占位值；③ `RuntimeWarning` 默认不显示，生产日志里根本看不到。

即"生产环境静默跑在可伪造的 JWT 密钥上"，是一次静默的认证门禁失效。

## 2. 复现条件

只要以下条件同时成立，就能稳定复现：

1. `ENV=prod`（或 `staging`），例如直接 `docker run` 镜像（`Dockerfile.backend` 已设 `ENV=prod`）而不注入 `JWT_SECRET`；
2. `JWT_SECRET` 未显式设置，落回字段默认 `default-secret-key-change-in-env`，或落回 compose 兜底 `change-me-in-prod`；
3. 后端正常启动（不报错、不退出），`/api/health` 正常；
4. 用已知弱密钥本地签一个 `{sub, role: "admin", exp}` 的 HS256 JWT，调任意仅 admin 端点 → 200 通过权限校验。

## 3. 定位过程

**Step 1 — 追问"弱密钥到底有没有被拦住"**：上一轮排查 CI/CD（[002](002-cd-pushes-image-without-ci-gate.md)）时顺带发现 `settings.py:31` 的 `JWT_SECRET` 默认值是明文占位字符串。起初以为 `database.py:47-54` 的 `RuntimeWarning` 就是防线——后来细读发现它**只 warn**，且只匹配一个值。

**Step 2 — 枚举所有弱密钥入口**：用 `grep` 扫全仓 `JWT_SECRET`，发现三个弱来源（字段默认、compose 兜底、`.env.dev` 占位）加一个 `Dockerfile.backend` 的 `ENV=prod`。三者组合后，最危险的一条路径是 `docker run` 直接起镜像——`ENV=prod` + 无密钥注入 = 生产进程用默认密钥。

**Step 3 — 验证现有告警的覆盖盲区**：`database.py:48` 只判 `== "default-secret-key-change-in-env"`，而 compose 兜底是 `change-me-in-prod`、`.env.dev` 是 `dev-secret-key-do-not-use-in-production`——三个占位值，告警只覆盖一个。且 `RuntimeWarning` 默认被 Python 吞掉，不会进日志。

**Step 4 — 确认 fail-fast 的可行性与副作用**：打算在 `settings.py` 加 `model_validator` 拒绝弱密钥。需排除两个误伤：① Docker 镜像**构建期**不实例化 `Settings`（只 `pip install` + `COPY`），不会触发校验；② `docker-compose.yml` 设 `ENV: dev`，本地 demo 路径 `ENV=dev` 校验直接跳过。故只在真 `prod/staging` 环境 fail-fast，不影响构建与本地演示。

## 4. 根因

`settings.py` 对 `JWT_SECRET` 提供了一个公开可猜的**弱默认值**，而现有防线（`database.py` 的 `RuntimeWarning`）只 warn 不 raise、且只覆盖三个占位值中的一个，导致非 dev 环境缺少 fail-fast 的强校验。

## 5. 解决方案

在 [settings.py](../src/backend/config/settings.py) 增加第二个 `model_validator(mode="after")` `_validate_jwt_secret`：

1. `ENV == "dev"` 时直接放行（本地演示保留弱密钥降级自由）。
2. 非 dev 环境，`JWT_SECRET` 命中弱占位集合 `{"default-secret-key-change-in-env", "change-me-in-prod"}` **或** 长度 `< 32` 时，`raise ValueError`，进程启动即失败、给出明确错误信息。

不修改 `docker-compose.yml` / `Dockerfile.backend` / `database.py`：compose 兜底值保留（dev 演示仍可用），因为真 prod 一旦 `ENV=prod`，本校验会在兜底值上 fail-fast，恰好兜住；`database.py` 的 warn 与新校验在 dev 语义上不冲突，保留不动以最小化改动。

备选方案（未采用）：把所有弱值集中到 `database.py` 里判 `raise`——但 `database.py` 在 import 链中晚于 `settings` 实例化，密钥问题应在**配置加载时**就拦截，fail 得越早越好；`model_validator` 是 pydantic-settings 的原生钩子，位置更对。

## 6. 验证

| 维度 | 修复前 | 修复后 |
| --- | --- | --- |
| dev + 弱密钥 | 正常启动 | 正常启动（`ENV=dev` 放行，行为不变） |
| prod + 字段默认 `default-secret-key-change-in-env` | 静默启动（仅 warn） | `raise ValueError`，启动失败 |
| prod + compose 兜底 `change-me-in-prod` | 静默启动（无任何告警） | `raise ValueError`，启动失败 |
| prod + 长度 `< 32`（如 `short`） | 静默启动 | `raise ValueError`，启动失败 |
| prod + 32 位强密钥 | 正常启动 | 正常启动 |

实测（`PYTHONPATH=. python -c "from config.settings import Settings"`）：

```
dev weak secret: OK (no raise)
OK raise for 'default-secret-key-change-in-env'
OK raise for 'change-me-in-prod'
OK raise for 'short'
prod strong secret: OK
```

全量 `pytest` 通过（配置校验仅影响非 dev，测试环境均为 dev，无回归）。

## 7. 通用经验

1. **密钥/令牌默认值要"要么空、要么 fail-fast"，绝不能给一个可运行的弱占位**：给默认值等于给了一条"忘记配置也能跑"的静默路径。
2. **安全告警要 `raise` 不要 `warn`**：`RuntimeWarning` 默认被吞、不进日志，等于没有防线；凡是"生产必须改"的配置，用 fail-fast 让它改不了就起不来。
3. **校验要枚举所有占位值，且最好用"长度 + 命中集合"双条件**：单判一个字符串等于，会漏掉同类占位（本例三个弱值只覆盖一个）；长度下限能兜住一切"看得像占位"的短串。
4. **配置校验放在配置加载层（pydantic `model_validator`），不要放在 DB 初始化层**：`settings` 是所有模块的依赖根，在 import 时就失败，比跑到 `init_db` 再报更早、更彻底。
5. **改"启动即失败"类校验前，先排查构建期与降级路径**：确认 Docker 构建不实例化配置、dev/compose 演示路径不会被误伤，避免 fail-fast 变成 build-time 误杀。

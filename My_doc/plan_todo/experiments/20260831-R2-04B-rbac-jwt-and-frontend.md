# 20260831-R2-04B-rbac-jwt-and-frontend

## 元数据

- 计划 ID：R2-04B
- 计划/决策版本：D-R2-RBAC / D-R2-TOKEN；矩阵 v2026-08-31
- 日期与时区：2026-08-31 Asia/Shanghai
- 执行人：Codex
- 层级：P0 本机协议
- Git 分支：feat/R2-04B-rbac-jwt-and-frontend
- Commit SHA：尚无
- PR URL：尚无
- CI run URL：尚无

## Schema 与数据来源

- Alembic 当前 revision：r2_04b_token_version（父级 r2_03_replan_task_claims）
- 数据库来源：fresh in-memory SQLite（pytest create_all / Alembic 测试用 TEMP 目录）
- 数据是否为合成/脱敏数据：是

## 环境

- OS：Windows 11
- Python 3.13.3（src/backend/.venv）
- Node：本地 npm.cmd / vue-tsc / vite
- 数据库：SQLite in-memory StaticPool
- Redis：无
- worker 数：1（登录限流为进程内计数）

## 场景

- 角色矩阵允许/拒绝
- /me 权限集合
- logout / 禁用 / 改角色撤权
- 登录 expires_in 对齐
- 登录限流
- 前端 vue-tsc 与生产构建

## 命令

```text
cd src/backend
.\.venv\Scripts\python.exe -m pytest tests/api/test_token_revocation.py tests/api/test_permissions.py tests/api/test_login_rate_limit.py tests/api/test_rbac_matrix.py tests/api/test_arrival_confirm.py tests/api/test_export.py tests/api/test_notifications.py tests/api/test_erp_webhook.py tests/unit/core/test_permissions.py -p no:cacheprovider --tb=line -p no:warnings -q
# 97 passed in the focused suite that also included release_migrate setup errors outside TEMP; with TEMP redirected, release_migrate 3 passed.

cd ../frontend
npx.cmd vue-tsc --noEmit
npm.cmd run build
```

## 原始结果与产物

- 命令是否实际执行：是
- 聚焦 API/单元：token 撤权、权限矩阵、到货确认、导出、通知、ERP、限流均通过
- 前端：`vue-tsc --noEmit` 退出码 0；`npm run build` 生成 dist（2026-08-31 14:38:15）
- SQLite 限制：进程内登录限流；StaticPool 单连接不作为跨线程 token_version 证明
- 脱敏检查：已检查；无凭据入库

## 结论

- 状态：实现已在功能分支落地，计划卡保持 in_progress，待 PR/CI 后再标 done
- 下一步：按 Git 协作规范提交并创建 PR

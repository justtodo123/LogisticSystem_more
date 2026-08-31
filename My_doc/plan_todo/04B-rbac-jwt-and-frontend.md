---
plan_id: "R2-04B"
title: RBAC、JWT 撤权与前端权限
status: in_progress
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-31
depends_on: ["R2-00A", "R2-04A"]
---

# R2-04B — RBAC、JWT 撤权与前端权限

## 来源证据与当前行为

已定义 `PERMISSIONS`、`ROLE_PERMISSIONS` 和 `require_permission()`，但路由仍主要使用登录用户或 `require_dispatcher`。前端菜单、路由和按钮尚未全部由后端返回的权限集合驱动；access token 也缺少统一的 logout/禁用/改角色撤权版本机制。

决策基线：[D-R2-RBAC](./decisions.md)、[D-R2-TOKEN](./decisions.md)。错误响应与数据库会话统一复用 [R2-04A](./04A-error-contract-and-db-session.md)，本卡不再自建异常契约。

## 问题与目标

让权限定义、后端路由、`/me`、前端展示、ERP JWT 回退和测试使用同一事实源；以 `token_version` 支持 logout、禁用和角色变化后的旧 token 失效，并对未知角色 fail closed。

## 范围（P0）

- 敏感端点最小权限矩阵；到货确认仅 dispatcher/admin。
- 路由迁移到 `require_permission`；统一 active、角色与 ERP JWT 回退检查。
- `/me` 返回规范化权限集合；前端菜单、路由和按钮统一 `can(permission)`。
- access token + `user.token_version`；logout / 禁用 / 改角色后 version 增加，旧 token 被拒绝。
- 登录响应 `expires_in` 对齐 `settings.JWT_EXPIRE_SECONDS`。
- 登录限流与生产演示账号防护；未知角色默认拒绝。
- 角色矩阵、撤权、越权、限流与前端类型/构建测试。

## 非目标

- 不把前端隐藏按钮当作安全边界。
- 不实现 refresh token 家族。
- 不在本卡定义 `DomainError`、全局异常 envelope 或 `get_db` rollback；这些属于 R2-04A。
- 不把本卡绑定到 Docker / PostgreSQL 多 worker；跨 worker 限流和数据库拓扑验证在 R2-05。

## 依赖与进入条件

- R2-00A 已建立 schema revision 基线，`token_version` 等 schema 变更从唯一 head 派生。
- R2-04A 已提供错误码、统一 envelope 与数据库 Session 契约。
- 角色与到货确认授权已由 D-R2-RBAC 冻结。

## 有序实施步骤

1. 盘点全部非公开路由，生成角色 × 权限允许/拒绝矩阵；明确 AI、审计、导出、重规划和到货确认 owner。
2. 按领域逐路由替换仅登录/`require_dispatcher` 依赖为 `require_permission`，保留 active 与未知角色 fail-closed 检查。
3. 统一 `/me` 权限返回和 ERP JWT 回退；前端类型、store、路由守卫、菜单和按钮改用 `can(permission)`。
4. 基于 R2-00A 单一 head 增加 `token_version`；签发/验证 token 携带版本，logout、禁用、改角色在同一事务中递增。
5. 校准 `expires_in`；实现登录限流。P0 若使用进程内计数，必须标明单进程限制，并在 R2-05 复跑跨 worker 行为。
6. 参数化测试各角色、未知角色、过期/篡改/登出/禁用/角色变化、并发撤权、越权、限流和前端权限渲染。
7. 使用 R2-04A 的领域错误与 envelope，更新权限矩阵、API、前端和运维文档。

## 验收标准（P0）

- admin / dispatcher / viewer / manager / warehouse_operator 的允许/拒绝矩阵测试全绿；未知角色无权限。
- AI、审计、导出、重规划、到货确认符合最小权限；warehouse_operator / manager 不能执行到货确认写操作。
- `/me` 返回的权限与后端 `ROLE_PERMISSIONS` 一致；前端 `can()` 只影响体验，直接调用 API 仍由后端拒绝。
- logout、禁用、改角色或 token version 变化后旧 token 被拒绝；`expires_in` 与设置一致。
- 并发角色变化/登出不出现旧版本重新生效；审计可定位 actor 与动作。
- 登录限流边界有测试，P0 单进程限制被明确记录；错误响应符合 R2-04A 且不泄露认证细节。
- 前端类型检查和生产构建通过。

## P1 复跑（不阻塞本卡 done）

在 R2-05 的 PostgreSQL + Redis + 多 worker 环境复跑 token 撤权可见性、并发角色变化和登录限流；若 P0 使用进程内计数，不得声称跨 worker 生效。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/api tests/unit/core tests/unit/services -p no:cacheprovider
cd ../frontend
npx vue-tsc --noEmit
npm run build
```

## 文档与问题记录同步

同步权限矩阵、认证/API 文档、前端权限说明、演示账号与限流边界、第二轮 README；错误码只引用 R2-04A registry。

## 回滚与恢复

权限迁移逐路由可回滚，但始终 fail closed；发现越权立即恢复默认拒绝并保留审计，不以关闭鉴权作为回滚。`token_version` schema 回滚不得让已撤销 token 重新有效；必要时采用前向修复或强制全员版本提升。

## 完成记录

- 已在分支 `feat/R2-04B-rbac-jwt-and-frontend` 落地，状态仍为 in_progress（无 commit/PR/CI 不标 done）。
- 权限矩阵：[04B-rbac-permission-matrix.md](./04B-rbac-permission-matrix.md)
- 实验记录：[20260831-R2-04B-rbac-jwt-and-frontend.md](./experiments/20260831-R2-04B-rbac-jwt-and-frontend.md)
- Alembic head：`r2_04b_token_version`
- 本地聚焦测试：RBAC 矩阵 / 撤权 / 限流 / 到货 / 导出 / ERP 回退已通过；登录限流为进程内计数
- 前端：`npx.cmd vue-tsc --noEmit` 通过；`npm.cmd run build` 生成 dist
- Commit/PR/CI：尚无

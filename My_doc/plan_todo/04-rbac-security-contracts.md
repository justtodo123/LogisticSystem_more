---
plan_id: "R2-04"
title: RBAC、JWT 与统一错误契约
status: pending
priority: P1
owner: 待认领
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-00"]
---

# R2-04 — RBAC、JWT 与统一错误契约

## 来源证据与当前行为

项目已定义 `PERMISSIONS`、`ROLE_PERMISSIONS` 和 `require_permission()`，但参考路线图指出实际路由仍主要使用登录用户或 dispatcher/admin 两档。`docs/07-规范说明.md` 同时描述业务响应和 FastAPI `detail` 错误，领域服务、HTTP 异常和数据库依赖的退出行为尚未完全统一。

## 问题与目标

让权限定义、后端路由、前端权限展示、ERP JWT 回退和测试使用同一事实源；补足 token 生命周期、登录防护和领域异常/HTTP status/业务码/rollback 契约。

## 范围

- AI、审计、导出、重规划、到货确认等敏感端点的最小权限矩阵。
- `/me` 权限集合、前端 `can(permission)`、未知角色默认拒绝和 ERP 认证复用。
- access/refresh 或明确的短 token 方案、token version/jti、logout/撤权、issuer/audience、登录限流。
- `DomainError`、全局异常映射、通用异常脱敏、数据库异常/取消 rollback。

## 非目标

- 不把前端隐藏按钮当作安全边界。
- 若 refresh token 方案未获确认，先以短 access token + token version 交付并记录取舍，不伪称完整会话系统。

## 依赖与进入条件

- R2-00 完成；角色清单和敏感操作责任人确认。
- 明确 HTTP 语义与现有 `code/message/data/meta` 响应的兼容策略。

## 有序实施步骤

1. 盘点所有非公开路由的依赖，生成角色×权限允许/拒绝矩阵。
2. 将路由从粗粒度角色迁移到权限依赖；统一 ERP JWT、active 检查和撤权逻辑。
3. 前端从 `/me` 读取权限，菜单、路由和按钮统一 `can()`；未知权限 fail closed。
4. 增加 token claim、限流、失败次数、撤销/版本策略和生产演示账号防护。
5. 建立领域异常层和全局处理器，统一 HTTP status、业务 code、对外 message、日志 traceback 与 rollback。
6. 参数化测试每个角色、过期/篡改/登出/角色变化、越权、限流和异常分支。

## 验收标准

- admin、dispatcher、viewer、manager、warehouse_operator 的允许/拒绝矩阵自动测试全绿；未知角色无权。
- AI、审计、导出、重规划、到货确认均符合最小权限；前后端展示与后端结果一致。
- 禁用用户、角色变更、logout 或 token version 变化后旧 token 行为符合书面策略。
- 4xx/5xx、业务错误和数据库 rollback 可预测，内部 SQL/第三方响应不泄漏。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/api tests/unit/core tests/unit/services
python -m pytest -q -p no:cacheprovider
cd ../frontend
npx vue-tsc --noEmit
npm run build
```

## 文档与问题记录同步

同步 `docs/07-规范说明.md`、API 文档、前端权限说明、错误码表和第二轮 README；非平凡安全问题按 `proced_problem` 记录。

## 回滚与恢复

权限迁移采用逐路由可回滚清单；错误契约切换保留兼容期。发现越权时立即恢复默认拒绝并保留审计日志，不以关闭鉴权作为回滚。

## 完成记录

- 尚未开始。完成时填写权限矩阵版本、token 策略、测试结果、Commit/PR 和兼容期限。

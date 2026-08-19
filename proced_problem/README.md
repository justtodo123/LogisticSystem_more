# 问题记录库（proced_problem/）

> 记录项目开发中实际遇到的问题：症状、定位过程、根因与修复。目的是积累工程直觉，可复盘、可检索。

## 为什么叫"proced_problem"

"proced" = **Pro**blem **Rec**ord**ed** — 每一个被踩过、定位出来的问题，而不是未发生的理论风险。已经过一遍完整的问题解决闭环。

## 目录结构

```
proced_problem/
├── README.md              # 本导航文件
├── _template.md            # 记录模板
└── {序号}-{简短slug}.md    # 单条问题记录
```

## 记录列表

| 序号 | 标题 | 日期 | 标签 |
| --- | --- | --- | --- |
| 001 | [种子脚本缺失 admin 用户，文档声明的 admin/123456 登录失败](001-seed-users-missing-admin.md) | 2026-08-12 | seed-data, init-script, docs-drift, silent-failure, auth |
| 002 | [CD 工作流绕过 CI 直接推送镜像，未通过测试的代码也会发布](002-cd-pushes-image-without-ci-gate.md) | 2026-08-14 | ci-cd, github-actions, workflow, supply-chain, silent-gate |
| 003 | [生产环境可用弱 JWT_SECRET 静默启动，JWT 可被伪造](003-prod-accepts-weak-jwt-secret.md) | 2026-08-14 | security, jwt, config, silent-failure, fail-fast |
| 004 | [manager 角色在 ROLE_PERMISSIONS 无映射，仓库类操作全部 403](004-manager-role-missing-permission-map.md) | 2026-08-14 | rbac, permissions, seed-data, silent-failure, auth |
| 005 | [种子订单状态枚举漂移（pending vs unassigned），核心调度链路在演示数据上不可用](005-seed-order-status-enum-drift.md) | 2026-08-14 | seed-data, state-machine, enum-drift, silent-failure, scheduling |
| 006 | [auth 登录返回 expires_in 硬编码 86400，与实际 JWT 有效期 172800 不符](006-auth-expires-in-hardcoded.md) | 2026-08-14 | auth, jwt, config, docs-drift, frontend |
| 007 | [OrderCreate schema 未校验 time_window 合法性，非法时间窗直接入库](007-ordercreate-time-window-unvalidated.md) | 2026-08-14 | validation, pydantic, schema, boundary, scheduling |
| 008 | [algorithm="deepseek" 未实现，策略工厂仅注册 greedy/dummy](008-deepseek-algorithm-not-implemented.md) | 2026-08-14 | algorithm, strategy-pattern, factory, docs-drift, ai |
| 009 | [schedule_service 残留 DEBUG/ERROR print 语句，内部状态泄漏到 stdout](009-residual-debug-print.md) | 2026-08-14 | logging, code-hygiene, print, observability |
| 010 | [已送达货物在 AI 重规划中被打回 pending_pack](010-delivered-goods-reset-on-replan.md) | 2026-08-19 | state-machine, replan, delivered, data-integrity |
| 011 | [CI 空仓库下 SQLite 无法打开 data/logistics.db](011-sqlite-missing-data-dir-breaks-ci.md) | 2026-08-19 | ci, sqlite, test-isolation, startup |

## 如何新增记录

1. 复制 `_template.md`，按 `{序号}-{slug}.md` 命名
2. 填写各章节：症状 → 定位过程 → 根因 → 修复 → 验证 → 经验
3. 更新本 README 的记录列表
4. 触发方式：手动编写，或用 `problem-record` skill 辅助模板填写

## 关联

- 项目理解说明：[CLAUDE.md](../.claude/CLAUDE.md)
- 优化点与已知边界：[docs/08-优化点说明.md](../docs/08-优化点说明.md)

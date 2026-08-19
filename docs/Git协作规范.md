# Git 协作规范

> 最后更新：2026-08-19（实时状态改指 plan_todo）

## 远程仓库

| 地址 | `https://github.com/justtodo123/LogisticSystem_more` |
|------|------|

## 分支策略

- **`main`** — 受保护分支，始终保持可构建、可运行、测试全绿
- **`feat/Tx-x`** — 功能/任务分支（如 `feat/T4-3`），从 main 分出，合并回 main
- 禁止直接向 main 推送，通过 Pull Request 合并

## 提交规范

遵循 Conventional Commits：

```
<type>: <描述>

Co-Authored-By: Claude <noreply@anthropic.com>
```

| type | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: T4-3 Redis 缓存层` |
| `fix` | 修复 | `fix: 修正幂等缓存 Bug` |
| `refactor` | 重构 | `refactor: 策略模式工厂扩展` |
| `test` | 测试 | `test: 补充 AI 输出校验测试` |
| `docs` | 文档 | `docs: 更新部署说明` |

## 任务开发流程

1. 从 `main` 拉取最新代码
2. 创建任务分支：`git checkout -b feat/Tx-x`
3. 开发和测试（保证已有测试不回归）
4. 更新 [plan_todo/README.md](../My_doc/plan_todo/README.md) 与对应计划卡状态
5. 提交并推送分支
6. 合并到 `main` 后删除分支

## Code Review 要点

- API 端点是否有适当的鉴权依赖（`get_current_user` / `require_dispatcher`）
- 服务层函数是否全部 `async def`
- 数据库操作是否使用参数化查询（防 SQL 注入）
- 新增模型是否有对应迁移脚本
- 新增端点是否有测试覆盖

## 文档维护

- 功能变更后同步更新 `docs/` 下对应文档
- 任务进度实时记录到 `My_doc/plan_todo/README.md` 与对应计划卡；已完成的旧计划只保留在 `My_doc/post_plan/`
- 历史文档归档到 `docs/history/`，不在 `docs/` 根目录分散

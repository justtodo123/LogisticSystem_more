# Git 协作规范

> 最后更新：2026-08-25（My_doc 正式追踪与证据治理）

## 远程仓库

| 地址 | `https://github.com/justtodo123/LogisticSystem_more` |
|------|------|

## 分支策略

- **`main`** — 受保护分支，始终保持可构建、可运行、测试全绿
- **`feat/Tx-x` / `feat/R2-xx-<slug>`** — 功能/任务分支（如 `feat/T4-3`、`feat/R2-01-cas-state-transitions`），从 main 分出，合并回 main
- **`feat/docs-<topic>`** — 跨计划卡的纯文档/治理分支（如 `feat/docs-r2-governance`）
- 禁止直接向 main 推送，通过 Pull Request 合并
- 创建分支前如工作区已有用户修改，必须先核对并原样保留；不得用 `reset --hard`、`restore`、`clean` 或未经确认的 stash 覆盖

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

1. 从 `main` 拉取最新代码并确认 `git status --short --branch`
2. 创建任务分支：`git checkout -b feat/R2-xx-<slug>`；纯文档治理使用 `feat/docs-<topic>`
3. 开发和测试（保证已有测试不回归）
4. 更新 [plan_todo/README.md](../My_doc/plan_todo/README.md) 与对应计划卡状态；实验按模板记录
5. 提交前执行范围、忽略规则、敏感内容与 `git diff --check` 检查
6. 提交并推送分支，经 Pull Request 合并
7. 合并到 `main` 后删除分支

## Code Review 要点

- API 端点是否有适当的鉴权依赖（`get_current_user` / `require_dispatcher`）
- 服务层函数是否全部 `async def`
- 数据库操作是否使用参数化查询（防 SQL 注入）
- 新增模型是否有对应迁移脚本
- 新增端点是否有测试覆盖

## 文档维护

- 功能变更后同步更新 `docs/` 下对应文档。
- `My_doc/` 已正式纳入 Git 追踪：任务进度实时记录到 `My_doc/plan_todo/README.md` 与对应计划卡；版本化决策在 `decisions.md`；已完成旧计划只保留在 `My_doc/post_plan/`。
- 根 `.gitignore` 与 `My_doc/.gitignore` 共同排除 `.env`、数据库、依赖目录、日志、预览、原始 CI 输出、待脱敏 Office 二进制、可再生成的历史演示输出及实验 `raw/` / `artifacts/` / `tmp/`。大型原始结果放 CI artifact 或受控外部存储，报告登记位置、大小、SHA-256、脱敏和保留期限。
- 解除忽略后先运行 `git ls-files --others --exclude-standard My_doc` 并分类审查；禁止在未审查候选、二进制和秘密前直接 `git add -A`。
- 完成记录只能填写真实存在的 commit SHA、PR URL、CI run、命令退出码和实验产物；禁止提前写“工作区干净”“已提交”“已合并”或“测试已通过”。
- 历史文档归档到 `docs/history/` 或 `My_doc/post_plan/`，不把历史“当前状态”计入实时待办。

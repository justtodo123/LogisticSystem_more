# My_doc 文档索引

> **用途**：本目录是仓库正式追踪的治理、计划、交付、历史和实验索引；现行计划入口为 [plan_todo/README.md](plan_todo/README.md)，项目交付与面试展示入口为 [delivery/README.md](delivery/README.md)。运行时产物、凭据、依赖目录和大型原始实验结果仍按根目录与 [My_doc/.gitignore](.gitignore) 排除，不把“文件可见”当成“实验已通过”。
> **事实日期**：2026-09-04

## 阅读顺序

1. 先读 [plan_todo/README.md](plan_todo/README.md)，确认当前活动计划与验证边界。
2. 再读 [plan_todo/decisions.md](plan_todo/decisions.md)，确认冻结协议和版本化治理决策。
3. 按依赖阅读 R2-00、R2-00A、R2-04A，再读 R2-01～03、R2-04B、R2-05～06。
4. 实验报告只在 [plan_todo/experiments/](plan_todo/experiments/) 中作为证据索引；大型或敏感原始产物看报告登记的 CI artifact/受控外部位置。
5. `post_plan/`、`pre-optimization/`、`test/` 是历史资料，不能覆盖现行计划状态；项目公开规范仍以仓库 `docs/` 和代码/验证证据为准。

## 目录结构

| 路径 | 角色 | 时效/追踪边界 |
|------|------|------|
| [plan_todo/](plan_todo/README.md) | 当前活动路线图、冻结决策、实验模板与计划卡 | **现行；R2-00～R2-06 已完成，生产验证与 P2 见 post-r2-followups.md** |
| [delivery/](delivery/README.md) | 当前项目交付与面试展示材料 | **现行；事实、证据、架构、STAR、演示和 PPT 提纲** |
| [post_plan/](post_plan/TASK_TRACKER.md) | 已执行完成的优化周期计划 | 历史快照；不承担当前待办 |
| [pre-optimization/](pre-optimization/) | MVP / P1 / 阶段 1～9 旧开发与联调材料 | 历史材料；依赖目录、可再生成 PPT/SVG 输出及待脱敏 Office 二进制不追踪 |
| [test/](test/) | 黑盒回归记录 | 历史证据；不得冒充当前 P0/P1 证明 |
| [reference/](reference/) | 路线图和外部参考摘要 | 参考资料；运行日志、原始 CI 输出和原始大产物忽略 |

## 当前治理状态

- `R2-00`～`R2-06` 已于 2026-09-04 完成工程交付；最终文档冻结点为 `main @ df025fb`（PR #42）。
- P0/P1 协议实现、PostgreSQL + Redis + 多 worker 验证、容量/soak 证据和镜像发布门禁均已收口；不可变镜像验收基线为 `f9e08a4` / CD [33826520856](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33826520856)，零 exception。
- 本机未执行 Docker Compose、第一轮 02B E2E、预发或生产拉起；这些生产验证以及可选 P2 增强统一登记在 [post-r2-followups.md](plan_todo/post-r2-followups.md)，不作为 R2 阻断项。
- 原 R2-04 已拆为 [R2-04B](plan_todo/04B-rbac-jwt-and-frontend.md)，只负责 RBAC、JWT 撤权和前端权限。

## 追踪和安全规则

- 提交前审查 `git ls-files --others --exclude-standard My_doc`，禁止 `git add -A` 未经分类审查。
- 不追踪 `.env`、口令/令牌/私钥、数据库副本、cookie、未脱敏个人数据、`node_modules/`、日志、预览、压测 raw 和大型生成文件。
- 实验报告记录命令、退出码、环境、数据量、branch/commit/PR、schema revision、产物大小/hash、脱敏检查、外部位置和保留策略。
- 发现历史文档中的 demo 账号或已脱敏示例时必须明确“仅 disposable/non-production”；不把示例值当成可用凭据。

## 维护规则

- 只在 [plan_todo/](plan_todo/README.md) 维护实时完成率；`blocked` / `needs_decision` / `mitigated` 不计为 `done`。
- 已完成计划移入 `post_plan/`，顶部保留历史标识和回链，不改写原文结论。
- 文档与代码冲突时，以当前代码和带日期的验证证据为准；新证据必须通过版本化决策或计划记录纳入。
- 每次小目标按 [Git 协作规范](../docs/Git协作规范.md) 使用独立分支和真实证据提交；未经用户明确授权不自动发布。

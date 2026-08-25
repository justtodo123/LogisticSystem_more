---
plan_id: "R2-00"
title: 第二轮执行治理与证据基线
status: in_progress
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-25
depends_on: []
---

# R2-00 — 第二轮执行治理与证据基线

## 来源证据与当前行为

- 第一轮已建立计划状态、历史归档和证据规则，原文见[第一轮执行治理](../post_plan/第一轮优化计划/00-execution-governance.md)。
- 2026-08-25 评审：原第二轮卡片把 PostgreSQL/Docker/多 worker 写进 P0 验收，但本机无 Docker/WSL/PostgreSQL/Redis，第一轮 02B 仍为 `mitigated`。按原卡执行会立刻 `blocked`。
- 协议决策见 [decisions.md](./decisions.md)；本轮治理修订正在把该文件与实验模板正式纳入 Git 追踪。
- 当前工作位于独立文档分支 `feat/docs-r2-governance`。分支创建时已有 00～06 与本 README 共 8 个未提交修改，均原样保留；不得写成“工作区干净”或“已提交”。

## 问题与目标

为第二轮建立可审计的任务、环境、实验和发布基线；把“本机可证明的协议”和“外部拓扑证明”拆开，使 P0 可立即开工。先补齐迁移与错误契约前置卡，再进入业务实现。

## 范围

- 第一轮归档与第二轮实时计划的边界；任务 ID、依赖、分支、提交和 owner。
- `My_doc/` 正式追踪边界，以及预览、依赖目录、实验大产物和运行日志的排除规则。
- P0 / P1 环境定义、数据规模、并发客户端和故障注入点登记规则。
- 实验摘要、外部原始产物、哈希、脱敏、回滚和 `blocked`/`needs_decision` 规则。
- 冻结并发冲突、幂等、编号、Saga、token、错误契约、RBAC、观测裁剪。
- 增设 R2-00A（迁移基线）与 R2-04A（错误契约/数据库会话），原 R2-04 收窄为 R2-04B。

## 非目标

- 不在本卡修改业务代码、生成 Alembic revision、升级数据库或宣称 PostgreSQL、Docker、压测通过。
- 不重写第一轮历史结论。
- 不在没有真实证据时预填 commit、PR、合并或测试通过记录。

## 依赖与进入条件

- 无。本卡是第二轮治理入口。

## 有序实施步骤

1. 保护已有工作区修改，在独立 docs 分支记录分支、HEAD、本机软件缺口和第一轮未验证项。
2. 移除根目录对整个 `My_doc/` 的忽略，建立 `My_doc/.gitignore`，盘点并审查全部新增追踪候选。
3. 版本化补充 P0/P1、文档追踪、迁移和错误兼容决策，不静默改写冻结语义。
4. 完善 `experiments/` 规则与模板；小型脱敏摘要可追踪，大型/敏感原始产物保存到 CI artifact 或受控外部存储并登记哈希。
5. 新增 R2-00A、R2-04A，将原 R2-04 拆为 R2-04B；同步 01～06 的依赖和链接。
6. 验证任务 ID 唯一、依赖无环、链接存在、Git 忽略边界正确且 diff 仅含治理文档。
7. 展示 diff；经授权后再分批 commit/push/创建 PR。只有真实证据产生并回填后才关闭本卡。

## 验收标准

- 9 张第二轮计划卡均有唯一 ID、owner、依赖、进入条件、验收和回滚；依赖图无环。
- README 是第二轮唯一实时聚合入口；[decisions.md](./decisions.md) 为版本化协议事实源。
- `decisions.md`、`experiments/README.md`、`experiments/_template.md` 可被 Git 发现；`node_modules`、预览、数据库、日志、实验 `raw/`/`artifacts/`/`tmp/` 仍被忽略。
- 实验报告能记录分支/commit/PR、计划版本、schema revision、fresh/legacy 数据库、环境、数据规模、worker、结果、产物位置/大小/hash、脱敏和保留策略。
- 未就绪的 Docker/PostgreSQL/Redis/压测标为 P1 `blocked`/`pending`，不阻塞 P0。
- 计划交叉引用无旧 R2-04 文件名或错误依赖；正常发布完成记录只引用真实 SHA、PR URL 与验证产物。

## 验证命令

```bash
git status --short --branch
git diff --check
git ls-files --others --exclude-standard My_doc
git check-ignore -v My_doc/README.md.preview.txt My_doc/pre-optimization/ppt/node_modules/pptxgenjs/package.json
```

只读核对迁移现状可运行 `alembic heads` / `alembic history`；本卡禁止执行 `upgrade`、`downgrade` 或写数据库。

## 文档与问题记录同步

同步本 README、decisions、experiments 模板、各卡 frontmatter、[My_doc 索引](../README.md)与 [Git 协作规范](../../docs/Git协作规范.md)。

## 回滚与恢复

治理文件误改时逐文件核对后恢复；不得删除第一轮归档或覆盖分支创建前的 8 个用户修改。无法确认的环境结果保持 `blocked`/`pending`。追踪范围回滚也必须继续保护凭据、数据库、依赖目录和大型原始产物。

## 进展记录

- 日期：2026-08-25
- 负责人：justtodo123
- 起始基线：`main` @ `85938d72e8a5951e55863795733e7a4355325c46`
- 工作分支：`feat/docs-r2-governance`
- 分支创建时工作区：00～06 与计划 README 共 8 个未提交修改；已保留
- 本机：Win11 家庭版，Ryzen 7 7840H 8C/16T，16GB；Python 3.13.3；Node v24.12.0；Git 2.49
- 缺口：Docker / Compose / WSL / PostgreSQL / Redis / k6 / Locust 均未安装；内存空闲曾约 1.6GB
- 当前决策基线：`v2026-08-25-r2-freeze`；治理增补版本待本次文档变更完成
- Commit/PR：尚无；不得提前填写
- 下一动作：完成治理 diff 与验证；之后 R2-00A、R2-04A 可并行实施

## 完成记录

- 状态：`in_progress`
- 关闭条件：独立 docs 分支的真实 commit/PR、追踪边界验证和计划一致性验证均已回填后，另行把本卡改为 `done`。

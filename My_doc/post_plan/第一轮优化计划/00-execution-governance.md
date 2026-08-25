---
plan_id: "00"
title: 执行治理与路线图维护
status: done
priority: P0
owner: 待认领
created: 2026-08-18
updated: 2026-08-19
depends_on: []
---

# 00 — 执行治理与路线图维护

## 来源证据与当前行为

- [Git 协作规范](../../docs/Git协作规范.md)要求任务分支、Conventional Commits、代码与文档同步。
- 当前活动路线图及唯一实时状态聚合入口为 [README](./README.md)；计划卡是任务级状态源，旧 T-01～T-13、`TASK_TRACKER` 和旧计划仅作为历史执行证据保留。
- 2026-08-19 既有验证基线：后端 `635 passed, 196 warnings`，前端类型检查及生产构建通过；该记录不是本计划重新执行的结果。本机没有 Docker 和 `gh`。
- 工作区已有 [order.py](../../src/backend/schemas/order.py) 伪修改：索引与工作树内容哈希相同。它不属于路线图文档变更。

## 问题与目标

建立统一的任务顺序、状态、证据和收尾规则，避免“测试通过即宣称完成”、跨阶段混合提交、覆盖他人改动或文档再次漂移。

## 范围

- 规定计划状态、依赖门禁、分支/提交、验证证据和 README 更新方式。
- 规定源代码、测试、文档和问题记录的完成条件。
- 规定中断恢复、失败回滚及外部环境阻塞的记录方式。

## 非目标

- 本计划不直接修复业务代码。
- 不把历史报告改写成当前事实。
- 不在缺少 Docker、GitHub 或 GHCR 证据时宣称远端验收成功。

## 依赖与进入条件

无；所有其他计划均受本计划约束。[00A 文档基线校准与状态源治理](./00A-documentation-baseline-and-source-governance.md)负责把本计划的文档规则落实为第一个实际工作包。

## 事实与文档优先级

发生文档冲突时，依次核对：**当前代码与实际验证证据 → 已批准的当前规范/决策记录 → 实时路线图 → 历史快照**。业务语义仍未决定时不得自行推断，应使用 `needs_decision` 并链接决策记录。

- 当前事实必须注明适用日期；测试、Docker、远端和数据迁移结果还必须注明命令、目录/环境及 Commit/PR（如有）。
- 历史里程碑保留当时的数字与结论，并明确日期和“历史快照”属性，不覆盖为当前事实。
- 文件或配置存在只能证明已实现/已配置，不能替代构建、启动、E2E 或外部环境验证。
- 历史文件不得继续自称实时 tracker；状态聚合统一回写 [README](./README.md)。

## 有序实施步骤

1. 开始任何任务前记录 `git status --short`、当前分支及目标文件；保护所有既有非目标改动。
2. 按 [Git 协作规范](../../docs/Git协作规范.md)从当前已确认基线建立任务分支，不直接在 `main` 上形成新提交。
3. 将计划状态按 `pending → in_progress → done` 推进；外部环境不可用时用 `blocked`，契约待定时用 `needs_decision`，仅短期缓解时用 `mitigated`。
4. 一次只推进一个可验收的小目标。实现、对应测试、当前文档和问题记录放在同一阶段提交中。
5. 只显式暂存本任务文件；禁止使用可能吸收无关改动的全量暂存。
6. 先跑定向测试，再跑受影响层级的完整回归；失败必须原样记录，不得填写完成记录。
7. 非平凡故障按 `proced_problem` 模板记录；已有记录则更新原记录，避免重复。
8. 任务完成后填写计划末尾的真实日期、commit/PR、验证命令及结果，同时更新 [README](./README.md) 状态。
9. 文档变更须检查链接、状态和事实日期；同一当前事实不得保留多个无日期版本，未验证能力不得用完成式措辞。[00A](./00A-documentation-baseline-and-source-governance.md)完成前，依赖它的 01 不得推进为 `done`。
10. 阶段中断时在计划中写明最后完成步骤、失败输出、下一条命令和未提交文件。

## 验收标准

- 每个计划都有负责人、依赖、进入条件、可量化验收和真实完成记录。
- 依赖未完成的任务不得标记 `done`。
- 每个行为变更都有回归测试；每个公开契约变更都有前后端及当前文档同步。
- Git diff 不包含开始任务前已存在的非目标改动。
- 本地未执行的 Docker/远端步骤明确标为 blocked 或待验证。
- 当前文档链接有效、状态与计划卡一致，同一当前事实有日期和单一来源；历史数字保留时间语境。
- `blocked`、`needs_decision` 和 `mitigated` 不得计入 `done`。

## 验证命令

```bash
git status --short
git branch --show-current
git diff --check
git diff --name-status
```

按任务补充定向测试，并在发布关口执行：

```bash
cd src/backend && python -m pytest -q -p no:cacheprovider
cd src/frontend && npm run build
```

## 文档与问题记录同步

- 每个状态变化同步唯一实时聚合入口 [README](./README.md)。
- 行为/契约变化同步 `docs/` 当前文档；历史目录只添加历史标识、日期语境和当前入口链接，不改写原结论。
- 文档基线、分类和冲突清单按 [00A](./00A-documentation-baseline-and-source-governance.md)维护。
- 只有完成非平凡排查后才新增 `proced_problem`；已有问题优先更新状态和验证证据。

## 回滚与恢复

- 代码失败：恢复本任务提交或在任务分支修复，不触碰基线前的用户改动。
- 数据迁移失败：执行具体业务计划中预先验证的回滚脚本/备份恢复。
- 外部验证失败：保留日志和 SHA，状态改为 `blocked`，不以本地结果替代。

## 完成记录

- 完成日期：2026-08-19
- 负责人：待认领（规则已采用，不补虚拟 owner）
- Commit / PR：无独立业务提交。本计划不修代码；规则以本卡为准被采用。
- 验证结果：`git branch --show-current` = `main`；`git status --short` 在开始时已有 `src/backend/schemas/order.py` 伪修改与 `.serena/memories/`，本计划未触碰。
- 遗留事项：文档基线校准交 [00A](./00A-documentation-baseline-and-source-governance.md)；业务缺口仍由 01～05 处理。本卡规则对后续任务持续生效。

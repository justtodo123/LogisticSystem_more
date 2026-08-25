---
plan_id: "03"
title: 前后端订单六态契约统一
status: done
priority: P1
owner: 待认领
created: 2026-08-18
updated: 2026-08-19
depends_on: ["00", "01"]
---

# 03 — 前后端订单六态契约统一

## 来源证据与当前行为

开始时：后端已是六态，前端/Mock 仍为旧四态，TypeScript 无法发现真实 API 漂移。

2026-08-19 完成后：

- 权威字典： [order_status.py](../../src/backend/core/order_status.py) 与 [ORDER_TRANSITIONS](../../src/backend/services/state_machine.py#L42-L49)
- 前端： [order.ts](../../src/frontend/src/types/order.ts) / [status.ts](../../src/frontend/src/constants/status.ts) 使用同一组六态；未知值显示为「未知状态（raw）」
- 契约测试：`tests/unit/core/test_order_status.py` 读取前端源文件，防止再次漂移

## 问题与目标

建立一个端到端权威订单状态契约，使数据库、后端状态机、API、前端、Mock、种子和文档使用同一语义，并为历史非法值提供可审计的兼容/回填方案。

## 范围

- 后端状态常量、Schema/API 示例、种子和迁移检查。
- 前端类型、标签、筛选、表格、详情、模拟、异常和 Mock。
- 状态转换与聚合契约测试。

## 非目标

- 不合并订单、货物、包裹三类不同状态机。
- 不引入未经业务确认的新订单状态。
- 不静默把未知值显示成合法状态。

## 依赖与进入条件

- [01](./01-delivered-goods-replan-integrity.md)确定终态与重规划不变量。
- 确认 `signed` 与 `closed` 的业务差异及何时推进。

## 有序实施步骤

1. 形成状态字典：英文值、中文标签、允许来源/目标、终态、异常恢复语义。
2. 搜索数据库模型、状态机、服务筛选、Schema、种子、迁移、测试和文档中的所有订单状态字符串。
3. 将后端权威值提取/复用到校验和响应层，拒绝未知新值；保持错误码规范。
4. 设计历史值映射：至少评估 `pending→unassigned`、`delivering→in_transit`、`completed→signed/closed`；歧义值必须先报告再迁移。
5. 更新前端 `OrderStatus`、状态映射、筛选、徽标、详情、操作按钮及异常/模拟流程。
6. 更新所有 Mock 与本地存储数据；为旧缓存加一次性兼容或明确清理版本。
7. 增加 API 契约测试与前端类型/组件测试，覆盖六态及未知状态显示。
8. 在全新种子库运行完整调度和签收流程，确认状态按规则推进。
9. 更新当前功能、状态机、API 和演示文档。

## 验收标准

- 前后端、种子、Mock 和当前文档只使用同一组六态值。
- 每条允许/禁止转换均有测试；未知状态不会被静默映射。
- 旧数据迁移可重复、可审计，迁移前后数量一致。
- 列表筛选、详情标签和操作权限在六态下正确。
- 真实后端 + 前端完成一条订单生命周期冒烟。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services/test_state_machine.py tests/api/test_orders.py
python -m pytest -q tests/integration/test_schedule_pipeline.py tests/integration/test_simulation_pipeline.py
python -m pytest -q -p no:cacheprovider
```

```bash
cd src/frontend
npx vue-tsc --noEmit
npm run build
```

另在临时数据库执行迁移 dry-run 和状态分布查询。

## 文档与问题记录同步

- 更新当前订单状态机、API 示例、前端演示及种子说明。
- 关联已修复的 [问题 005](../../proced_problem/005-seed-order-status-enum-drift.md)，如发现新的前后端契约根因则单独记录。
- 完成后更新 [README](./README.md)。

## 回滚与恢复

先备份/导出状态分布再迁移。前端和后端契约应同版本发布；若一侧失败，回滚整组变更，不保留半兼容状态。

## 完成记录

- 完成日期：2026-08-19
- 负责人：待认领
- 契约版本/决策：`2026-08-19-six-state`。`signed`=全部货物送达，仍可转 `exception`；`closed`=未完成即关闭，硬终态。历史回填 `pending→unassigned`、`delivering→in_transit`、`completed→signed`（不把 `completed` 推断为 `closed`）。未知值拒绝筛选且不静默映射。
- Commit / PR：62942c0 on eat/01-delivered-goods-replan（ix: 统一前后端订单六态契约）
- 迁移及测试结果：
  - `python -m pytest -q tests/unit/core/test_order_status.py tests/unit/services/test_state_machine.py tests/api/test_orders.py` → 155 passed
  - `python -m pytest -q tests/integration/test_schedule_pipeline.py tests/integration/test_simulation_pipeline.py` → 7 passed
  - `python -m pytest -q -p no:cacheprovider` → **656 passed, 201 warnings**
  - `src/frontend`：`npm run build`（含 `vue-tsc -b`）通过
  - 本地 `src/backend/data/logistics.db` dry-run：`pending 100 + unassigned 6`；执行回填 `changed=100`，事后 106 条均为 `unassigned`，二次 dry-run `planned=[]`
- 遗留事项：未做真实浏览器端到端点烟（本机无 Docker，见计划 02）；Alembic 仍为双 head，回填走 `scripts/migrate_legacy_order_status.py` 而非新 revision。

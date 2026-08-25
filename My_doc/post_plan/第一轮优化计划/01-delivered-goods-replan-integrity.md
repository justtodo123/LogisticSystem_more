---
plan_id: "01"
title: 已送达货物重规划完整性
status: done
priority: P0
owner: 待认领
created: 2026-08-18
updated: 2026-08-19
depends_on: ["00", "00A"]
---

# 01 — 已送达货物重规划完整性

## 来源证据与当前行为

- [reset_goods_for_replan](../../src/backend/services/state_machine.py#L741-L764)把 `packed`、`in_transit`、`delivered` 全部强制转为 `pending_pack`。
- [货物状态机](../../src/backend/services/state_machine.py#L51-L57)却把 `delivered` 定义为终态。
- [AI 重规划调用点](../../src/backend/services/replan_service.py#L202-L209)在非异常、非草稿路径执行上述重置。
- [当前单元测试](../../src/backend/tests/unit/services/test_state_machine.py#L318-L322)把 delivered 回退固化为预期。

## 问题与目标

部分送达订单重规划时，已签收货物可能重新进入打包、派车和配送。目标是保护终态数据，只让业务明确允许重排的未终态货物参与新方案，并保证失败不破坏旧方案。

## 范围

- 明确 packed、in_transit、delivered 在 AI/异常/草稿重规划中的处理矩阵。
- 修正状态重置、打包候选和后续调度筛选。
- 增加混合状态订单及失败回滚测试。
- 检查订单、包裹和旧方案的聚合状态。

## 非目标

- 不重写完整重规划架构。
- 不改变 delivered 的终态定义。
- 不同时处理算法评分或 2-opt。

## 依赖与进入条件

- [00 执行治理](./00-execution-governance.md)已采用。
- [00A 文档基线校准](./00A-documentation-baseline-and-source-governance.md)已完成，当前状态与业务契约来源已统一。
- 先确认业务不变量：已送达货物在任何重规划中均不可再次履约。

## 有序实施步骤

1. 为 AI 非草稿、AI 草稿、异常 full/partial/hybrid 建立状态处理表。
2. 将 delivered 从 `reset_goods_for_replan()` 查询范围移除；评审 in_transit 是否允许回退，并用显式注释说明原因。
3. 更新已有 `test_reset_delivered_goods`：断言 delivered 保持不变；补 packed/in_transit/exception/未知订单边界。
4. 建立一个订单同时含 delivered 与未送达货物的测试数据。
5. 贯穿 F007→F021→F005→F006，断言新包裹、新调度任务和新路线均不包含 delivered goods_code。
6. 模拟调度或路径规划失败，断言事务回滚后 delivered、旧方案和旧批次保持一致。
7. 检查订单最终聚合：剩余货物完成后订单只推进一次，不因旧 delivered 数据重复计数。
8. 运行定向及全量测试，完成后新增/更新对应问题记录和路线图状态。

## 验收标准

- delivered 永远不转回 `pending_pack`，也不进入新包裹、调度任务或路线。
- 混合状态订单只重排允许的未终态货物。
- 草稿生成不改变现有货物状态。
- 重规划任何阶段失败均不损坏旧方案和终态数据。
- 状态矩阵有单元、服务和至少一条 API/集成回归保护。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services/test_state_machine.py
python -m pytest -q tests/unit/services/test_exception_service.py tests/integration/test_exception_replan.py
python -m pytest -q tests/integration/test_schedule_pipeline.py tests/integration/test_simulation_pipeline.py
python -m pytest -q -p no:cacheprovider
```

## 文档与问题记录同步

- 更新状态机/重规划当前说明及测试场景。
- 若无已有精确问题记录，按模板新增“delivered 被重规划回退”记录；记录根因、事务边界和真实验证。
- 完成后更新 [README](./README.md)。

## 回滚与恢复

若新筛选导致部分重规划无候选，不得恢复 delivered 回退；应回滚该任务提交并保留失败数据，重新澄清 in_transit/packed 策略。

## 完成记录

- 完成日期：2026-08-19
- 负责人：待认领
- 分支：`feat/01-delivered-goods-replan`
- Commit / PR：`0d21f00` on `feat/01-delivered-goods-replan`
- 定向测试：`tests/unit/services/test_state_machine.py` + `tests/unit/algorithms/test_global_schedule.py` + `tests/integration/test_schedule_pipeline.py` → 148 passed
- 全量测试：2026-08-19，`src/backend`，`python -m pytest -q -p no:cacheprovider` → **645 passed, 196 warnings**
- 数据不变量复核：delivered 不再回退；F007/F021 不再收终态货物；失败 rollback 不损坏旧 delivered；订单 signed 仅在剩余货物全部完成时推进一次
- 问题记录：[proced 010](../../proced_problem/010-delivered-goods-reset-on-replan.md)

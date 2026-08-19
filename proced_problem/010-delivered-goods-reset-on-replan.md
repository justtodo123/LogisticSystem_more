---
problem_id: "010"
slug: delivered-goods-reset-on-replan
date: 2026-08-19
tags: [state-machine, replan, delivered, data-integrity]
severity: major
status: fixed
related_files:
  - src/backend/services/state_machine.py
  - src/backend/services/replan_service.py
  - src/backend/algorithms/global_schedule.py
  - src/backend/algorithms/packaging.py
related_pr: ""
---

# 已送达货物在 AI 重规划中被打回 pending_pack

## 1. 症状（表现形式）

部分送达订单再次 AI 重规划时，已签收货物从 `delivered` 被强制转回 `pending_pack`，并进入新的包裹/调度/路线。货物状态机定义 `delivered` 为终态（不可再转），与实现矛盾。

## 2. 复现条件

1. 订单含至少一件 `delivered` 货物与一件未送达货物
2. 调用 AI 重规划（`ReplanService.redispatch`，无异常事件，`draft_only=False`）
3. `reset_goods_for_replan()` 以 `force=True` 把 `delivered` 写回 `pending_pack`

稳定复现。异常重规划 `mark_exception_statuses` 本就不包含 delivered。

## 3. 定位过程

- 状态机 `GOODS_TRANSITIONS["delivered"] = []`
- `reset_goods_for_replan` 查询 `packed/in_transit/delivered` 并 `force=True`
- 单测 `test_reset_delivered_goods` 把回退固化为预期
- F007 `_build_schedule` 遍历 `order.goods` 不筛状态，终态货物仍进 `goods_schedules`

## 4. 根因

重规划重置把「已离开待打包」误当成「包括已签收」，用 `force=True` 绕过终态约束；下游 F007 也未排除 `delivered`。

## 5. 解决方案

- 重置范围改为 `packed/in_transit`；`in_transit` 仍允许回退（未终态，需召回重打包）
- F007 跳过 `delivered`；若无未终态货物则明确报错，不恢复 delivered 回退
- 打包查询继续只收 `pending_pack/exception`
- `draft_only` 仍不调用重置

## 6. 验证

2026-08-19 在 `src/backend`：

- 定向：`test_state_machine.py` + `test_global_schedule.py` + `test_schedule_pipeline.py` 148 passed
- 异常/模拟/打包：43 passed
- 全量：`python -m pytest -q -p no:cacheprovider` → **645 passed, 196 warnings**

## 7. 通用经验

终态不允许 `force` 回退。测试不能把违背不变量的行为固化成预期。重规划筛选要在重置、调度、打包三层一致。

---
problem_id: "005"
slug: seed-order-status-enum-drift
date: 2026-08-14
tags: [seed-data, state-machine, enum-drift, silent-failure, scheduling]
severity: critical
status: fixed
related_files:
  - src/backend/scripts/init_demo_data.py
  - src/backend/services/state_machine.py
  - src/backend/services/order_service.py
  - src/backend/services/ai.py
related_pr: ""
---

# 种子订单状态枚举漂移（pending vs unassigned），核心调度链路在演示数据上不可用

## 1. 症状（表现形式）

`init_demo_data.py` 生成的 100 条种子订单，业务代码全部"看不见"：

| 观测点 | 结果 |
| --- | --- |
| `GET /api/orders` 列表 | 100 条，status 全为 `pending` |
| AI `_build_context` 待调度订单计数 | 仅命中 6 条（测试中新建的），非种子 100 条 |
| `POST /api/schedule/global`(traditional) | `40001 没有找到未打包的订单...请确认订单状态为 unassigned/exception` |

调度、打包、派单、路径规划全链路因"找不到可调度订单"而阻塞。

## 2. 复现条件

1. `python scripts/init_demo_data.py` 生成种子数据（订单 `status="pending"`）
2. 调全局调度端点
3. **稳定复现**——种子订单永不进入订单状态机合法枚举，调度恒为空

## 3. 定位过程

**Step 1 — 排除"调度算法"问题**：调度报错是 `40001 没有找到未打包的订单`，说明入口能跑，是"查不到订单"而非"算法崩了"。

**Step 2 — 对比订单种子状态与状态机枚举**：[init_demo_data.py:340](../src/backend/scripts/init_demo_data.py) 写订单 `status="pending"`；而 [state_machine.py](../src/backend/services/state_machine.py) 的 `ORDER_TRANSITIONS` 起点是 `unassigned`，合法状态为 `unassigned/assigned/in_transit/signed/exception/closed`，**无 `pending`**。`order.py:14` 默认值也是 `server_default="unassigned"`。

**Step 3 — 确认各消费方统一用 `unassigned`**：`order_service.create_order` 设 `status="unassigned"`；`ai._build_context` 查 `status="unassigned"`。种子订单写的 `pending` 全程不命中。

**Step 4 — 澄清货物状态（推翻 issue_analysis 的误判）**：`GOODS_TRANSITIONS` 起点是 `pending_pack`（[state_machine.py:52](../src/backend/services/state_machine.py)），`goods.py:18` 默认值 `server_default="pending_pack"`，`order_service.create_order` 建货物也写 `pending_pack`。因此种子货物 `status="pending_pack"` **本就是合法状态，无需改动**。issue_analysis 里"货物也改成 unassigned"的建议是错的——`unassigned` 是订单状态，不是货物状态；货物应保持 `pending_pack`。真正漂移的只有**订单**的 `pending`。

**起初以为**：订单和货物两个状态都写错了。**后来确认**：只有订单 `pending` 漂移；货物 `pending_pack` 是状态机合法起点，保持不变。

## 4. 根因

`init_demo_data.py` 写入的**订单**种子状态 `pending` 与订单状态机/业务代码统一使用的 `unassigned` 不一致，种子订单从不进入状态机合法状态。

## 5. 解决方案

**状态：fixed（2026-08-17）**。

1. [init_demo_data.py:340](../src/backend/scripts/init_demo_data.py) 订单 `status="pending"` → `"unassigned"`。货物 `status="pending_pack"` 保持不变（本就是合法状态）。

## 6. 验证

**已执行（2026-08-17）**：

```python
# init_demo_data.py:340 修改确认
status="unassigned"  # 原 "pending"
```

全量 `pytest` → **635 passed**，0 failed。✅

## 7. 通用经验

1. **种子数据的状态枚举必须与状态机/业务代码同一套常量**：理想是种子脚本直接 import 状态机的枚举常量，而不是手写字符串字面量 `"pending"`。
2. **"自动化测试全绿"无法覆盖"种子数据漂移"**：测试夹具注入的是符合枚举的临时数据，真实种子脚本是另一条写入路径。应补一条"针对真实种子数据的冒烟测试"。
3. **"列表查得到、引擎找不到"是枚举漂移的典型信号**：当某个实体列表能查到、但按状态过滤/调度却为空时，先对比两处的状态枚举。
4. **状态枚举按实体区分，不能混用**：订单状态（`unassigned`）和货物/包裹状态（`pending_pack`）是两套枚举，排查时要分别对照各自的 `*_TRANSITIONS` 起点，避免"订单该用 unassigned"被误套到货物上。


## 8. 后续（2026-08-19，plan 03）

种子脚本漂移已在 2026-08-17 修复。03 继续收口剩余契约面：

- `init_demo_data.py` 改为引用 `core.order_status.ORDER_UNASSIGNED`，不再手写六态字面量。
- 前端/Mock 从旧四态改为同一组六态；未知状态显示为「未知状态（raw）」而不是映射成合法态。
- 本地 `src/backend/data/logistics.db` 仍有 100 条历史 `pending`，已用 `scripts/migrate_legacy_order_status.py` 回填为 `unassigned`（106=106，二次 dry-run 无计划项）。

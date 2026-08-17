---
problem_id: "007"
slug: ordercreate-time-window-unvalidated
date: 2026-08-14
tags: [validation, pydantic, schema, boundary, scheduling]
severity: minor
status: open
related_files:
  - src/backend/schemas/order.py
  - src/backend/services/order_service.py
related_pr: ""
---

# OrderCreate schema 未校验 time_window 合法性，非法时间窗直接入库

## 1. 症状（表现形式）

`POST /api/orders` 的 `time_window` 字段无任何校验，非法值被直接接受并入库：

| 输入 `time_window` | 结果 |
| --- | --- |
| `"18:00-9:00"`（起晚于止） | 被接受 |
| `"abc"` | 被接受 |

`order_service.create_order` 直接透传入库，不解析、不校验起止时间。

## 2. 复现条件

1. `POST /api/orders` 传 `time_window` 为倒置或非 `HH:MM-HH:MM` 格式
2. **稳定复现**——只要字段是字符串就通过，无格式/先后校验

## 3. 定位过程

**Step 1 — 确认校验层是否生效**：[schemas/order.py:18](../src/backend/schemas/order.py) `OrderCreate.time_window: str` 只有类型标注，无 regex/validator。

**Step 2 — 确认服务层是否兜底**：[order_service.create_order](../src/backend/services/order_service.py) 直接透传 `time_window` 入库，不解析、不校验。

**Step 3 — 确认下游影响**：非法时间窗会进入调度，可能影响 ETA/SLA 计算与路线规划。

**起初以为**：也许在调度阶段才对时间窗做校验。**后来确认**：全链路无人校验，非法值从入库一路流到调度。

## 4. 根因

`OrderCreate.time_window` 缺少 Pydantic v2 字段级 `field_validator` 校验时间窗格式与起止先后，服务层也不兜底。

## 5. 解决方案

**状态：open（待澄清，暂缓）**。

ISSUE-004 建议给 `time_window` 加严格 `HH:MM-HH:MM` 正则校验，但**该建议与代码库实际契约冲突**，直接落地会引入回归：

- `time_window` 实际是自由文本"时效要求"，合法值包括 `"全天"`、`"2026-06-15 全天"`、`"2026-06-20 9:00-18:00"`、`"9:00-18:00"`（见 `tests/conftest.py`、`tests/api/test_orders.py`、`scripts/init_demo_data.py:339`）。
- 严格正则只接受 `HH:MM-HH:MM`，会拒绝上述 `"全天"` 和带日期前缀的合法值，破坏现有测试与真实数据。
- 全链路无人解析 `time_window` 的起止时间做 ETA/SLA 计算（`deepseek_service.py:98` 仅作字符串拼进 AI prompt），因此"非法时间窗影响 ETA/SLA"的顾虑在当前实现中不成立。
- 代码库已有 `core/validators.py:64` 的 `validate_time_window`，但它是**死代码**（grep 全仓无调用点），且其正则同样假设 `HH:MM-HH:MM`。

**待决策**：若确实要校验，需先明确 `time_window` 的规范（是自由文本、还是拆成 `time_window_start/end` 两个 TIME 字段——后者已在 `database.py:68-69` 预留）。当前不改动 schema，避免破坏性回归。

## 6. 验证

暂不修改代码，无回归风险。若后续决定引入校验，需同步更新 `tests/conftest.py` / `test_orders.py` 等用 `"全天"`、`"2026-06-15 全天"` 的用例。

## 7. 通用经验

1. **给字段加校验前，先摸清该字段的真实取值分布**：`time_window` 的合法值远不止 `HH:MM-HH:MM`，先 `grep` 全仓所有 `time_window=` 的赋值，再决定校验规则，否则严格正则会误杀"全天"这类合法值。
2. **测试报告的建议不等于可直接落地**：ISSUE-004 的正则示例与代码库契约不符，落地前要对着现有测试/种子数据核对。
3. **已存在但未被调用的校验函数是"校验意图与实现脱节"的信号**：`core/validators.py:validate_time_window` 无人调用，说明"想校验"和"实际没校验"长期并存，需先决定要不要启用。

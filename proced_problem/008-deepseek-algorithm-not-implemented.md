---
problem_id: "008"
slug: deepseek-algorithm-not-implemented
date: 2026-08-14
tags: [algorithm, strategy-pattern, factory, docs-drift, ai]
severity: major
status: mitigated
related_files:
  - src/backend/algorithms/factory.py
  - src/backend/algorithms/global_schedule.py
related_pr: ""
---

# algorithm="deepseek" 未实现，策略工厂仅注册 greedy/dummy

## 1. 症状（表现形式）

`POST /api/schedule/global` 传 `{"algorithm":"deepseek"}`：

```
40001 全局调度失败: 阶段3仅支持 traditional 算法，收到: deepseek
```

但 docs/功能清单把 `deepseek` 列为可选调度算法，与 AI 助手（deepseek 解析）的能力边界不一致。

## 2. 复现条件

1. `POST /api/schedule/global` 传 `{"algorithm":"deepseek"}`
2. **稳定复现**——每次都在 [global_schedule.py:342](../src/backend/algorithms/global_schedule.py) 抛 `ValueError`

## 3. 定位过程

**Step 1 — 确认是"入口拒绝"而非"策略内部报错"**：[global_schedule.py:342-343](../src/backend/algorithms/global_schedule.py) 入口 `if algorithm != "traditional": raise ValueError(...)`，直接拒绝。

**Step 2 — 确认策略注册表内容**：[factory.py:42-44](../src/backend/algorithms/factory.py) `_GLOBAL_STRATEGIES` 只注册 `greedy` 和 `dummy`，无 `deepseek`。

**Step 3 — 确认文档声称**：docs/功能清单将 `deepseek` 列为可选算法，实际未落地，是文档超前于实现。

**起初以为**：`deepseek` 可能只在 AI 解析层用，调度算法本就不该有。**后来确认**：调度端点 docstring 写明 `algorithm 类型（"traditional" 或 "deepseek"，阶段3仅实现 traditional）`，即设计上预留了 deepseek、但未实现。

## 4. 根因

策略工厂 `_GLOBAL_STRATEGIES` 未注册 `deepseek`，且调度入口硬编码仅接受 `traditional`，与文档声明的能力不一致。

## 5. 解决方案

**状态：mitigated（2026-08-17，短期缓解；完整实现待排期）**。

已实施短期方案：
- [schedule_service.py](../src/backend/services/schedule_service.py) 新增 `SUPPORTED_ALGORITHMS = ("traditional",)`，`create_global_schedule` 在调用策略前校验 `algorithm`，未知算法返回 `code=40000`（参数错误）+ 支持列表，不再流到 `global_schedule()` 抛 `40001` 业务错误。
- [api/schedule.py](../src/backend/api/schedule.py) schema `algorithm` 描述更新为 `"算法类型：traditional（deepseek 预留未实现）"`。

正确实现（`DeepSeekScheduleStrategy`）留待后续排期。

## 6. 验证

**已执行（2026-08-17）**：

- `{"algorithm":"deepseek"}` → `code=40000, message="不支持的算法: deepseek，当前支持: traditional"` ✅
- `{"algorithm":"traditional"}` → 正常返回 draft ✅
- API 测试 `test_create_global_schedule_invalid_algorithm` 仍通过（`code != 0`，message 含 "算法"/"不支持"）✅
- 单元测试 `test_invalid_algorithm_raises_error` 仍通过（内部函数仍有 ValueError 防御）✅
- 全量 `pytest` → **635 passed**，0 failed。✅

## 7. 通用经验

1. **策略工厂的注册表要与文档/接口 docstring 一致**：`_GLOBAL_STRATEGIES` 是能力的唯一权威来源，文档声称的算法必须能在表里找到。
2. **"未实现的枚举值"应返回参数错误码而非业务错误码**：`40001 调度失败` 会误导排查方向；未知 `algorithm` 应尽早 `40000` + 支持列表。
3. **预留能力要标注"未实现"并 fail-fast**：docstring 里写"阶段3仅实现 traditional"是对的，但接口对外暴露了 `deepseek` 这个取值，就应要么实现、要么在入口明确拒绝并说明。

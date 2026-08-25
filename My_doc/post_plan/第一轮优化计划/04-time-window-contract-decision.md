---
plan_id: "04"
title: time_window 数据契约决策
status: done
priority: P1
owner: 待认领
created: 2026-08-18
updated: 2026-08-19
depends_on: ["00", "03"]
---

# 04 — `time_window` 数据契约决策

## 来源证据与当前行为

- [OrderCreate](../../src/backend/schemas/order.py#L14-L19)只声明 `time_window: str`。
- [问题 007](../../proced_problem/007-ordercreate-time-window-unvalidated.md#L48-L61)记录了严格 `HH:MM-HH:MM` 与真实值冲突：合法数据含“全天”、带日期前缀和纯时间范围。
- 现有严格 validator 是未调用代码；当前下游主要把该字段作为展示文本/AI prompt，而非可计算 SLA 约束。

## 问题与目标

先决定该字段是展示性“时效要求”还是调度可计算时间窗，再设计校验与迁移，避免用简单正则破坏现有数据或继续让字段语义含混。

## 范围

- 全仓及真实环境值分布盘点。
- 三种方案决策：自由文本最小约束、规范化可解析字符串、结构化日期/start/end + 兼容文本。
- API、数据库、导入、种子、前端、AI prompt、迁移和版本策略。

## 非目标

- 决策前不修改 [order.py](../../src/backend/schemas/order.py)。
- 不假定所有时间窗都在同一天或不可跨午夜。
- 不在没有历史数据报告时执行破坏性迁移。

## 依赖与进入条件

- [03](./03-order-status-contract.md)完成契约治理方式统一。
- 产品方明确近期是否要求 ETA/SLA/调度算法真正消费时间窗。

## 有序实施步骤

1. 盘点代码、测试、种子、导入样例和脱敏真实库中的不同值、空白、长度及异常分布。
2. 写出用例矩阵：全天、指定日期全天、日内范围、跨午夜、时区、无截止期、非法文本。
3. 比较并记录决策：
   - A：保留自由文本，只做 strip、非空、长度和安全限制；
   - B：定义兼容的规范化字符串 grammar；
   - C：新增 `service_date/start/end/timezone/note` 结构化字段，旧文本只作兼容。
4. 推荐规则：若近期参与计算选 C；若只展示选 A 并把名称/文档改为“时效要求”。不得选择与现有值冲突的单一正则。
5. 定义 API 兼容期、响应双写/读取优先级、数据库迁移与回填报告。
6. 定义 Excel 导入、种子、前端表单、AI prompt 和错误提示变化。
7. 决策评审后再拆出代码实施提交；新增解析/校验/迁移及 round-trip 测试。
8. 用全新库和历史样本验证，最后关闭或更新问题 007。

## 验收标准

- 有书面决策、业务用例、字段语义、时区/跨午夜规则和兼容期限。
- 现有合法样本不会在无迁移提示下被拒绝。
- 非法输入错误稳定且可理解；数据库列长度与 API 限制一致。
- 若结构化，迁移前后记录数一致，无法解析项生成报告而非丢失。
- 所有生产者/消费者和当前文档同步。

## 验证命令

决策阶段：运行值分布脚本并保存脱敏统计。实施阶段：

```bash
cd src/backend
python -m pytest -q tests/api/test_orders.py tests/api/test_orders_import.py tests/unit/services/test_order_service.py
python -m pytest -q -p no:cacheprovider
```

```bash
cd src/frontend
npx vue-tsc --noEmit
npm run build
```

迁移必须先在数据库副本 dry-run，并验证回滚。

## 文档与问题记录同步

- 更新 [问题 007](../../proced_problem/007-ordercreate-time-window-unvalidated.md)的最终决策、迁移与验证。
- 同步 API、数据库字段、导入模板、前端表单和 AI 能力边界。
- 完成后更新 [README](./README.md)。

## 回滚与恢复

结构化方案采用可逆迁移并保留原文本至兼容期结束；回滚时从原文本恢复，禁止先删旧列再验证。

## 完成记录

- 决策日期：2026-08-19
- 选定方案及理由：**A — 时效要求自由文本 + 最小约束**。近期不参与 ETA/SLA/调度计算（仅展示与 AI prompt）；现有合法值含「全天」和日期前缀，禁止 `HH:MM-HH:MM` 正则。C 留到调度真正消费时间窗时再开。
- 落地约束：`strip`、非空、无控制字符、长度 ≤ 32（对齐 `orders.time_window`）。
- Commit / PR：`4643289`
- 数据迁移与测试结果：无需回填（本地 106 条均为 `9:00-18:00`）。
  - 定向：`tests/unit/core/test_time_window.py` + `tests/api/test_orders.py` + `tests/api/test_orders_import.py` + `tests/unit/services/test_order_service.py` → 48 passed
  - 全量：`python -m pytest -q -p no:cacheprovider` → 678 passed, 209 warnings（04 前基线 664）
  - 前端：`npm run build`（`vue-tsc -b && vite build`）通过

---
plan_id: "05"
title: 路线分页契约与查询效率
status: done
priority: P1
owner: 待认领
created: 2026-08-18
updated: 2026-08-19
depends_on: ["00", "03"]
---

# 05 — 路线分页契约与查询效率

## 来源证据与当前行为

开始时：`get_routes` 已分页但只返回 `items/total`，循环内再查 Dispatch/Batch/Vehicle。

2026-08-19 完成后：

- 响应为 `items / total / page / page_size`，非法 `page/page_size` 返回 `code=40000`
- 一次 join 取出关联字段，查询次数不随 `page_size` 增长
- 稳定排序：`created_at desc, id desc`

## 问题与目标

统一路线列表分页契约，并在不改变筛选和排序语义的前提下，把每页关联数据改为有界查询。

## 范围

- `GET /api/routes` 的查询、响应和测试。
- batch_code、vehicle_code 组合筛选，空页/越界页和稳定排序。
- 前端调用方兼容及查询次数基准。

## 非目标

- 不重构路线规划算法。
- 不改变 route detail 或坐标 API，除非复用公共序列化器是必要且无行为变化。
- 不提前引入游标分页。

## 依赖与进入条件

- [00](./00-execution-governance.md)已采用。
- 确认统一列表响应的 page/page_size 放在 `data` 还是 `meta`，沿用项目现有多数端点模式。

## 有序实施步骤

1. 对照其他分页端点确定权威响应：`items / total / page / page_size` 及参数边界。
2. 增加失败先行测试：第一页、第二页、空库、越界页、非法 page/page_size、batch、vehicle 和组合筛选。
3. 定义稳定排序（例如 created_at + id），避免跨页重复或遗漏。
4. 使用一次 join/选列查询返回 Route、NodeDispatch、DispatchBatch、Vehicle 所需字段；避免循环内查询。
5. 保持可选筛选 join 不造成重复行；total 对应筛选后的唯一路线数。
6. 加查询次数测试或 SQL 事件计数，断言查询数不随 page_size 线性增长。
7. 更新前端 API 类型和分页组件，兼容旧响应的策略必须有明确移除日期。
8. 运行定向、全量和适量数据性能基准。

## 验收标准

- 成功响应稳定包含 items、total、page、page_size。
- 相同条件下分页顺序稳定，组合筛选和 total 正确。
- 每页查询数为常数级，不随 item 数增加。
- 前端翻页、筛选和空态正常。
- 现有 route detail/coordinates 行为无回归。

## 验证命令

```bash
cd src/backend
python -m pytest -q tests/unit/services/test_route_service.py tests/api/test_routes.py tests/api/test_pagination.py
python -m pytest -q -p no:cacheprovider
```

```bash
cd src/frontend
npx vue-tsc --noEmit
npm run build
```

记录优化前后固定 20/100 条数据的 SQL 次数和响应时间，仅将查询次数作为硬门禁。

## 文档与问题记录同步

- 更新路线 API 的分页字段、默认值和最大值。
- 如 N+1 修复需要非平凡排查，新增对应问题记录；否则在计划完成记录中保存基准。
- 完成后更新 [README](./README.md)。

## 回滚与恢复

响应契约与前端必须同阶段发布。查询重写出现数据库兼容问题时回滚实现但保留失败测试，不恢复缺失分页元数据的错误契约。

## 完成记录

- 完成日期：2026-08-19
- 负责人：待认领
- Commit / PR：d1fb3f7 on eat/01-delivered-goods-replan（ix: 补齐路线列表分页契约并消除 N+1）
- 查询次数前后对比（25 条路线，SELECT 次数）：
  - 修复前：约 `2 + 3 * page_size`（count + 列表 + 每条 3 次关联查询）→ page_size=20 约 62，page_size=100 约 302
  - 修复后：page_size=20 与 100 均为常数级（测试断言 `<= 3` 且两者相等）
- 测试结果：
  - `pytest tests/unit/services/test_route_service.py tests/api/test_routes.py tests/api/test_pagination.py` → 30 passed
  - 全量 `python -m pytest -q -p no:cacheprovider` → **664 passed, 207 warnings**
  - 前端 `npm run build`（含 `vue-tsc -b`）通过
- 遗留事项：无独立路线管理页，前端调用方（异常列表/车辆坐标）已兼容新字段；未引入游标分页。

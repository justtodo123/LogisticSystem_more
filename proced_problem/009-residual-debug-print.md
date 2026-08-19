---
problem_id: "009"
slug: residual-debug-print
date: 2026-08-14
tags: [logging, code-hygiene, print, observability]
severity: minor
status: fixed
related_files:
  - src/backend/services/schedule_service.py
related_pr: ""
---

# schedule_service 残留 DEBUG/ERROR print 语句，内部状态泄漏到 stdout

## 1. 症状（表现形式）

真实调度请求时，服务端 stdout 出现内部状态打印：

```
[DEBUG] gs.id=..., gs.score=..., raw_score=..., max_possible=..., score_display=...
[DEBUG] gs.goods_schedules type=..., len=...
[ERROR] get_global_schedule failed: ...
```

这些打印绕过统一 logging，向 stdout 泄漏内部结构（`gs.id`、`raw_score`、`score_display` 等），`[ERROR]` 分支也未用 `logger.error`。

## 2. 复现条件

1. 触发一次全局调度请求（`POST /api/schedule/global`）
2. 观察后端进程 stdout
3. **稳定复现**——每次调度都打印 DEBUG 行

## 3. 定位过程

**Step 1 — 全仓 grep `print(`**：命中 [schedule_service.py:318-319](../src/backend/services/schedule_service.py) 两条 DEBUG print、[:425](../src/backend/services/schedule_service.py) 一条 `[ERROR]` print。

**Step 2 — 确认是否走统一日志**：三处均为裸 `print(f"...")`，未走模块 `logger`。

**Step 3 — 评估影响**：DEBUG print 在真实请求路径上，每次调度都执行；`[ERROR]` 分支本应进错误日志/告警，却只 print 到 stdout。

**起初以为**：可能是测试代码残留。**后来确认**：位于 `get_global_schedule` 的主请求路径，生产环境同样会触发。

## 4. 根因

开发期调试残留的裸 `print` 未清理，`[ERROR]` 分支误用 `print` 而非 `logger.error`。

## 5. 解决方案

**状态：fixed（2026-08-17）**。

1. [schedule_service.py](../src/backend/services/schedule_service.py) 顶部新增 `import logging; logger = logging.getLogger(__name__)`。
2. 删除原 318-319 行两条 `[DEBUG]` print。
3. 原 425 行 `[ERROR]` print + `traceback.print_exc()` → `logger.error("get_global_schedule failed: %s", e, exc_info=True)`。

## 6. 验证

**已执行（2026-08-17）**：

```bash
grep -n "print(" src/backend/services/schedule_service.py
# 无输出 — 所有裸 print 已清除
```

全量 `pytest` → **635 passed**，0 failed。✅

## 7. 通用经验

1. **业务代码里 `grep print(` 是收尾 check 项**：裸 `print` 绕开日志级别控制，生产会污染 stdout 且 `[ERROR]` 不触发告警。
2. **异常日志用 `logger.error(..., exc_info=True)` 或 `%s` 传异常**，不要 `f-string` 拼异常字符串，否则丢堆栈。

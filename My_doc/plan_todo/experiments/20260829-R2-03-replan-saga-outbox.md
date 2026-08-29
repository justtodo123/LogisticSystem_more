# R2-03 Step 1/2 实验草稿：重规划 Saga 与任务骨架

- 日期：2026-08-29
- 分支：`feat/R2-03-replan-saga-outbox`
- 基线：`origin/main` @ `87190d2`
- 决策：`D-R2-SAGA`（`v2026-08-25-r2-freeze`）
- 状态：草稿；仅覆盖 Step 1 事务边界分析与 Step 2 `replan_tasks` 骨架
- 环境边界：Windows 11 + Python 3.13 + SQLite。SQLite 结果只辅助验证 P0 schema/幂等协议，不代表 PostgreSQL、多 worker 或生产并发能力。

## 当前 commit 点与外部 I/O

`ReplanService.redispatch()` 表面有 3 次显式提交，但调用的下层服务还会独立提交，因此现有调用链并不是一个可整体回滚的事务：

| 顺序 | 领域步骤 | 当前写入/提交位置 | 提交后失败的现状 |
|---|---|---|---|
| 1 | F007 生成 draft | `ScheduleService.create_global_schedule()` 内部 `db.commit()`；`draft_only` 分支随后在 `replan_service.py:238` 再提交版本链 | draft 已存在；后续失败不会删除或作废 |
| 2 | F021 确认与打包 | `ScheduleService.confirm_schedule()` 默认提交 draft→active、订单/货物/包裹状态；版本链在 `replan_service.py:273` 再提交 | F005/F006 失败时，F021 已不可由请求级 rollback 撤销 |
| 3 | 旧实体标记 | `mark_old_entities_exception()` 修改旧包裹/批次，最终在 `replan_service.py:312` 提交 | 与 F005/F006 的实际提交顺序交错，失败后可能留下新旧实体状态不一致 |
| 4 | F005 节点调度 | `DispatchService.create_node_dispatch()` 内部 `db.commit()`（`dispatch_service.py:162`） | 批次和调度单已经存在；之后 F006 失败不会自动作废未发车批次 |
| 5 | F006 路径规划 | `RouteService.create_route_planning()` 内部 `db.commit()`（`route_service.py:98`） | route 已存在；随后版本/旧实体更新失败时 route 仍保留 |
| 6 | 批量事件回写 | `redispatch_batch()` 在 `replan_service.py:423` 提交 `replan_batch_code` | 每组重规划自身已经多次提交，批量回写失败不能撤销它们 |
| 7 | reroute 版本链 | 路径服务先提交 route，`reroute()` 在 `replan_service.py:526` 再提交版本链 | 两次提交之间失败会留下未挂版本链的新 route |
| 8 | 通知 | `await send_notification(...)` 在业务提交后执行；dispatcher 也提供 fire-and-forget | 请求 Session 可能被后台 task 继续使用；通知失败被吞掉，且没有可靠重放记录 |
| 9 | SMTP | `EmailChannel.send()` 在 async 函数内直接调用同步 `smtplib.SMTP`，超时 10 秒 | 阻塞事件循环；请求返回与通知是否真正送达之间没有持久化协议 |

## 按 D-R2-SAGA 拟定的短事务边界

每个步骤由 `replan_tasks` 的唯一幂等键标识。每段事务只负责“检查前置状态 → 执行业务写入 → 更新任务步骤状态 → commit”；进程崩溃后根据持久化步骤判断继续、补偿或转人工。本轮仅创建任务表，不改造现有调用链。

| 事务 | 成功提交内容 | 失败/恢复规则 |
|---|---|---|
| T0 创建任务 | 插入唯一 `idempotency_key`，状态 `PENDING`，步骤 `F007` | 唯一冲突读取已有任务；不得插入第二行有效任务 |
| T1 F007 | draft + 版本链 + task→`F021` 同事务提交 | commit 前 rollback；commit 后可删除或作废 draft，再重试 |
| T2 F021 | draft→active、打包和订单/货物状态 + task→`F005` 同事务提交 | commit 前 rollback；commit 后禁止自动拆包，无法安全继续时置 `manual_required` |
| T3 F005 | dispatch batch / dispatches + task→`F006` 同事务提交 | 未发车可作废批次后重试；已 `in_transit` 置 `manual_required` |
| T4 F006 | routes + task→`NOTIFICATION` 同事务提交 | 路线未执行可删后重试；已执行则置 `manual_required` |
| T5 通知入队 | 业务最终状态、task→`COMPLETED` 与 outbox 事件同行提交 | 不回滚业务；worker 独立 Session 重试，耗尽后死信与人工重放 |

## 外部 I/O 隔离目标

1. 请求事务内不执行 SMTP/Webhook；只写 outbox。
2. outbox worker 每次领取和投递使用独立 Session，不复用请求 Session。
3. 网络 I/O 发生在数据库事务外；投递结果用短事务回写。
4. 通知失败不反向回滚 F007/F021/F005/F006，但必须留下 retry/dead-letter 证据。
5. 同步 SMTP 和 fire-and-forget 的剥离属于后续 Step 4/5，本轮不修改。

## Step 2 最小 schema

`replan_tasks` 记录：

- 唯一 `idempotency_key`；
- 整体 `status` 与 `current_step`；
- `retry_count`、脱敏后的 `last_error`；
- 乐观并发用 `version`；
- `manual_required`；
- 创建/更新时间。

本骨架不生成新的对外业务编号，因此不新增 `max+1` 或号段资源；后续若任务需要公开业务码，必须通过 R2-02B `code_ranges` 分配。

## 本轮验证结果

```text
cd src/backend
python -m alembic -c alembic.ini heads
# exit 0: r2_03_replan_tasks (head)

python -m pytest -q -p no:cacheprovider tests/migration tests/unit/core/test_model_registry.py
# exit 0: 34 passed in 14.70s

python -m pytest -q -p no:cacheprovider tests/migration tests/unit/core/test_model_registry.py tests/unit/models/test_replan_task.py
# 首次 exit 1: 34 passed, 2 failed（Boolean server default schema parity 差异）
# 修复后 exit 0: 36 passed in 15.73s
```

迁移验证覆盖从 `r2_02b_code_range_allocation` upgrade、downgrade、字段/唯一索引存在性；模型测试覆盖字段默认值和重复幂等键冲突。首次 parity 失败的定位和修复记录见 `proced_problem/013-replan-task-schema-parity-default.md`。

## 明确未覆盖

- 未实现完整 Saga `resume(task_id)` 或启动扫描；
- 未实现 `manual_required` 判定/补偿执行器；
- 未创建 outbox 表或 worker；
- 未剥离 fire-and-forget、请求 Session 复用或同步 SMTP；
- 未执行 PostgreSQL/Redis/Docker/真实 SMTP 验证；
- R2-03 计划卡仍保持 `pending`。

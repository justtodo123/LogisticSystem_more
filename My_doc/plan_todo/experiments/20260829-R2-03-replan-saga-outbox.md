# R2-03 实验记录：重规划 Saga、transactional outbox 与 leased claims

- 日期：2026-08-31
- 分支：`feat/R2-03-replan-saga-outbox`；远程分支 `origin/feat/R2-03-replan-saga-outbox` @ `ffec6bb`
- 基线：`origin/main` @ `87190d2`；当前相对基线 ahead 15 / behind 0
- 决策：`D-R2-SAGA`（`v2026-08-25-r2-freeze`）
- 状态：`pending`；功能实现与本地验证已完成，尚无 R2-03 PR，必须等待 PR 授权、CI 与 merge 后才能标记 `done`
- 当前唯一 Alembic head：`r2_03_replan_task_claims`
- 环境边界：Windows 11 + Python 3.13 + SQLite。SQLite 结果只辅助验证 P0 schema/幂等/租约协议，不代表 PostgreSQL、多 worker 或生产并发能力。

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
5. 外部邮件/Webhook 的崩溃边界取决于接收方能力：若接收方不支持幂等令牌，则在“外部已接收、数据库尚未写回 `delivered`”时崩溃只能保证 **at-least-once**，不得声称 exactly-once。

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
# exit 0: r2_03_outbox_claims (head)

python -m pytest -q -p no:cacheprovider tests/unit/services/test_replan_task_service.py
# exit 0: 3 passed in 0.42s

python -m pytest -q -p no:cacheprovider tests/migration tests/unit/core/test_model_registry.py tests/unit/models/test_replan_task.py tests/unit/services/test_replan_task_service.py
# exit 0: 39 passed in 15.49s
```

验证覆盖迁移 schema、模型注册、任务字段默认值/唯一键，以及 `get_or_create_replan_task` 的幂等复用和 `check_replan_task_preconditions` 的重复只读行为。R2-03 仍保持 `in_progress`，未扩展到 outbox worker 或完整 Saga。

## Step 3 可恢复编排骨架

`services/replan_task_service.py` 在 Round 1 的幂等创建/只读检查草稿上补充：

- `start(db, idempotency_key)`：以唯一索引为真相源，首次创建提交任务；重复 key 返回原任务，不创建第二行。
- `resume(db, task_id, executors, compensators)`：每次只执行 `current_step` 对应的一个注入执行器；业务写入和 task 的步骤/status/version 更新由同一次 commit 落库。
- commit 前异常：统一 rollback，task 保持原步骤，执行器写入的业务数据不落库。
- commit 后异常：
  - F007 draft、F005 未发车、F006 未执行：调用注入补偿器，补偿提交后保持当前步骤可重试；
  - F021：禁止自动拆包，直接 `manual_required=True`；
  - F005 `in_transit`、F006 `executed`：直接进入人工处理；
  - 缺少可靠补偿或补偿失败：fail closed，进入人工处理。
- 已进入 `manual_required` 的任务，后续 `resume` 抛出 R2-04A `DomainError(CODE_STATE_CONFLICT)`，由既有全局 handler 渲染统一 envelope。

执行器/补偿器仅是 Step 3 的测试级编排边界，没有重写 F007/F021/F005/F006 算法，也没有接入通知/outbox。

## Round 2 验证结果

```text
cd src/backend
python -m alembic -c alembic.ini heads
# exit 0: r2_03_outbox_claims (head)

python -m pytest -q -p no:cacheprovider tests/unit/services/test_replan_task_service.py
# exit 0: 12 passed in 0.56s

python -m pytest -q -p no:cacheprovider tests/unit/models/test_replan_task.py tests/unit/services/test_replan_task_service.py tests/migration tests/unit/core/test_model_registry.py
# exit 0: 48 passed in 36.86s
```

故障注入覆盖：commit 前业务/task 同时回滚、F021 commit 后转人工且禁止 resume、F005/F006 不可逆状态转人工、F007/F005/F006 可补偿状态调用补偿器、重复 start 不新增任务、F007 成功后从 F021 继续。

## Step 4 transactional outbox

- 迁移 `r2_03_outbox_events` 从 `r2_03_replan_tasks` 派生，保持单 head。
- `enqueue_outbox()` 只在调用方事务中 flush，不 commit、不调用 SMTP/Webhook；唯一 `dedup_key` 防止同一业务事件生成多行。
- `resume()` 的 `NOTIFICATION` 步调用 `complete_notification_step()`，任务完成状态与 `replan.completed` outbox 事件同行提交。
- `deliver_outbox_batch(session_factory, sender)` 每批创建独立 Session；查询事务在外部 I/O 前结束，投递结果再用短事务写回。
- 投递成功标记 `delivered`，后续扫描不再调用 sender；暂时失败进入 `retry` 并设置 `available_at`，达到上限或 `NonRetryableOutboxError` 进入 `dead-letter`。
- 本轮 sender 是可注入投递边界，没有从请求事务调用现有同步 SMTP。

## Round 3 验证结果

```text
cd src/backend
python -m alembic -c alembic.ini heads
# exit 0: r2_03_outbox_claims (head)

python -m pytest -q -p no:cacheprovider tests/unit/services/test_outbox.py
# 首次 exit 1: 5 passed, 1 failed（测试复用 worker Session 导致 request Session 被关闭）
# 修复为外部 I/O 前结束查询事务后 exit 0: 6 passed in 0.34s

python -m pytest -q -p no:cacheprovider tests/unit/services/test_replan_task_service.py tests/unit/services/test_outbox.py tests/migration tests/unit/core/test_model_registry.py
# exit 0: 53 passed in 13.81s
```

覆盖：业务提交成功但投递失败时 task 保持完成且 outbox 为 retry、重复 deliver 不重复 sender 副作用、pending/retry/dead-letter/delivered 状态、永久失败直达 dead-letter、数据库去重键、worker Session 与请求 Session 隔离、迁移 upgrade/downgrade 与 registry parity。

## Step 5 重规划请求路径隔离

- `ReplanService.redispatch()` 和 `reroute()` 的成功路径不再导入或调用 `send_notification` / fire-and-forget。
- 两条成功路径在请求 Session 的业务事务中写入唯一 `replan.completed` outbox 行；请求返回时状态为 `pending`，没有 SMTP/Webhook I/O。
- dispatcher/email 通道保持不变，供 worker sender 使用；测试验证 dispatcher 绑定 worker 创建的独立 Session，而不是请求 Session。
- 其他非重规划业务仍可能使用 fire-and-forget，本轮按范围未做跨模块清扫。

## Round 4 验证结果

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/services/test_outbox.py tests/unit/services/test_replan_task_service.py tests/unit/services tests/migration -k replan
# exit 0: 42 passed, 397 deselected, 11 warnings in 3.37s
```

验证覆盖重规划/NOTIFICATION 入队路径不触发 `smtplib.SMTP`、请求返回时 outbox 为 pending、worker 独立 Session 绑定 dispatcher、既有 resume/补偿与 replan service 回归。11 条 warning 均为既有 Pydantic v2 class Config 弃用提示。

## Step 6 真实主链短事务

- `redispatch()` 非 draft 路径通过 `start(idempotency_key)` 创建/复用任务，再由 `resume_async()` 按持久化 `current_step` 推进 F007/F021/F005/F006/NOTIFICATION。
- `ScheduleService.create_global_schedule()`、`confirm_schedule()`、`DispatchService.create_node_dispatch()`、`RouteService.create_route_planning()` 在 Saga 调用中统一传 `commit=False`；各步骤只 flush，task 步骤与业务数据由编排层一次 commit 同行落库。
- F007 执行器创建 draft 并挂版本链；F021 执行确认/打包并标记旧实体；F005 写批次/调度；F006 写 route；NOTIFICATION 将 task 完成与 outbox 同行提交。
- 重复 `idempotency_key` 从持久化步骤恢复；已完成任务直接重放结果，不重复创建方案、批次、路线或 outbox。
- 补偿边界：F007 可删除仍为 draft 的方案；F005 未发车批次标失败；F006 仅在批次未执行时删除路线；F021 commit 后故障进入 `manual_required`。

## Round 5 验证结果

```text
cd src/backend
python -m alembic -c alembic.ini heads
# exit 0: r2_03_outbox_claims (head)

python -m pytest -q -p no:cacheprovider tests/unit/services/test_replan_task_service.py tests/unit/services/test_outbox.py tests/unit/services/test_exception_service.py tests/migration tests/unit/core/test_model_registry.py
# exit 0: 90 passed, 3 warnings in 22.92s
```

新增真实链路测试覆盖：相同 key 重放无重复业务行、F007 下层真实写入后 commit 前异常整体 rollback、F021 已提交后注入异常进入 `manual_required`。通知失败时 outbox 保留由既有 `test_outbox.py` 回归覆盖。3 条 warning 是既有 Pydantic v2 class Config 弃用提示。

## Step 7 reroute 收口

- `reroute()` 复用 `replan_tasks` 的 `start(initial_step="F006", initial_status="RUNNING")` / `resume_async()`，直接从 F006 初始化，再按 F006 → NOTIFICATION → COMPLETED 推进。
- RouteService 使用 `commit=False`；route 版本链与 task 步骤由编排层一次提交。NOTIFICATION 与 outbox 同行提交。
- 相同 idempotency key 完成后重放持久化 route 结果，不重复创建 route/outbox。
- F006 route 写入后、commit 前异常整体 rollback；提交后检测为已执行的异常进入 `manual_required`，未执行路线可由补偿器删除。

## Round 7 验证结果

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/services/test_exception_service.py -k reroute
# exit 0: 7 passed, 32 deselected in 0.68s

python -m pytest -q -p no:cacheprovider tests/unit/services/test_replan_task_service.py tests/unit/services/test_outbox.py tests/unit/services/test_exception_service.py tests/migration tests/unit/core/test_model_registry.py
# exit 0: 93 passed, 3 warnings in 15.86s
```

## Round 8～11 收口证据

### 第一优先：`3965855` Saga 恢复加固

- HTTP 层将 `X-Idempotency-Key` 贯通到重规划 Saga。
- 补偿成功后恢复 `current_step`，避免任务停留在错误推进状态。
- 持久化并重放任务产物引用，避免完成任务丢失返回对象。
- redispatch 版本链覆盖 `1 → 2 → 3`。
- 聚焦测试结果：**114 passed**。

### 第二优先：`ffba2f0` 真实集成覆盖

- `tests/integration/test_exception_replan.py` 已移除 TODO/空 `pass`。
- 使用真实 HTTP 请求与 `X-Idempotency-Key` 验证重放、恢复和错误边界。
- `tests/integration/test_exception_replan.py` 与 `tests/api/test_exceptions.py` 合计：**20 passed**。

### 第三优先：`71e7506` leased outbox claims

- outbox 增加 `processing`、`claim_token` 与 lease 字段。
- worker 通过原子 claim 防止并发领取同一事件；过期租约可回收。
- 新增独立 Session worker：`src/backend/scripts/outbox_worker.py`。
- 聚焦测试结果：**101 passed**。
- Alembic 当前唯一 head 推进为 `r2_03_outbox_claims`。

### 第四优先：`ffec6bb` 完整后端回归

- `test_release_migrate.py` 的发布迁移期望 head 更新为 `r2_03_outbox_claims`。
- 完整后端测试（不同于上述聚焦测试）：

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests
# exit 0: 899 passed, 269 warnings in 173.43s

python -m alembic -c alembic.ini heads
# exit 0: r2_03_outbox_claims (head)
```

**证据分层说明**：114、20、101、24 passed 分别证明特定功能与故障边界；908 passed 是当前完整后端回归。不得将这些数字混写成同一组测试结果，也不得用完整回归替代聚焦场景说明。SQLite 结果只辅助验证 P0 schema/幂等/租约协议，不代表 PostgreSQL、多 worker 或生产并发能力。

## Round 12 task execution claims 收口

### 第五优先：`ea4415a` replan task execution claims

- `replan_tasks` 增加 `claim_token`、`claimed_by`、`claimed_step`、`claimed_at` 与 `lease_until`。
- 步骤执行通过条件更新抢占租约；默认租约 300 秒，过期可回收。
- 推进、补偿与 `manual_required` 均以 claim token + version fencing；过期后的旧 token 不能 finalize，也不能提交业务写入。
- `reroute()` 改为 `start(initial_step="F006", initial_status="RUNNING")`，不再先创建 F007 再改写步骤。
- Alembic 当前唯一 head 推进为 `r2_03_replan_task_claims`。

### 并发/任务聚焦测试：`c7f49aa`

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/services/test_replan_task_service.py tests/unit/services/test_replan_task_concurrency.py
# exit 0: 24 passed, 2 warnings in 1.60s
```

24 项 = `test_replan_task_service.py` 17 项 + `test_replan_task_concurrency.py` 7 项。
覆盖活跃 lease 阻塞、过期 lease 回收、旧 token fencing、并发 resume 只执行一次、并发 NOTIFICATION 只写一条 outbox，以及相同/不同 fingerprint 的并发 start。

### 完整后端回归

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests
# exit 0: 908 passed, 271 warnings in 184.88s

python -m alembic -c alembic.ini heads
# exit 0: r2_03_replan_task_claims (head)
```

## 功能分支提交（`87190d2` 之后，oldest → newest）

- `e8f3203` — `feat: add R2-03 replan task skeleton`
- `9aeabe4` — `feat: add replan task recovery orchestration`
- `f652947` — `feat: add transactional outbox delivery`
- `8b8bc61` — `feat: route replan notifications through outbox`
- `e7ad8ff` — `feat: wire replan saga short transactions`
- `fa716dc` — `docs: record R2-03 saga implementation evidence`
- `9e78068` — `feat: wire reroute through replan saga`
- `3965855` — `fix: harden replan saga recovery`
- `ffba2f0` — `test: add real replan saga integration coverage`
- `71e7506` — `fix: add leased outbox delivery claims`
- `ffec6bb` — `test: update release migration head expectation`
- `17b4f73` — `docs: record R2-03 implementation evidence`
- `ea4415a` — `feat: add replan task execution claims`
- `c7f49aa` — `test: cover concurrent replan task execution`

远程分支已存在：`origin/feat/R2-03-replan-saga-outbox` @ `ffec6bb`；本地相对远程 ahead 4。当前尚无 R2-03 PR，未执行 push。

## 明确未覆盖

- `redispatch(draft_only=True)` 仍走旧路径，不属于已接入 Saga 的非 draft 主链；
- 已将重规划成功路径迁到 outbox，并提供独立 Session worker；尚未执行真实 SMTP/Webhook 投递验证；
- 若外部邮件/Webhook 不支持幂等令牌，worker 在外部成功后、`delivered` 写回前崩溃可能造成重复投递，因此语义为 at-least-once，不是 exactly-once；
- 未剥离其他非重规划调用点的 fire-and-forget 或同步 SMTP；
- 未执行 PostgreSQL/Redis/Docker/真实 SMTP/Webhook 验证，也未做独立 worker 进程重启；R2-05 保持 `blocked`；
- R2-03 计划卡保持 `pending`，直到授权创建 PR、CI 通过并 merge；下一动作仅为待授权后创建 R2-03 PR，不开始 R2-04B。未获明确授权前不执行 `git push` 或创建 GitHub PR。

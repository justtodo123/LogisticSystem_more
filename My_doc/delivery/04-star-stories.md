# 后端面试 STAR 故事

> 每个故事都包含 30 秒版本、2 分钟主版本、追问入口和边界。数字以 [Claim-to-evidence 台账](02-claim-evidence-ledger.md) 为准；现场不必一次背完所有 run ID，但必须知道证据放在哪里。

## 通用讲述模板

- **Situation**：线上会出现什么错误，而不是“我想用某个技术”。
- **Task**：明确要守住的不变量和验收标准。
- **Action**：先讲约束与取舍，再讲实现。
- **Result**：说明环境、规模和结果。
- **Boundary**：主动说明还没有证明什么。

---

## Story 1：把 Schema 从“能启动”变成可审计迁移

### 30 秒版本

项目早期同时存在多个 Alembic head、运行时 `create_all()` 和手写 SQLite DDL，`stamp head` 还能把未知数据库伪装成最新状态。我把模型 metadata 收敛到统一 registry，建立单一正式 head，并按 fresh、已受 Alembic 管理的旧库、已知混合 SQLite、未知结构和 drift 分类处理。发布脚本只对可证明安全的状态迁移，其余 fail closed。这样 schema 变更从“应用启动时碰运气”变成了可复现、可审计的 release gate。

### 2 分钟主版本

**Situation**

项目迭代后出现了三类风险：迁移图有多个 head；部分代码在运行时 `create_all()` 或执行手写 DDL；历史 SQLite 可能既有业务表又没有可信的 `alembic_version`。如果直接执行 `stamp head`，只会改版本标签，并不能证明真实 schema 与 ORM 一致。

**Task**

我定义了三个不变量：

1. 正式 schema 只有一个迁移真相源；
2. 应用和 worker 启动不执行 DDL；
3. 只有已识别且经过验证的数据库状态才能自动前进，未知状态必须停止。

**Action**

- 建立统一模型 registry，让 Alembic metadata 覆盖全部正式模型；
- 新增 schema convergence revision，收敛历史分支为单一 head；
- 移除 runtime DDL，把迁移前置到 `release_migrate.py`；
- 识别 fresh、Alembic-managed legacy、known mixed SQLite、unknown revision、多版本行和 metadata drift；
- 对 known mixed 状态先校验预期结构，再走受控升级；对未知/漂移状态 fail closed；
- 用 fresh、legacy、parity 和错误状态测试固定行为。

**Result**

R2-00A 经 PR #5 和 CI `32932228092` 验收；该阶段记录的迁移相关完整运行是 718 passed、209 warnings。更重要的结果是发布路径不再依赖 `stamp head` 或应用启动时建表。

**Boundary**

这证明了迁移协议和自动化 gate，不代表我已经在本机 Docker 或真实生产数据库完成升级演练。生产迁移仍要备份、受控执行和验证。

### 典型追问

**Q：为什么不能自动修所有 drift？**

A：未知 drift 没有可靠意图，自动 DDL 可能删除数据或错误补列。release gate 的职责是阻止不确定状态进入发布，而不是猜测修复。

**Q：`stamp head` 什么时候能用？**

A：只有数据库 schema 已经通过外部方式被严格证明与目标 revision 等价时，才可能作为受控登记动作；不能用它绕过迁移失败。

**证据入口**：[R2-00A](../plan_todo/00A-alembic-migration-baseline.md)、[架构说明](03-architecture-and-flows.md#1-系统上下文)。

---

## Story 2：用 CAS 消除确认流程重复副作用

### 30 秒版本

调度确认、到货确认和 AI 建议确认原来是 read-check-write，两个请求可能同时读到待确认状态并重复生成事件或通知。我改为带 expected state 的条件更新，用 `rowcount` 决定谁获得执行权，并强制 CAS 先于所有副作用。SQLite 独立 Session 的 20 和 100 竞争者测试中都最多只有一个成功，其余返回稳定 `40901`，且没有重复副作用。

### 2 分钟主版本

**Situation**

确认接口通常先查询当前状态，应用判断是 `PENDING` 后再更新。如果两个请求并发，它们都可能通过读取检查，随后重复修改订单/货物、创建事件并发通知。这不是简单加一个 Python lock 就能解决的，因为部署到多 worker 后进程锁不共享。

**Task**

需要守住两个不变量：

- 同一业务对象从同一 expected state 最多一个请求成功；
- 失败的 contender 不得产生任何领域副作用。

**Action**

- 抽出 CAS helper，执行 `UPDATE ... WHERE id=? AND state=?`；
- 用 `rowcount == 1` 判断当前事务是否成为赢家；
- `rowcount == 0` 映射为稳定的状态冲突 `40901`；
- 把 CAS 放在关联实体更新、事件和通知之前；
- 状态和必要副作用在短事务中提交，外部通知放在提交后并交给可靠通知机制；
- 为 schedule、arrival 和 AI suggestion confirmation 建立独立 Session 并发测试。

**Result**

20/100 contender 场景均最多一个成功，其他请求获得可识别冲突；测试还核对了没有重复包装、事件或通知副作用。R2-01 通过 PR #8 / CI `33047947336` 合入。

**Boundary**

这些 SQLite 独立 Session 测试证明了 CAS 不变量和副作用顺序，不是 PostgreSQL 多 worker 的性能上限。P1 后续在 PostgreSQL 拓扑复跑协议，但容量数字要按具体场景单独引用。

### 典型追问

**Q：悲观锁不是更直接吗？**

A：CAS 对短状态转换更轻，冲突结果清晰，也减少持锁范围；如果后续出现必须读取多行并基于其组合决策的场景，再考虑行锁和统一锁顺序。

**Q：为什么通知不在锁内？**

A：网络调用延迟不可控，会扩大锁时间和失败面。状态先提交，通知通过 outbox 恢复。

**证据入口**：[R2-01](../plan_todo/01-concurrency-state-transitions.md)、[CAS 实验](../plan_todo/experiments/20260827-R2-01-cas-state-transitions.md)。

---

## Story 3：跨 worker 幂等与原子业务编号

### 30 秒版本

原方案采用“先查再执行再缓存”和进程内编号，在多 worker 下有 TOCTOU 和重复编号风险。我把幂等记录设计为数据库 `PROCESSING/SUCCEEDED/FAILED/EXPIRED` 状态机，加入 payload fingerprint、claim token 和 exact response replay；Redis 只做成功后的 best-effort cache。同时用 `code_ranges` 条件更新分配号段。独立写路径完成 600/600 replay 且无重复副作用；PostgreSQL 16、8 workers 下完成 100,000 次唯一连续编号分配。

### 2 分钟主版本

**Situation**

幂等如果只做“缓存里查 key，没有就执行”，两个 worker 能同时 miss 并重复执行。编号如果用 `max+1` 或进程内序号，也会在并发、重启和多实例下冲突。Redis 可提升速度，但不能成为唯一正确性来源，因为它可能被清空、超时或降级。

**Task**

- 同一 key + 同一 payload 只能有一个当前 owner，完成后可精确重放；
- 同一 key + 不同 payload 必须冲突；
- owner 回收后旧请求不能覆盖新结果；
- 业务编号在多 worker 下唯一、连续并可恢复。

**Action**

- 在数据库记录 `PROCESSING/SUCCEEDED/FAILED/EXPIRED`；
- claim 时原子写入 fingerprint 和 token；
- 其他请求看到 `PROCESSING` 返回 `40902 + Retry-After`，fingerprint 不同返回 `40903`；
- 成功时存储 status、原始 response bytes、media type 和安全 headers，用于 exact replay；
- finalize 必须携带 claim token，防止旧 owner 的迟到写；
- Redis 只在成功提交后缓存 replay 结果，失败时回数据库；
- 编号使用 `code_ranges` 条件更新和有限重试，并处理宽度耗尽。

**Result**

协议测试覆盖 20/100 同 key contender。P1 独立写场景完成 600/600 replay、0 unexpected 5xx、数据库 600 个唯一节点且无残留 `PROCESSING` outbox，写 P95 27.66 ms。独立号段实验在 PostgreSQL 16、8 workers 下完成 100,000 claims，516.578 秒、193.6 claims/s、P95 158.342 ms、P99 294.859 ms，唯一、连续、恢复均通过。

**Boundary**

我不会称它为 exactly-once：业务副作用事务和幂等 `mark_succeeded` 仍不是一个不可分割提交。准确表述是数据库持久化幂等、owner fencing 和可恢复 replay。100,000 claims 也只是编号分配实验，不是完整订单写入吞吐。

### 典型追问

**Q：为什么保存 response bytes，而不是重新序列化对象？**

A：重新序列化可能受代码版本、字段默认值或顺序影响。保存最终响应可以保持 status、body、media type 和协议头一致。

**Q：Redis 为什么不是分布式锁？**

A：核心业务已经有数据库事务，使用同一持久化源更容易维持 claim 和业务状态的可审计性；Redis 在项目中是可选依赖，故障时不能破坏正确性。

**证据入口**：[R2-02](../plan_todo/02-idempotency-and-code-generation.md)、[写路径基线](../plan_todo/experiments/20260903-R2-06-write-path-baseline.md)、[R2-05](../plan_todo/05-postgresql-redis-resilience.md)。

---

## Story 4：用 Saga/outbox 处理重规划与通知失败

### 30 秒版本

异常重规划包含多个提交点，网络通知又不能和数据库形成原子事务。我的方案是持久化 Saga task 和 step state，用 lease + claim token 支持 worker 回收，用 stale-token fencing 拒绝旧 worker 迟到写；领域变化与 outbox event 同事务提交，再由独立 worker retry/dead-letter。这样可以明确恢复、补偿和 `manual_required`，但外部 sender 无幂等能力时仍诚实地定义为 at-least-once。

### 2 分钟主版本

**Situation**

重规划不是一个单表更新：它可能先生成候选、保存差异、变更调度状态，再发送邮件/Webhook。进程在任一步崩溃时，仅靠内存无法知道已完成什么；如果业务提交后直接调外部服务，还会出现业务成功但通知丢失，或者超时重试造成重复投递。

**Task**

- 任务进度必须可恢复；
- 同一步不能被两个 worker 同时有效完成；
- 旧 worker 恢复后不能覆盖新 worker；
- 业务状态和待发送事件不能出现 dual-write 缝隙；
- 自动补偿失败时必须暴露人工处理状态。

**Action**

- 把 replan task 和每一步状态持久化；
- claim 时写入 lease deadline 和 token，执行时保持短事务；
- lease 过期后新 worker 可以 reclaim，所有 finalize 都校验 token；
- 按步骤记录 retryable failure、compensated 或 `manual_required`；
- 在业务事务中同时插入 outbox event；
- 独立 worker 使用自己的 Session claim 事件，发送成功后按 token 标记；失败进入退避重试，耗尽后 dead-letter；
- trace metadata 随 outbox 传播，便于从 HTTP 定位到 retry/dead-letter。

**Result**

测试矩阵覆盖 rollback、compensation、manual-required、lease reclaim、stale claim rejection、retry/dead-letter 和 duplicate suppression；记录有 101 个 outbox claim/lease focused tests 与 24 个 replan concurrency tests。P1 又覆盖 worker restart 和 lease reclaim。

**Boundary**

transactional outbox 关闭的是“数据库业务提交与事件入队”的缝隙，不会自动让外部服务 exactly-once。邮件/Webhook 如果不接受幂等键，接收方仍可能看到重复，因此语义是 at-least-once，并需要接收方去重或幂等 API。

### 典型追问

**Q：为什么不用一个长事务做完？**

A：算法和网络调用耗时不可控，长事务会占用连接和锁，也无法覆盖外部系统原子性。Saga 用显式状态和补偿换取可恢复性。

**Q：lease 和 token 为什么都要有？**

A：lease 决定何时允许接管；token 决定谁仍有提交资格。只有 lease 没有 token，旧 worker 在暂停后恢复仍可能覆盖新结果。

**证据入口**：[R2-03](../plan_todo/03-replan-saga-and-outbox.md)、[Saga/outbox 实验](../plan_todo/experiments/20260829-R2-03-replan-saga-outbox.md)。

---

## Story 5：从生产近似验证到零 exception 安全发布

### 30 秒版本

为了避免“单机测试绿就宣称完成”，我把 P0 协议搬到 GitHub Actions 的 PostgreSQL 16、Redis 7、两个 Uvicorn worker 和独立 outbox worker 中，注入 Redis pause、worker restart、数据库断连、pool timeout 等故障，再分开做 read、spike、write、confirm 和 2h soak。发布端先构建但不推送，生成 SBOM、用 Trivy 按版本化 policy fail closed；初始基础镜像被 CRITICAL/HIGH 阻断后，没有放宽策略，而是切换到含修复包的发行版，最终零 exception 推送不可变 SHA 镜像。

### 2 分钟主版本

**Situation**

P0 的 SQLite 测试能证明协议，但不能说明 PostgreSQL、多 worker 和 Redis 故障下仍然成立。与此同时，原 CD 如果先推镜像再扫描，会把有阻断漏洞的产物发布出去。初始扫描确实发现 backend 3 个 CRITICAL/15 个 HIGH、frontend 2 个 CRITICAL/35 个 HIGH，主要来自 OS 基础层。

**Task**

我把目标拆成两部分：

1. 在生产近似拓扑验证协议、故障恢复和可观测性；
2. 保证只有通过安全 policy 的同批次镜像才能发布，并保留审计证据。

**Action**

- GHA 使用 PostgreSQL 16、Redis 7、两个独立 HTTP worker 和 outbox worker；
- 验证 migration、幂等 replay、outbox reclaim、Redis pause/recovery、deadlock/serialization retry、pool timeout、短暂断连和备份恢复；
- 建立 request/trace/task ID、结构化脱敏日志和 HTTP → outbox → worker trace 传播；
- 把 read-mix、spike、write、confirm、soak 拆成独立实验，只对相同参数 baseline/candidate 做 15% 相对回归判断；
- CD 先 build、生成 CycloneDX SBOM、Trivy 扫最终镜像、按版本化 policy 评估并上传 artifact；通过后才登录 GHCR；
- 第一轮只加 OS upgrade 后 backend 仍被 Debian trixie 的 no-dsa/postponed 包阻断，于是切换到 forky；frontend 切换 Alpine 3.24；全程没有放宽 policy 或先加 exception。

**Result**

P1 故障矩阵和跨 worker 限流通过。read-mix/spike 均 0% failed；独立 write 600/600 replay；confirm 8 contenders 为 1 success/7 conflicts；2h soak 为 0 errors、0 unexpected 5xx、0 dropped，预热后 RSS 约 1.002x。最终 CD `33826520856` 在零 exception 下通过：backend 仅剩 1 个 MEDIUM report-only，frontend 无漏洞，然后发布 backend/frontend 同一 `f9e08a4...` SHA tag。

**Boundary**

GHA 拓扑不是生产部署；不同脚本 P95 不直接比较；2h 不能证明永久无泄漏；应用级 trace 不是完整 OTel；发布门禁不是定时扫描；镜像扫描通过也不代表本机 Compose、02B E2E 或生产拉起完成。

### 典型追问

**Q：为什么不直接为 CVE 加 exception？**

A：先判断是否有修复路径。阻断项来自 EOL/修复节奏落后的基础层，切换到含 fixed package 的发行版可以消除，不需要用 exception 掩盖。最终残留只是 MEDIUM report-only。

**Q：为什么先 push SHA 再推进 latest？**

A：SHA tag 是不可变审计批次；两个镜像 SHA 都成功后再更新便利标签，避免 latest 指向半批次。审计和回滚始终使用 SHA。

**Q：9.81 ms 能称为系统 P95 吗？**

A：不能。只能说在约 5 分钟、8 RPS reads + 1 RPS login 的 read-mix 场景，混合 P95 为 9.81 ms；write、confirm、soak 各有独立指标。

**证据入口**：[R2-05](../plan_todo/05-postgresql-redis-resilience.md)、[R2-06](../plan_todo/06-observability-load-and-delivery.md)、[镜像扫描实验](../plan_todo/experiments/20260904-R2-06-image-scan.md)、[R2 收口](../plan_todo/20260904-R2-closeout.md)。

---

## 追问快速索引

| 追问方向 | 优先故事 | 一句话核心 |
|---|---|---|
| 数据库迁移/发布事故 | Story 1 | 先识别数据库状态，再迁移；未知状态 fail closed |
| 高并发/超卖/重复确认 | Story 2 | 条件更新把检查与抢占合一，赢家才有副作用资格 |
| 接口幂等/分布式锁 | Story 3 | 数据库是正确性源，Redis 是可选加速层 |
| 分布式事务/消息可靠性 | Story 4 | Saga 显式恢复，outbox 关闭数据库 dual-write 缝隙 |
| PostgreSQL/Redis/压测 | Story 5 | 按环境和场景给证据，不把 CI 冒充生产 SLA |
| DevSecOps/供应链安全 | Story 5 | 先扫描后发布，先修基础层，exception 是最后手段 |

## 最后 20 秒收束

> 这个项目最重要的变化不是多了多少接口，而是把几个容易在多实例下失败的隐含假设——启动时建表、先查再写、进程内幂等、直接发通知、扫描后置——改成了数据库不变量、恢复协议和 fail-closed 发布门禁。我能说明每个结论在哪个环境被验证，也会明确它还不能代表生产 SLA 或 exactly-once。

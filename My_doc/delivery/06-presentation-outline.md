# 项目展示 / PPT 提纲

> 推荐做 9 页主版本，再按面试时长裁剪。旧 `My_doc/pre-optimization/ppt/` 只借用视觉结构；本阶段不修改旧二进制 PPT，也不沿用其中的旧技术栈、旧角色/状态、2-opt 已实现或无证据效率数字。

## 统一叙事主线

> 我没有把第二轮优化做成“再加几个接口”，而是围绕多实例下容易失效的五个假设——schema 可随启动修补、先读后写不会竞争、进程内 key 足够幂等、数据库提交后直接发通知、镜像先发布后扫描——分别建立了迁移 gate、CAS、持久化状态机、Saga/outbox 和 fail-closed 发布门禁，并用分层实验说明结论与边界。

## 9 页主版本

### 第 1 页：项目与问题

**标题**：智能物流调度平台——从功能 MVP 到可验证工程交付

**页面内容**

- 业务链：订单 → 资源匹配 → 调度候选 → 人工确认 → 配送 → 异常重规划 → 报表/通知/审计；
- 技术栈：FastAPI、SQLAlchemy 2.0、Pydantic v2、Vue 3、TypeScript、PostgreSQL、Redis；
- R2 目标：一致性、恢复、权限、故障韧性、观测和安全发布。

**讲稿（约 45 秒）**

> 平台业务功能在第一轮已经基本完整，第二轮我把重点转向多实例和失败场景。核心问题不是页面能不能点击，而是两个请求同时确认怎么办、worker 崩溃后任务如何恢复、Redis 不可用是否破坏正确性、schema 漂移是否还能安全发布、镜像有阻断漏洞时流水线是否会停止。

**视觉建议**：一条横向业务链，不展示不稳定的 API/测试/表总数。

---

### 第 2 页：架构与验证分层

**标题**：应用分层 + 分层证据，而不是单一“测试通过”

**页面内容**

- Vue SPA → FastAPI → services/algorithms → PostgreSQL/Redis/outbox worker；
- P0：SQLite 独立 Session，证明协议不变量；
- P1：PostgreSQL 16 + Redis 7 + 2 HTTP workers + outbox worker，证明外部拓扑下仍成立；
- P2：load/spike/write/soak 与镜像门禁；
- Production：单独待验证。

**讲稿（约 60 秒）**

> 我把证据按层分开。SQLite 测试适合快速证明 CAS、幂等和恢复状态机；随后在 GHA 的 PostgreSQL、Redis 和多 worker 拓扑复跑协议并注入故障；性能和 soak 再按独立脚本记录。这样不会把 100 个 SQLite contender 说成 PostgreSQL 性能，也不会把 CI service container 冒充生产部署。

**视觉建议**：使用 [架构与核心流程](03-architecture-and-flows.md) 中“P1 验证拓扑”一节的图。

---

### 第 3 页：迁移治理

**标题**：Schema 单一真相源与 fail-closed release gate

**页面内容**

- 原问题：multiple heads、runtime DDL、mixed SQLite、`stamp head` 掩盖风险；
- 方案：统一 metadata registry、单一 head、状态分类、release migration；
- 不变量：未知 revision、未知结构和 drift 阻止启动；
- 证据：PR #5 / CI `32932228092`。

**讲稿（约 60 秒）**

> 迁移治理的核心不是“会写 Alembic”，而是明确哪些库可以自动升级。fresh、可信 legacy 和已知 mixed 状态分别验证；未知 revision、多行版本或 metadata drift 都 fail closed。应用和 worker 不再执行 DDL，发布阶段先过 migration gate。

**视觉建议**：状态分类漏斗：known → migrate；unknown/drift → stop。

---

### 第 4 页：CAS + 幂等 + 编号

**标题**：把并发正确性落到数据库不变量

**页面内容**

- CAS：expected-state 条件更新，赢家才执行副作用；
- 幂等：`PROCESSING/SUCCEEDED/FAILED/EXPIRED` + fingerprint + token + replay；
- 编号：`code_ranges` 条件更新替代 `max+1`；
- 结果：20/100 CAS 最多一个成功；600/600 replay；编号专项为 PostgreSQL 16、8 workers、100,000 claims。

**讲稿（约 90 秒）**

> 三个问题共同点是不能依赖进程内状态。CAS 把检查和抢占合成一个 UPDATE；幂等 owner 落在数据库，Redis 只作成功后的缓存；号段也用条件更新。这里我会主动区分三组证据：SQLite contender 是协议测试，600 replay 是独立 HTTP 写场景，100,000 claims 是 PostgreSQL 编号规模实验。

**视觉建议**：左侧 CAS sequence，右侧幂等 state machine；数字只放三个。

---

### 第 5 页：Saga + transactional outbox

**标题**：长业务流程和外部通知的可恢复性

**页面内容**

- persistent task / step state；
- lease + claim token + stale-token fencing；
- 业务变更与 outbox event 同事务；
- 独立 worker retry / dead-letter；
- compensation 失败进入 `manual_required`。

**讲稿（约 75 秒）**

> 我没有用一个长事务包住算法和网络，而是用 Saga 记录进度，用 lease 决定何时接管、token 决定谁能提交。业务变更和 outbox event 同事务关闭 dual-write 缝隙。外部发送仍诚实定义为 at-least-once，因为 sender 不支持幂等时接收端可能看到重复。

**视觉建议**：使用 [架构与核心流程](03-architecture-and-flows.md) 中“Replan Saga + transactional outbox”一节的 sequence。

---

### 第 6 页：P1 故障韧性与权限

**标题**：在 PostgreSQL/Redis/多 worker 中复跑协议

**页面内容**

- Redis pause → 可见降级 → recovery；
- worker restart replay / outbox reclaim；
- deadlock/serialization retry、pool timeout、短暂断连；
- JWT `token_version` 撤权；
- 跨 worker 登录限流 5 attempts / 60 s。

**讲稿（约 60 秒）**

> P1 不只是把测试数据库换成 PostgreSQL。我启动两个独立 HTTP worker 和 outbox worker，验证共享限流、Redis 中断后的进程内降级、恢复后重新共享，也覆盖数据库死锁/序列化失败、连接池超时和短暂断连。权限侧旧 JWT 通过 token_version 失效，未知角色 fail closed。

**视觉建议**：故障注入矩阵，列为注入、预期、结果、边界。

---

### 第 7 页：观测与负载证据

**标题**：每个性能数字都有场景，不混用 P95

**页面内容**

- request/trace/task ID + JSON 脱敏日志；
- read-mix：约 5m，0% failed，混合 P95 9.81 ms；
- write：600/600 replay，P95 27.66 ms；
- confirm：8 contenders，1/7，P95 836.7 ms；
- 2h soak：0 errors，RSS post-warmup 约 1.002x。

**讲稿（约 75 秒）**

> 这些数字不能放进同一条曲线比较。read-mix 包含读取和登录，write 是独立幂等场景，confirm 是竞争场景，soak 关注长时间错误率和 RSS。只有相同脚本、相同参数的 baseline/candidate 才进入 15% 相对回归门禁。2h 只说明该窗口没有观察到明显持续增长，不代表永久无泄漏。

**视觉建议**：四张独立小卡，不画误导性的统一折线。

---

### 第 8 页：供应链安全发布

**标题**：先扫描，后发布；exception 是最后手段

**页面内容**

- Build（不推）→ CycloneDX SBOM → Trivy → versioned policy → artifact → SHA push → latest；
- 初始阻断：backend 3 CRITICAL/15 HIGH，frontend 2 CRITICAL/35 HIGH；
- 先升级/切换基础镜像，不放宽 policy；
- 最终：blocked `[]`、exception `[]`，backend 1 MEDIUM report-only，frontend 无漏洞；
- immutable batch：`f9e08a4...`。

**讲稿（约 75 秒）**

> 第一轮只加 OS upgrade 后，backend 仍受 Debian trixie no-dsa/postponed 影响，重复升级拿不到不存在的 fixed package。我没有直接加 exception，而是切换到含修复包的 forky；frontend 切换 Alpine 3.24。门禁通过后才登录 GHCR，先推两个 SHA tag，再推进 latest。审计和回滚只认 SHA。

**视觉建议**：绿色/红色 gate 流程；突出 `zero exception` 而不是“零漏洞”。

---

### 第 9 页：结果、边界与复盘

**标题**：工程交付完成，不把 CI 结果夸大成生产结论

**页面内容**

**已完成**：R2-00～R2-06、P0/P1 协议与故障验证、分场景容量证据、2h soak 绝对值、安全发布门禁。

**独立后续**：Compose/02B/生产拉起、回滚演练、Grafana/Prometheus/OTel、跨 worker 指标聚合、定时扫描、完整读写组合容量。

**讲稿（约 45 秒）**

> 当前可以冻结代码并进入交付：工程基座、协议和自动化证据已经闭环。没有完成的是生产环境验收和可选 P2 能力，它们被单独登记，不会反过来改写 R2 状态。这个项目让我形成的核心方法是：先定义失败模式和不变量，再选择最小机制，最后用分层证据和明确边界收口。

**视觉建议**：已验证 / 未验证双栏，结尾放二维码或仓库文档入口（只在仓库公开且适合分享时使用）。

## 时长裁剪

### 5 分钟版本（5 页）

1. 项目与问题（30 秒）；
2. 架构与证据分层（45 秒）；
3. CAS + 幂等 + 编号（90 秒）；
4. Saga/outbox + P1 故障（75 秒）；
5. 安全发布、边界和总结（60 秒）。

省略独立迁移页和详细性能页，只在问题或追问中展开。

### 10 分钟版本（推荐，8 页）

- 合并第 1/2 页为 75 秒；
- 第 3～8 页各 60～75 秒；
- 第 9 页 45 秒；
- 预留 60 秒切换或追问。

### 15 分钟版本（9 页 + 演示）

- 9 页讲解控制在 10 分钟；
- 按 [Demo Runbook](05-demo-runbook.md) 使用 5 分钟压缩演示；
- 如果面试官偏技术，跳过 UI，把 5 分钟用于 CAS/幂等和 outbox 白板追问。

## 视觉和文案规范

- 每页只保留一个结论、一个图和最多三个数字；
- 数字旁写环境/场景，不写无上下文的“大并发”“高性能”；
- 使用“通过”“验证”“观察到”，避免“绝对保证”“生产级”“永久”；
- Mermaid 图可先导出为 SVG/PNG 再放 PPT，但源文件仍以 [架构与核心流程](03-architecture-and-flows.md) 为准；
- 性能页不把不同测试的 P95 画在同一折线；
- 安全页写“零阻断、零 exception”，不能写“零漏洞”；
- Demo 截图不得出现 `.env`、token、cookie、个人信息或 CI 原始日志。

## 需要准备的展示素材

| 素材 | 来源 | 状态/要求 |
|---|---|---|
| 系统上下文图 | [架构与核心流程](03-architecture-and-flows.md) | 从 Mermaid 导出，保留边界注释 |
| CAS sequence | 同上 | 强调先 CAS 后副作用 |
| 幂等 state machine | 同上 | 标注不是 exactly-once |
| Saga/outbox sequence | 同上 | 标注外部 at-least-once |
| 发布 gate 图 | 同上 | 标注 scan-before-push 和 SHA tag |
| UI 截图 | 按 [Demo Runbook](05-demo-runbook.md) 从 Mock 环境采集 | 只截当前页面，不复用旧 UI 截图 |
| 数字小卡 | [证据台账](02-claim-evidence-ledger.md) | 复制时同时带环境/场景 |
| PR/CI/CD 链接 | 证据台账 | PPT 只显示精简 ID，讲稿保留完整链接 |

## 不能沿用的旧内容

- Python 3.11、MySQL optional 等旧栈描述；
- 423/421、626/645/664 等未绑定当前 run 的“总测试数”；
- 14 tables、固定 API 总数等易漂移统计；
- dispatcher/manager 两角色或旧状态机；
- 2-opt 已完整实现；
- “80% AI-generated code”“效率提升 3–5 倍”“一次评审通过率 90%+”等无当前证据说法；
- 把 HTTP Mock、GHA service topology 或镜像扫描成功写成生产部署完成。

## 答辩结束语

> 我能展示的不只是功能结果，还包括并发和失败情况下如何守住不变量、怎样留下可复现实验证据，以及哪些结论还不能外推。当前 R2 已完成工程收口；如果进入生产阶段，下一步会在固定 SHA 镜像上做 Compose、release migration、02B E2E、回滚与备份恢复，而不是重新修改已经冻结的协议。

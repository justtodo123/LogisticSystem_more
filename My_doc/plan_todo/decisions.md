# 第二轮冻结决策

> 状态：已冻结（2026-08-25）；同日追加治理基线 `v2026-08-25-r2-governance`。P0 按本文件执行，不再把下列项标为 `needs_decision`。
> 变更须新增条目并改版本，禁止静默改验收语义。
> 协议冻结版本：`v2026-08-25-r2-freeze`。
> 当前治理增补版本：`v2026-08-25-r2-governance`。

## D-R2-ENV 证据环境

- **P0 环境**：本机 Windows 11 + Python 3.13.3 + 现有 pytest + SQLite。不安装 Docker Desktop，不因本机无 Docker/PostgreSQL/Redis 把 P0 标 `blocked`。
- **P1 环境**（就绪一条即可，优先从上到下）：
  1. GitHub Actions `ubuntu-latest` + Postgres/Redis service container（首选，本机无 Docker/WSL）
  2. 本机 4GB Ubuntu Server 虚拟机 + Docker Engine（不是 Desktop）
  3. 云主机 + Docker Engine
- **禁止**：Windows 宿主安装 Docker Desktop（飞连曾拦截）。
- 第一轮 `02` 仍为 `mitigated`（仅 02A）。P0 不依赖 02B；P1/`R2-05` 独立验收，不得把第一轮 02 默认为通过。

## D-R2-DB 正确性边界

- SQLite：开发与协议测试辅助。允许独立 Session 并发测试，报告必须写明 SQLite 写锁会串行化，**不能**写成生产并发证明。
- PostgreSQL：P1 的并发、恢复、多 worker 正确性证据。
- P0 代码必须方言安全：`check_same_thread` 仅 SQLite；新增表/列走 Alembic，停止在 `config/database.py` 堆 SQLite `ALTER TABLE`。

## D-R2-CONFLICT 并发确认冲突

- 无幂等键或不同幂等键：同一 draft **最多一次成功**（2xx）；其余 HTTP `409` + 业务码 `40901`，**不**重放成功响应体。
- 同幂等键 + 同 payload：走 `D-R2-IDEM`（成功后重放原始 HTTP status 与 body）。
- 禁止把第二次确认伪装成 `200` 成功。

## D-R2-IDEM 幂等协议

- **真相源**：数据库 `idempotency_records`（扩展 `status` / `payload_hash` / `http_status` / 必要 header），`UNIQUE(idempotency_key)`。
- 状态机：`不存在 → PROCESSING → SUCCEEDED | FAILED | EXPIRED`。
- 占位：`INSERT` 抢占；唯一冲突则读取已有行。
- 同 key、不同 payload hash：`409` + `40903`。
- 同 key 且 `PROCESSING`：`409` + `40902`，可带 `Retry-After`；**不**在请求内长轮询。
- Redis 只缓存 `SUCCEEDED` 响应。Redis 不可用时继续打数据库，**禁止**用进程内 dict 冒充分布式幂等。
- TTL 24h；请求体上限 1MB。
- **P0 强制携带** `X-Idempotency-Key` 的写接口：
  - `POST /api/schedule/global`
  - `POST /api/schedule/confirm/{schedule_code}`
  - `POST /api/simulation/confirm-arrival`
  - `POST /api/simulation/confirm-arrival-batch`
  - `POST /api/ai/suggestions/{suggestion_id}/confirm`
  - `POST /api/ai/suggestions/{suggestion_id}/reject`
  - `POST /api/exceptions/{event_code}/replan`
  - `POST /api/exceptions/replan/batch`
- 其他写接口：有 key 则走同一中间件，无 key 不强制。

## D-R2-CODE 业务编号

- 保留 `GS_` / `PKG_` / `RT_` / `DB_` 等可读前缀与对外形态。
- 禁止 `max + 1` / `count + 1` / 进程序号。
- P0：号段表（资源 + 前缀 + `next_value`）条件更新抢号；已有唯一约束保留；唯一冲突有限重试，耗尽后返回可识别业务码，不升未知 `500`。
- 不把 ULID / UUIDv7 作为对外业务编号。

## D-R2-SAGA 补偿边界

| 步骤 | 已提交后 | 自动补偿 | 否则 |
|---|---|---|---|
| F007 生成 draft | draft 行存在 | 删除或作废 draft | — |
| F021 确认 + 打包 | draft→active 且包裹/订单已改 | 无（提交前 rollback） | `manual_required` |
| F005 节点调度 | 批次/调度单已写 | 未发车可作废批次 | 已 `in_transit` 则 `manual_required` |
| F006 路径规划 | route 已写 | 路线未执行可删 | 否则 `manual_required` |
| 通知 | outbox 与业务同行提交 | 不回滚业务；worker 重试 | 死信 + 人工重放 |

旧方案与 `delivered` 终态保持第一轮不变量。不具备可靠补偿的步骤必须进入 `manual_required`，禁止静默多次 `commit` 后当成功。

## D-R2-TOKEN 会话

- 本轮不实现 refresh token。
- 沿用 access token + `user.token_version`：logout / 禁用 / 改角色时 `version + 1`，旧 token 拒绝。
- 登录响应 `expires_in` 必须等于 `settings.JWT_EXPIRE_SECONDS`。

## D-R2-ERROR 错误契约

- 对外唯一形状：`{code, message, data, meta}`。
- `DomainError` → HTTP status + 业务 code；`message` 不泄漏 SQL / 第三方原文。
- `get_db` 异常路径必须 `rollback`。
- FastAPI `detail` 只作内部映射，文档不再并列两套对外契约。

## D-R2-RBAC 权限

- 路由从 `require_dispatcher` / 仅登录 迁到 `require_permission`。
- 到货确认 P0 仍仅 dispatcher/admin（权限位 `schedule:confirm` 或新增 `arrivals:confirm`，只授这两角）。
- `warehouse_operator` / `manager` 不开放到货确认写。
- 未知角色 fail closed。

## D-R2-OBS 观测与压测裁剪

- P1 最小集：`request_id` / `trace_id` / `task_id`、结构化 JSON 日志、核心计数、一份 load + 一份 spike（5～15 分钟）。
- soak、Grafana、完整告警、镜像安全扫描：P2，不阻塞 P1 `done`。

## D-R2-CI P1 证据入口

- P1 首选：GitHub Actions 增加 Postgres/Redis services，复跑 `01`～`03` 并发与恢复测试。
- 本机无 Docker 时，`R2-05` 保持 `blocked`，不得用 SQLite 结果代替。

## D-R2-DOC-TRACKING 文档与证据追踪边界

- 自 `v2026-08-25-r2-governance` 起，`My_doc/` 正式纳入 Git 追踪；现行计划、冻结决策、实验模板、历史资料与小型脱敏实验摘要均可审查和版本化。
- 根 `.gitignore` 不再整目录忽略 `My_doc/`；由根规则与 `My_doc/.gitignore` 共同排除依赖目录、预览、数据库、日志、实验 `raw/` / `artifacts/` / `tmp/` 等可再生成或大体积产物。
- 凭据、`.env`、JWT/cookie、私钥、含口令 DSN、个人数据和未脱敏业务数据禁止进入 Git。大型原始结果保存到 CI artifact 或受控外部存储，报告登记大小、SHA-256、位置、脱敏检查和保留期限。
- 完成记录只能引用已经存在的 commit、PR、CI run 和实验产物；禁止提前写“工作区干净”“已提交”“已合并”或“已通过”。

## D-R2-MIGRATION-BASELINE Schema 真相源

- `R2-00A` 是 R2-01、R2-02、R2-03、R2-04B 和 R2-05 中 schema 变更或迁移验证的前置基线。
- 正常启动与部署由 Alembic 管理正式 schema；`Base.metadata.create_all()` 如保留，只能用于明确隔离的测试辅助，不能继续充当运行时迁移。
- 当前双 head `c78f9b436833` 与 `phase7_exception_fields` 共同源于 `17b1974d0918`。后者修改 `exception_events`，但父链未创建该表；禁止用空 merge revision 掩盖 fresh 数据库缺表或 schema parity 问题。
- 必须覆盖 fresh、受 Alembic 管理的 legacy、无 `alembic_version` 的混合旧 SQLite 三类路径；未知 schema fail closed。迁移前备份，验证单 head、幂等升级、模型/Alembic parity 和可恢复回滚。
- 本决策不代表本轮治理文档已经生成 revision 或执行升级；实现仅在 R2-00A 中进行。

## D-R2-ERROR-COMPAT 错误契约兼容期

- `R2-04A` 建立错误码登记表与 `DomainError`，统一对外 envelope 为 `{code, message, data, meta}`；HTTP status 与业务 code 分别表达传输和领域语义。
- `40901`（状态冲突）、`40902`（幂等处理中）、`40903`（同 key 不同 payload）必须登记 HTTP status、公开 message、owner 与调用方，业务实现禁止硬编码裸数字。
- 兼容期由全局处理器接管 `DomainError`、`HTTPException`、请求校验、数据库异常和未处理异常。旧 `HTTPException.detail` 的字符串或字典须转换到统一 envelope，并保留原 HTTP status；未知旧错误使用登记的通用 code，不把 SQL、第三方原文或内部 cause 暴露给客户端。
- 内部 cause 和诊断上下文只进入已脱敏日志。`get_db` 异常路径必须 rollback、重新抛出，最终 close。
- 旧 `detail` 只在完成路由迁移清单、调用方兼容验证和契约测试后移除；新增接口不得继续扩散第二套对外形状。

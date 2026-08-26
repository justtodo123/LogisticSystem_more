---
plan_id: "R2-00A"
title: Alembic 迁移基线与 Schema 真相源治理
status: in_progress
priority: P0
owner: justtodo123
created: 2026-08-25
updated: 2026-08-26
depends_on: ["R2-00"]
---

# R2-00A — Alembic 迁移基线与 Schema 真相源治理

## 来源证据与当前行为

- 当前 Alembic 图有两个 head：`c78f9b436833` 与 `phase7_exception_fields`，共同父 revision 为 `17b1974d0918`。
- `phase7_exception_fields` 修改 `exception_events`，但其父链没有创建该表；只新增空 merge revision 不能使 fresh 数据库可升级。
- 应用启动链目前是 `main` → `init_db()` → 导入模型 → `Base.metadata.create_all()` → `_run_phase1_migrations()` → `_run_phase4_migrations()`。
- `config/database.py` 仍含约 15 个手写 SQLite `ALTER TABLE ADD COLUMN` 与 7 个运行时索引创建；这使 Alembic、ORM metadata 和实际运行库之间没有单一真相源。
- 至少 routes、idempotency_records、notification_configs、ai_suggestions 未在现有迁移历史中得到完整表达；应用、Alembic 和测试的模型注册路径也不一致。
- 历史阶段 7 文档曾采用 `init_db()` → 初始化数据 → `alembic stamp head` 的绕行；`stamp` 只登记版本，不执行 DDL，不能作为迁移成功证明。

决策基线：[D-R2-DB](./decisions.md)、[D-R2-MIGRATION-BASELINE](./decisions.md)。

## 问题与目标

建立唯一、可复现、可审计的 schema 管理路径：Alembic 能从空库和受支持的旧 SQLite 数据库升级到与 ORM 一致的单一 head；应用启动不再以 `create_all()` 或手写运行时 DDL 代替正式迁移。

## 范围（P0 基础卡）

- 清点完整 ORM model registry，使 Alembic `target_metadata`、应用和测试引用同一模型集合。
- 修复迁移图及缺失 DDL，最终只保留一个 head；合并必须建立在 fresh upgrade 可工作的历史之上。
- 统一应用与 Alembic 的数据库 URL 解析和环境配置来源，避免迁移指向不同数据库。
- 定义并实现 fresh、Alembic-managed legacy、无 `alembic_version` 的混合旧 SQLite 三类升级路径。
- 把正常启动/部署的 schema 变更归入 Alembic，逐步移除运行时手写 `ALTER TABLE` / `CREATE INDEX`。
- 建立 schema parity、迁移幂等、备份/回滚、CI 门禁和运维 runbook。

## 非目标

- 不在本卡实现 CAS、幂等状态机、号段、Saga/outbox、RBAC 或错误处理业务功能。
- 不把 PostgreSQL/Redis 多 worker 验证混入 P0；PostgreSQL 复跑属于 R2-05。
- 不重写历史联调原文；只增加“已被 R2-00A 取代”的现状注记与回链。
- 本计划卡本身不代表 migration 已生成或数据库已升级。

## 依赖与进入条件

- R2-00 已完成，`My_doc/`、决策与实验模板具有可审计版本。
- 执行迁移前已识别测试数据库，legacy 样本有备份；禁止对未知开发/生产库直接试跑。

## 数据库分类与处置

| 类型 | 识别条件 | 期望动作 |
|---|---|---|
| fresh | 空数据库，无业务表、无 `alembic_version` | 从 base 执行到唯一 head，禁止先 `create_all()` |
| Alembic-managed legacy | 有合法 `alembic_version` 且 revision 在受支持图中 | 备份后按图升级，验证数据与约束 |
| 混合旧 SQLite | 有业务表但无 `alembic_version`，可能由 `create_all` + 手写 DDL 建成 | 先指纹识别和 parity 检查；只对已知签名执行受控 baseline/修复，禁止盲目 `stamp head` |
| unknown | 表/列/约束与任一支持签名不符 | fail closed，输出诊断与人工迁移入口 |

## 有序实施步骤

1. 导出 ORM 表、列、约束和索引清单；审计所有 revision、当前两个 head、手写 DDL 与测试 `create_all()` 使用点。
2. 建立共享模型 registry，在 Alembic `env.py` 加载完整 metadata；统一 settings 与 Alembic URL，确保日志不暴露凭据。
3. 设计修复迁移：先补齐 fresh 链缺失表/列/约束，再合并两个分支为单一 head。不得用空 merge 掩盖 `exception_events` 或其他缺表。
4. 将现有 `_run_phase1_migrations()` / `_run_phase4_migrations()` 中的 schema 变更映射为 Alembic revision；确定兼容窗口后停止正常启动调用这些运行时 DDL。
5. 明确 `create_all()` 边界：正常应用启动、部署和 smoke 不使用；如测试仍需要，仅限显式隔离 helper，并另有 migration-based 测试覆盖。
6. 为三类受支持数据库制作脱敏样本，执行备份 → upgrade → 数据/约束/parity 校验 → 再次 upgrade 幂等检查；未知 schema 验证 fail closed。
7. 增加 CI：`alembic heads` 唯一、fresh upgrade、legacy fixtures upgrade、`alembic check` 或等价 schema diff、应用启动 smoke。
8. 更新启动/迁移/备份恢复 runbook，并给历史 `stamp head` 绕行文档添加取代说明。

## 验收标准（P0）

- `alembic heads` 仅返回一个 head；revision 图无断链，fresh SQLite 可从 base 升到 head。
- ORM registry 与 Alembic `target_metadata` 覆盖所有正式表；schema parity 检查无未解释差异。
- 受支持的 Alembic legacy 和混合旧 SQLite 样本升级后数据、外键、唯一约束和索引符合预期；再次 upgrade 无额外 DDL/错误。
- 未知 schema 拒绝自动 stamp/升级，并给出不含敏感信息的诊断。
- 正常应用启动不再依赖 `Base.metadata.create_all()` 或手写 SQLite schema migration；测试辅助边界有明确注释和独立迁移测试。
- 应用与 Alembic 使用同一已核对的数据库 URL 来源；迁移日志不泄露口令。
- 备份、失败恢复、revision 回退适用边界与历史绕行取代说明已文档化。

## 验证命令

实现阶段根据隔离测试路径记录完整命令，至少包含：

```bash
cd src/backend
alembic heads
alembic history
alembic upgrade head
alembic check
python -m pytest -q tests -p no:cacheprovider
```

- `upgrade` / `downgrade` 只对本卡创建的临时 fresh/legacy fixture 执行，不对未识别数据库执行。
- 若当前 Alembic/SQLite 组合不支持 `alembic check`，使用可审计的 metadata/schema diff 替代，并记录原因。

## 文档与问题记录同步

同步 `src/backend/README.md`、启动说明、数据库环境配置、迁移 runbook、历史阶段 7 绕行注记、第二轮 README 和实验记录。

## 回滚与恢复

- 每个 legacy 实验先复制数据库并记录 SHA-256；原文件只读保留。
- revision 必须说明 downgrade 能力；SQLite 无法安全逆转的数据变更采用前向修复 + 备份恢复，不虚构可逆。
- 新迁移失败时恢复备份和旧应用版本，不用 `stamp head` 跳过失败 DDL。
- 切断运行时 DDL 前保留一个受控兼容窗口；确认 migration smoke 全绿后再删除旧路径。

## 完成记录

- 本地实现与 P0 协议验证已完成并按治理边界分批提交，计划保持 `in_progress`，直至 PR、远程 CI 与合并证据齐备。
- 唯一 head：`r2_00a_schema_convergence`；双父为 `c78f9b436833` 与 `phase7_exception_fields`。
- 已覆盖 fresh、全部受支持 revision、known mixed、WAL、未知/漂移、多 version rows、孤立 sidecar、失败目标清理与发布门禁。
- metadata parity 与临时数据库重启 smoke 已通过；完整后端结果为 718 passed、209 warnings。
- Commit SHA：`71237cd`（模型/URL 基座）、`9952095`（迁移收敛）、`adb3cac`（安全 SQLite 工作流）、`efe6d73`（发布门禁与 CI）；文档证据提交见本次后续提交。
- PR URL：尚无。
- CI run：未执行。
- Docker runtime validation：未执行（本机 Docker CLI unavailable，退出码 127）。
- PostgreSQL、Redis、多 worker 验证不在本卡 P0 本机协议范围内。
- 详细命令、环境、退出码与限制见 [R2-00A 实验记录](./experiments/20260826-R2-00A-migration-verification.md)。

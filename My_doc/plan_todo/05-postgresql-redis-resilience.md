---
plan_id: "R2-05"
title: PostgreSQL、Redis 与故障韧性验证
status: in_progress
priority: P1
owner: justtodo123
created: 2026-08-25
updated: 2026-08-31
depends_on: ["R2-00A", "R2-01", "R2-02", "R2-03"]
---

# R2-05 — PostgreSQL、Redis 与故障韧性验证

## 来源证据与当前行为

开发默认 SQLite；Redis 失败回退进程内缓存。Compose 当前是 SQLite + 单 worker，**不是**本卡目标拓扑。本机 2026-08-25：无 Docker / WSL / PostgreSQL / Redis。第一轮 02B 仍为 `mitigated`。

**当前动作**：按 [D-R2-ENV](./decisions.md) 走首选路径，给 GitHub Actions 增加 Postgres/Redis service，并补齐 PostgreSQL 驱动。本机仍无 Docker/WSL/PostgreSQL，因此故障注入、多 worker 复跑和备份恢复尚未执行；在这些证据出现前本卡不得标 `done`。

## 问题与目标

在**生产近似拓扑**上复跑 P0 协议，证明数据库并发、缓存降级、迁移、重启和连接资源行为。

## 范围（P1）

- PostgreSQL schema/Alembic、连接池、隔离级别、deadlock/serialization 有限重试。
- 复跑 R2-01～03：CAS、幂等、号段 10 万、Saga/outbox、worker 重启。
- Redis cache-aside、写后失效、单飞/锁、TTL 抖动、空值短 TTL、熔断与降级可见性。
- 多 worker；Compose 或 GHA service；健康检查；备份恢复。
- 给 backend 增加 PostgreSQL 驱动依赖；Compose 增加 postgres 服务（不再把 SQLite 当本卡栈）。

## 非目标

- 不分库分表、不上 Kafka、不装 Windows Docker Desktop。
- 不把 SQLite P0 结果外推为生产容量。
- 不把第一轮 02A smoke 或当前 SQLite compose 启动写成 P1 通过。

## 依赖与进入条件

- R2-00A 已完成单 head、fresh/legacy SQLite migration 基线；本卡只负责在 PostgreSQL 上复跑和验证，不再处理历史双 head。
- R2-01～03 协议已在本机 `done`（或至少代码已合入、P0 测试绿）。
- P1 环境三条之一可用；使用专用数据库/volume，不得清理开发库。

## 有序实施步骤

1. 选定并记录环境（GHA 首选）：Postgres 版本、Redis、worker、CPU/内存、连接池、数据规模。
2. 从 R2-00A 的唯一 head 在 PostgreSQL fresh 库执行升级，并从已登记旧 revision 升级；完成备份/恢复 dry-run。
3. 独立连接复跑并发状态、幂等、Saga/outbox、多 worker smoke。
4. 验证缓存失效、热点回源、Redis 中断与降级熔断。
5. 注入断连、锁冲突、worker 重启、短暂超时，记录边界（能测 RTO/RPO 则测，否则写适用边界）。
6. 将 PG/Redis 测试接入 CI（GHA services）；保存镜像/日志/实验记录。

## 验收标准（P1）

- PostgreSQL + Redis + 多 worker 的核心 HTTP smoke、迁移和重启通过；业务编码重启后可查。
- 并发冲突、死锁/序列化失败、连接池耗尽有稳定处理，无重复副作用。
- Redis 故障时降级可见、不承诺强一致；恢复后无无界回源。
- 备份恢复或迁移 dry-run 有原始日志。
- **Docker/GHA 未执行时本卡保持 `blocked`。**

## 验证命令

环境就绪后按实际拓扑记录。**当前仓库 `docker compose up` 仍是 SQLite，不能当本卡命令。** 示例（GHA 或 Linux）：

```bash
# GHA P1 job uses postgres:16-alpine + redis:7-alpine services
cd src/backend
python scripts/release_migrate.py
python -m pytest -q -p no:cacheprovider tests/p1 tests/unit/core/test_database_url.py

# Linux / VM only; current Windows host has no Docker
docker compose -f docker-compose.p1.yml -p logistics-r2 up -d --build
```

记录 `docker version` 或 GHA run URL、compose ps、镜像 ID、退出码。

## 文档与问题记录同步

更新环境配置、启动说明、迁移 runbook、缓存一致性边界、第一轮 02 状态链接和第二轮 README。

## 回滚与恢复

实验使用专用 project/volume；清理前确认名称。迁移先备份。

## 完成记录

- 状态：`in_progress`（2026-08-31）。不得标 `done`。
- 第一刀：`psycopg[binary]`、`docker-compose.p1.yml`、CI job `P1 PostgreSQL + Redis 基线`、Postgres 迁移到唯一 head + Redis ping。
- 本机：未执行 Docker / PostgreSQL / Redis；P1 测试在无 `P1_DATABASE_URL` 时 skip。
- 未做：CAS/幂等/号段/Saga 在 PostgreSQL 复跑、多 worker 故障注入、备份恢复、跨 worker 登录限流。
- 实现提交：`03a3436`。PR：[PR #18](https://github.com/justtodo123/LogisticSystem_more/pull/18)，尚未合并。CI：进行中；未通过、未合并不得标 done。

---
plan_id: "R2-05"
title: PostgreSQL、Redis 与故障韧性验证
status: pending
priority: P1
owner: 待认领
created: 2026-08-25
updated: 2026-08-25
depends_on: ["R2-01", "R2-02", "R2-03"]
---

# R2-05 — PostgreSQL、Redis 与故障韧性验证

## 来源证据与当前行为

开发默认 SQLite，Redis 失败时回退进程内缓存，第一轮 Docker 计划区分了本地 smoke 与真实 Docker E2E。参考路线图要求 PostgreSQL + Redis + 多 worker 作为生产验收基线，并关注连接池、事务隔离、锁等待、缓存击穿和降级一致性。

## 问题与目标

建立可重复的生产近似拓扑和集成测试，证明数据库并发、缓存降级、迁移、重启和连接资源行为，而不是仅证明配置文件能启动。

## 范围

- PostgreSQL schema/migration、连接池、隔离级别、deadlock/serialization failure 有限重试。
- Redis cache-aside、写后失效、singleflight/锁、TTL 抖动、空值短 TTL、熔断窗口和指标。
- Uvicorn 多 worker、Compose/Testcontainers、健康检查、备份恢复和 Docker 业务 smoke。

## 非目标

- 不在没有瓶颈数据时引入分库分表、微服务或 Kafka。
- 不把 SQLite 结果外推为生产容量；不把内存缓存当强一致存储。

## 依赖与进入条件

- R2-01～03 的并发、幂等和恢复协议已可在目标库运行。
- 准备独立测试库/Redis 和专用 volume；不得清理开发库。

## 有序实施步骤

1. 固定 PostgreSQL、Redis、worker、CPU/内存、连接池和数据规模，建立 Compose 或 Testcontainers 环境。
2. 执行 Alembic 从旧版本升级、双 head 处理、回滚/备份恢复和索引/EXPLAIN 检查。
3. 在独立连接下复跑并发状态、幂等、Saga/outbox 和多 worker smoke。
4. 改造/验证缓存失效顺序、热点并发回源、Redis 中断恢复和降级熔断。
5. 注入数据库断连、锁冲突、Redis 故障、worker 重启和网络短暂超时，记录 RTO/RPO 或适用边界。
6. 将目标环境接入 CI 的可选/必选门禁，并保存镜像、迁移和 smoke 产物。

## 验收标准

- PostgreSQL + Redis + 多 worker 的核心 HTTP smoke、迁移和重启通过；业务编码重启后可查。
- 并发冲突、死锁/序列化失败和连接池耗尽有稳定处理，不产生重复副作用。
- Redis 故障时降级可见、缓存不承诺强一致，恢复后不会无界回源或击穿。
- 备份恢复和迁移 dry-run 有原始日志；Docker 未执行时保持 `blocked`。

## 验证命令

```bash
docker compose config
docker compose -p logistics-r2 up -d --build
cd src/backend
python scripts/smoke_local.py --base-url http://127.0.0.1:8000
python -m pytest -q -p no:cacheprovider
```

若本机无 Docker，必须在 Linux VM/授权测试主机执行并记录 `docker version`、compose ps、镜像 ID 和退出码；本地 SQLite 测试只能作为补充。

## 文档与问题记录同步

更新环境配置、启动说明、迁移 runbook、缓存一致性边界、第一轮 02 的状态链接和第二轮 README。

## 回滚与恢复

所有实验使用专用 project/volume；清理前确认名称。迁移先备份，故障按恢复 runbook 操作，不删除未知环境数据。

## 完成记录

- 尚未开始。完成时填写拓扑、版本、数据量、故障矩阵、恢复结果、Commit/PR 和外部环境限制。

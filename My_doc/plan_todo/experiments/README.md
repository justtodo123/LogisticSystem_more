# 第二轮实验目录

本目录保存可审计的实验**报告、模板和小型脱敏摘要**。配置或脚本存在不等于实验已经执行，更不等于验收通过。

- 模板：[_template.md](./_template.md)
- P0：本机 SQLite 协议/并发/故障注入；报告必须说明 SQLite 写锁、单 worker、无 Redis 等限制。
- P1：GitHub Actions 或 Linux VM/云主机上的 PostgreSQL + Redis + 多 worker；未执行时保持 `blocked` 或“未执行”。
- P2 镜像发布扫描：已在 CD [run 33826520856](https://github.com/justtodo123/LogisticSystem_more/actions/runs/33826520856) 通过，零 exception。小摘要见 [r2-06-image-scan](./r2-06-image-scan/)，报告见 [20260904-R2-06-image-scan.md](./20260904-R2-06-image-scan.md)。原始 Trivy/SBOM 只留 14 天 CI artifact，不入库。R2 冻结记录见 [../20260904-R2-closeout.md](../20260904-R2-closeout.md)。

## Git 追踪边界

可追踪：

- Markdown 实验报告、复现命令、脱敏后的小型 JSON/CSV 摘要；
- 数据规模、退出码、统计摘要、SHA-256、CI run/artifact URL 与保留期限；
- 不包含凭据、cookie、JWT、个人数据、完整请求体或数据库副本的必要诊断片段。

不追踪：

- `raw/`、`artifacts/`、`tmp/` 下的原始日志、数据库快照、压测明细和临时文件；
- `.env`、密钥、令牌、连接串中的口令、私钥、未脱敏业务数据；
- 可从命令重新生成的大型产物。

大型原始产物放在 GitHub Actions artifact 或受控外部存储。报告必须登记位置、大小、SHA-256、脱敏检查和保留/删除日期；外部产物不可访问时，不得把结论写成可复现。

## 记录规则

1. 文件名用 `YYYYMMDD-<plan-id>-<slug>.md`。
2. 明确区分 `通过`、`失败`、`blocked`、`未执行`；命令缺失或退出码未知不能写“通过”。
3. 绑定分支、commit SHA、PR、计划/决策版本与 Alembic revision；尚不存在的字段写“尚无”，禁止预填。
4. 标明数据库是 fresh、受 Alembic 管理的 legacy，还是无 `alembic_version` 的混合旧库。
5. 失败也必须保留证据；若原始内容不可提交，保留脱敏摘要、hash 和外部位置。
6. SQLite 结果只证明 P0 协议辅助验证，不外推 PostgreSQL 多 worker 容量或锁行为。

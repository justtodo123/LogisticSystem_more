# R2 之后的后续任务（不阻断 R2）

> 这些任务在 R2 **工程交付完成 / Closeout ready** 之后单独登记。
> R2 基线见 [20260904-R2-closeout.md](./20260904-R2-closeout.md)。
> 不要把本文件中的项重新定义为 R2 阻断条件。

## P3-PROD 生产部署验证

环境：云主机或受控 Linux Docker。本机未装 Docker 不构成 R2 缺陷。

验收镜像必须使用同一 SHA 批次，不要只拉 `latest`：

- `ghcr.io/justtodo123/logisticsystem_more-backend:f9e08a499ba50987505e32d58b545a37c9543ef4`
- `ghcr.io/justtodo123/logisticsystem_more-frontend:f9e08a499ba50987505e32d58b545a37c9543ef4`

待办：

- 拉取上述 SHA tag
- Compose 启动
- release migration
- backend health check
- frontend `/api` 反向代理
- Redis / PostgreSQL 连通性
- 第一轮 02B 业务 E2E（当前仍为 `mitigated`）
- 回滚和备份恢复演练

`latest` 只作便利标签，不作审计或回滚依据。

## P3-P2 可选增强

- Grafana + Prometheus + OpenTelemetry 全家桶
- 跨 worker 指标聚合
- 定时镜像扫描（发布门禁 ≠ cron）
- 更长 soak / 泄漏结论（当前 2h 只登记绝对值）
- 完整写+读业务全路径容量验证

不要把 soak P95 与 5 分钟读混合/写路径 P95 做直接性能结论比较。

## 明确不做（相对本收口）

- 不为 CVE-2026-13346（pip MEDIUM, report-only）登记 exception
- 不为清零该报告项改应用依赖或扫描策略
- 不把 02B Docker E2E 改写成 R2 阻断项

# 智能物流调度平台

> LogisticSystem — FastAPI + Vue 3 全栈物流调度与路径优化平台  
> R2-00～R2-06 工程交付已完成；阶段测试、容量和 CI/CD 数字按日期与场景记录在[证据台账](My_doc/delivery/02-claim-evidence-ledger.md)，不把历史测试/API 统计写成当前固定总数。

## 快速开始

```bash
# Docker 一键启动（无需安装 Python/Node）
docker compose up -d  # release_migrate 门禁成功后才启动 backend
docker exec -it logistics-backend python scripts/init_demo_data.py
# 访问 http://localhost:8080 · 登录 admin / 123456
```

> Docker 验证级别（2026-08-26）：Compose 已配置一次性 `migrate` 服务作为 backend 启动闸门；本机未执行 Docker 业务 E2E，不能把配置检查写成容器验收，见 [plan 02](My_doc/post_plan/第一轮优化计划/02-docker-seed-e2e.md)。旧 SQLite 不应直接挂载试迁移，先按[后端迁移说明](src/backend/README.md#数据库迁移边界)分类并复制处理。

```bash
# 本地开发
cd src/backend && pip install -r requirements.txt && python -m alembic -c alembic.ini upgrade head && python scripts/init_demo_data.py && uvicorn main:app --reload --port 8000
cd src/frontend && npm install && npm run dev    # http://localhost:5173
```

```bash
# 仅前端 Mock 演示（无需后端）
cd src/frontend && cp .env.example .env.local && npm install && npm run dev
```

## 文档导航

| 文档 | 说明 |
|------|------|
| [01-技术路线](docs/01-技术路线.md) | 技术选型、分层架构、数据流、降级策略 |
| [02-项目结构](docs/02-项目结构.md) | 仓库目录树、模块职责、"找代码指南" |
| [03-项目功能](docs/03-项目功能.md) | 功能模块总览 + 按运行时 OpenAPI 核对的 API 清单 |
| [04-实现方式](docs/04-实现方式.md) | 核心机制：状态机 / 调度管线 / AI 闭环 / 缓存降级 |
| [05-部署说明](docs/05-部署说明.md) | Docker Compose / CI/CD / 生产环境变量 |
| [06-启动说明](docs/06-启动说明.md) | 3 种启动方式 + 演示账号 + 常见问题 |
| [07-规范说明](docs/07-规范说明.md) | API 格式 / 错误码 / 鉴权 / 前后端规范 |
| [08-优化点说明](docs/08-优化点说明.md) | 第一轮 T0-T6 历史摘要、当前 R2 映射与遗留边界 |

> 历史文档（MVP/P1 阶段计划、PRD、架构说明书等）已归档至 [docs/history/](docs/history/README.md)。
> 当前工程交付与面试展示入口：[My_doc/delivery/README.md](My_doc/delivery/README.md)。R2 已冻结；该目录只整理当前事实、证据和演示，不重新开启应用开发。

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 | RESTful API，Alembic 迁移 |
| 前端 | Vue 3 + TypeScript + Element Plus + Vite | SPA，Mock 开关独立开发 |
| 数据库 | SQLite（开发）/ PostgreSQL 16（P1 验证） | 通过 DATABASE_URL 切换；生产部署另行验收 |
| 缓存 | Redis + 自动内存降级 | 普通缓存与登录限流可降级；分布式幂等以数据库为真相源 |
| AI | DeepSeek API → Pydantic 校验层 → 确认闸门 | 3 次重试 + 降级兜底 |
| 地图 | 高德 API → 直线×系数 → Haversine | 三档降级，无 Key 自动 Canvas 折线 |
| 部署 | Docker Compose + GitHub Actions CI/CD | 本地 Compose 配置与 P1 验证拓扑分离；生产部署尚未验收 |

## 核心功能

- **订单管理** — CRUD + Excel/CSV 导入 + 筛选搜索
- **调度引擎** — 可插拔策略模式（贪心/Dummy），多目标评分（Top-K 候选 + 可解释性）
- **人工干预** — 换车/换司机/重算/撤销，带版本链
- **模拟送达** — 6 状态机流转（unassigned → in_transit → signed）
- **异常重规划** — 3 策略（partial/full/hybrid）+ 差异报告
- **AI 助手** — 自然语言调度 + 方案解释 + 确认闸门（建议→人工确认→生效）
- **报表分析** — SLA / 成本 / 异常 / 运力 4 类报表 + Dashboard 可视化
- **通知服务** — 可插拔渠道（Console/Email/企业微信）
- **ERP 对接** — CSV(xlsx) 导出 + Excel 导入列映射 + Webhook
- **RBAC + 审计** — `admin` / `dispatcher` / `viewer` / `warehouse_operator` + 兼容 `manager`，后端权限依赖 + token_version 撤权 + 操作审计日志
- **可观测性** — request/trace/task ID、JSON 日志、`/metrics`；load/spike 走 GHA

## 仓库结构

```text
LogisticSystem/
├── docs/               # 项目文档（01-08 核心 + 4 规范 + history/ 归档）
├── src/
│   ├── backend/        # FastAPI 后端（api/services/algorithms/models/schemas/…）
│   └── frontend/       # Vue 3 前端（views/components/composables/api/…）
├── scripts/            # 启动脚本
├── docker-compose.yml
├── Dockerfile.backend / Dockerfile.frontend
└── orderdata.xlsx      # 演示用订单导入模板
```

---

查看 [docs/README.md](docs/README.md) 获取完整文档导航与阅读顺序建议。

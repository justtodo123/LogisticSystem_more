# 智能物流平台 — 后端

> FastAPI 后端服务 · 83 个 API 端点 · 626 测试全绿

## 快速启动

```bash
cd src/backend
pip install -r requirements.txt
cp .env.example .env.dev          # 编辑 .env.dev，至少修改 JWT_SECRET
python scripts/init_users.py      # 创建演示用户
python scripts/init_demo_data.py  # 初始化示例数据
uvicorn main:app --reload --port 8000
```

访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看 Swagger API 文档。

## 目录结构

| 目录 | 职责 |
|------|------|
| `api/` | REST 路由层（24 个 Router 模块） |
| `services/` | 业务逻辑层（调度/模拟/异常/AI/通知） |
| `algorithms/` | 调度算法（策略模式：base → greedy/dummy/deepseek） |
| `models/` | SQLAlchemy ORM 模型 |
| `schemas/` | Pydantic v2 请求/响应 Schema |
| `core/` | 统一响应/错误码/权限/RBAC/幂等 |
| `middleware/` | 审计日志中间件 |
| `config/` | 环境配置（pydantic-settings）+ algorithm_config.json |
| `scripts/` | 运维脚本（init_users/init_demo_data） |
| `tests/` | 单元/集成/API 测试（626 用例） |
| `alembic/` | 数据库迁移 |

## 运行测试

```bash
python -m pytest -q     # 全部 626 测试
python -m pytest tests/unit/ -q    # 仅单元测试
python -m pytest tests/api/ -q     # 仅 API 测试
```

## 文档

所有项目文档集中在仓库根目录 [docs/](../../docs/) 下：

| 文档 | 说明 |
|------|------|
| [01-技术路线](../../docs/01-技术路线.md) | 技术选型与架构 |
| [02-项目结构](../../docs/02-项目结构.md) | 目录与模块职责 |
| [03-项目功能](../../docs/03-项目功能.md) | 功能模块 + 完整 API 端点表 |
| [04-实现方式](../../docs/04-实现方式.md) | 核心机制（状态机/调度/AI/缓存） |
| [06-启动说明](../../docs/06-启动说明.md) | 本地/Docker/Mock 启动 |
| [07-规范说明](../../docs/07-规范说明.md) | 开发/API/Git 规范 |
| [08-优化点说明](../../docs/08-优化点说明.md) | T0-T6 优化 + 遗留边界 |

## 环境变量

关键变量见 `.env.example`，完整定义见 [环境配置说明](../../docs/环境配置说明.md)。

| 变量 | 说明 |
|------|------|
| `JWT_SECRET` | JWT 签名密钥（**必须修改**） |
| `DEEPSEEK_API_KEY` | AI 功能密钥（空时自动降级） |
| `MAP_API_KEY` | 高德地图密钥（空时降级 Canvas 折线） |
| `REDIS_ENABLED` | Redis 缓存开关（关闭时自动内存降级） |
| `DATABASE_URL` | 数据库连接（默认 SQLite） |

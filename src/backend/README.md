# 智能物流平台 — 后端

> FastAPI 后端服务 · 运行时 OpenAPI 清单见项目功能文档 · Alembic 管理正式 schema

## 快速启动

```bash
cd src/backend
pip install -r requirements.txt
cp .env.example .env.dev          # 编辑 .env.dev，至少修改 JWT_SECRET
python -m alembic -c alembic.ini upgrade head  # 显式迁移 schema
python scripts/init_demo_data.py  # 初始化完整 Demo；会清理并重建演示数据
# 或：python scripts/init_users.py # 仅创建/补齐演示用户，不要与上一步重复执行
uvicorn main:app --reload --port 8000
```

> `init_demo_data.py` 仅用于 disposable 的本地/演示数据库；它会清理并重建 Demo 数据，禁止对生产库或需要保留数据的开发库执行。

访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看 Swagger API 文档。

## 数据库迁移边界

- Alembic 是正式 schema 的唯一迁移入口；应用启动和 Uvicorn worker 不执行 DDL。
- 本地 fresh 开发库可运行 `python -m alembic -c alembic.ini upgrade head`；发布/Compose 使用 `python scripts/release_migrate.py`，只创建 fresh SQLite 或验证已处于当前 head 且无 drift 的现有库。
- `config.database.init_db()` 仅供隔离测试按 ORM metadata 建表，禁止用于部署或旧库升级。
- 旧 SQLite 必须先备份；合法 `alembic_version` 由 Alembic 升级，未知 revision、多版本行或未知结构均停止处理，禁止用 `stamp head` 掩盖差异。
- 无版本旧库只能在 schema 与当前 ORM 完全一致时复制采用；原文件保持不变，副本 parity 通过后才能 stamp。

旧 SQLite 操作必须在 `src/backend` 目录执行，并指定与源文件不同、尚不存在的目标副本：

```bash
python scripts/migrate_sqlite.py classify <source>
python scripts/migrate_sqlite.py upgrade-copy <source> <target>  # 仅 Alembic managed 旧库
python scripts/migrate_sqlite.py adopt-copy <source> <target>    # 仅与当前 ORM 完全一致的无版本库
```

命令会先分类；未知 revision、异常版本行、结构漂移或含未映射遗留数据时 fail closed，不修改源文件，也不会创建可误用的目标副本。

## 目录结构

| 目录 | 职责 |
|------|------|
| `api/` | REST 路由层；运行时清单见 `docs/03-项目功能.md` |
| `services/` | 业务逻辑层；同步与异步函数按调用链契约并存 |
| `algorithms/` | 调度算法；当前注册 greedy/dummy，DeepSeek 不作为调度 engine，2-opt 仍为 stub |
| `models/` | SQLAlchemy ORM 模型；`base.py` 提供共享 metadata，`registry.py` 显式注册正式模型 |
| `schemas/` | Pydantic v2 请求/响应 Schema |
| `core/` | 统一响应/错误码/权限/RBAC 等公共基座 |
| `middleware/` | 审计、持久化幂等、请求超时等中间件 |
| `config/` | 环境配置、共用数据库 URL 解析及 engine/session |
| `utils/` | 通用工具；`schema_management.py` 负责 SQLite 分类、复制迁移与 parity |
| `scripts/` | 初始化脚本、`migrate_sqlite.py` 旧库安全操作 CLI 与 `release_migrate.py` 发布门禁 |
| `tests/` | 单元/集成/API/迁移测试 |
| `alembic/` | 正式 schema 唯一迁移入口及 revision graph |

## 运行测试

```bash
python -m pytest -q     # 全部后端测试
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
| `REDIS_ENABLED` | Redis 普通缓存/共享登录限流开关；关闭或故障时可降级，数据库幂等不依赖 Redis |
| `DATABASE_URL` | 数据库连接（默认 SQLite） |

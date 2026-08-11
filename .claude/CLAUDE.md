# CLAUDE 项目理解说明

本文件用于 Claude 助手快速理解 `LogisticSystem` 仓库的核心结构、技术栈、开发规范和启动流程。
请根据仓库内现有文档与代码实现，优先遵循 `docs/` 下的规范，不做与当前项目风格冲突的改动。

## 项目概览

- 名称：智能物流调度平台（LogisticSystem）
- 技术栈：后端 FastAPI + SQLAlchemy 2.0 + Pydantic v2；前端 Vue 3 + TypeScript + Element Plus + Vite
- 数据库：开发默认 SQLite，生产可切换 PostgreSQL
- 缓存：Redis 可选，关闭时自动降级为进程内存缓存
- AI：DeepSeek API 作为自然语言解析与解释层，空 key 或超时时自动降级
- 目标：订单管理、调度引擎、异常重规划、AI 助手、报表分析、ERP 对接、审计与权限

## 关键目录

- `docs/`：项目文档主入口，包含技术路线、项目结构、功能清单、启动说明、规范说明、优化说明等。
- `src/backend/`：FastAPI 后端服务根目录。
- `src/frontend/`：Vue 3 前端源码根目录。
- `scripts/`：初始化数据与用户的辅助脚本。
- `docker-compose.yml`、`Dockerfile.backend`、`Dockerfile.frontend`：容器化启动与部署配置。

## 后端重点

- 入口：`src/backend/main.py`
- 路由层：`src/backend/api/`
- 业务层：`src/backend/services/`
- 算法层：`src/backend/algorithms/`
- ORM 模型：`src/backend/models/`
- Pydantic Schema：`src/backend/schemas/`
- 公共基座：`src/backend/core/`、`src/backend/middleware/`、`src/backend/config/`、`src/backend/utils/`
- 数据迁移：`src/backend/alembic/`
- 测试：`src/backend/tests/`，共 626 个测试用例。

### 后端规范

- API 响应统一为 `code/message/data/meta`，成功时 `code=0`。
- 降级场景仍返回 `code=0`，通过 `meta.degraded` / `meta.degraded_reason` 提示。
- HTTP 异常由 FastAPI 处理，返回 `detail`。
- 错误码定义在 `src/backend/core/error_codes.py`，禁止硬编码数字。
- 鉴权通过 `core/permissions.py` 和依赖注入完成，角色有 `admin`、`dispatcher`、`operator`、`viewer` 等。
- 数据库约定：自增 `id`、业务编码 `xxx_code`、`created_at` / `updated_at`、物理删除、级联删除。

## 前端重点

- 入口：`src/frontend/src/main.ts`
- 页面：`src/frontend/src/views/`
- 组件：`src/frontend/src/components/`
- 组合式逻辑：`src/frontend/src/composables/`
- API 封装：`src/frontend/src/api/`
- 状态管理：`src/frontend/src/stores/`
- 类型定义：`src/frontend/src/types/`
- 工具：`src/frontend/src/utils/`

### 前端约定

- 组件名：PascalCase
- 文件名：kebab-case
- Composable：`use*`
- API 文件按领域拆分，例如 `api/orders.ts`、`api/schedule.ts`
- 前端 Mock 开关由 `src/frontend/.env.local` 控制，默认 `VITE_USE_MOCK_* = true`

## 启动与开发

### 本地开发

后端：
- `cd src/backend`
- `pip install -r requirements.txt`
- `cp .env.example .env.dev`
- `python scripts/init_users.py`
- `python scripts/init_demo_data.py`
- `uvicorn main:app --reload --port 8000`

前端：
- `cd src/frontend`
- `cp .env.example .env.local`
- `npm install`
- `npm run dev`

### Docker 一键启动

- 根目录下运行 `docker compose up -d`
- 进入容器后运行 `docker exec -it logistics-backend python scripts/init_demo_data.py`

### 仅前端 Mock 演示

- `cd src/frontend`
- `cp .env.example .env.local`
- 确保 `VITE_USE_MOCK_* = true`
- `npm install`
- `npm run dev`

## 测试与校验

- 后端测试：`cd src/backend && python -m pytest -q`
- 前端类型检查：`cd src/frontend && npx vue-tsc --noEmit`
- 前端构建：`cd src/frontend && npm run build`

## 参考文档

- `docs/01-技术路线.md`
- `docs/02-项目结构.md`
- `docs/03-项目功能.md`
- `docs/04-实现方式.md`
- `docs/06-启动说明.md`
- `docs/07-规范说明.md`
- `docs/环境配置说明.md`

## 任务建议

- 任何修改前优先查看 `docs/07-规范说明.md` 和 `src/backend/README.md`。
- 后端变更应尽量在现有 `services/` + `algorithms/` + `api/` 模式下扩展。
- 前端改动应保持组件、composable、类型和 API 封装一致。
- 若涉及新环境变量，先补充 `src/backend/config/settings.py`、`.env.example`、`src/frontend/.env.example` 以及对应文档。
- 每个阶段完成后按 `docs/Git协作规范.md` 的提交规范提交 git，保留阶段性变更记录，避免把多个阶段合并为单次提交。

## Git 提交流程

- 使用 Conventional Commits 格式，例如：`docs: 补充 Claude 项目理解说明`
- 每完成一个小功能、一个文档更新或一个阶段后提交一次，不要等到整个阶段结束再提交。
- 新增依赖、环境变量或配置变更时，同步更新对应模板/文档并与代码一起 commit。
- 提交前检查 `git status`，确认不要含 `.env`、`node_modules/`、`*.db` 等禁止提交内容。

## 注意事项

- 不要随意改变项目主架构或技术栈。
- 不要将后端业务逻辑写入前端，也不要在后端直接操纵 Vue/前端文件。
- 与项目当前风格不一致的改动应当征求确认。
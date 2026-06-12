# 智能物流平台 - 后端

基于 **Python 3.11 + FastAPI 0.110+** 的单体后端服务，承载 API 接口、调度算法和 DeepSeek AI 代理。

## 项目状态

**当前阶段**：阶段 1（认证与权限）已完成  
**下一阶段**：阶段 2（基础数据管理）

## 技术栈

| 层 | 技术 | 用途 |
|---|------|------|
| Web 框架 | FastAPI 0.110+ | REST API 服务 |
| ASGI 服务器 | Uvicorn 0.27+ | 开发/生产服务器 |
| ORM | SQLAlchemy 2.0+ | 数据库操作 |
| 迁移 | Alembic 1.13+ | 数据库版本管理 |
| 数据校验 | Pydantic v2 | 请求/响应模型 |
| 数据库 | SQLite（开发）/ MySQL 8.0（可选） | 持久化存储 |
| 认证 | PyJWT 2.8+ + passlib[bcrypt] | JWT Token + 密码哈希 |
| 算法 | NumPy + 自研 Haversine + 自研 2-opt | 路径规划与调度 |
| AI 编排 | DeepSeek API（OpenAI 兼容） | 自然语言调度 |
| HTTP 客户端 | httpx 0.27+ | 外部 API 调用 |
| 数据处理 | openpyxl + pandas | Excel 导入 |

## 快速开始

### 环境要求

- Python 3.11+
- Windows / macOS / Linux

### 安装与启动

```bash
cd src/backend

# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
copy .env.example .env
# 编辑 .env，填写 JWT_SECRET 等必要配置

# 5. 执行数据库迁移
alembic upgrade head

# 6. 初始化种子数据（创建演示账号）
python scripts/init_users.py

# 7. 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：
- **API 文档 (Swagger)**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/api/health

### 演示账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 调度员 | `dispatcher` | `123456` | 读写全部接口 |
| 物流管理者 | `manager` | `123456` | 仅读（POST/PUT/DELETE 返回 403） |

## 项目结构

```
src/backend/
├── main.py                     # FastAPI 应用入口，注册路由、CORS、全局异常处理器
├── requirements.txt            # Python 依赖清单
├── alembic.ini                 # Alembic 迁移配置
├── .env / .env.example         # 环境变量
│
├── api/                        # 路由层
│   ├── __init__.py
│   ├── auth.py                 # 认证端点 (POST /login, GET /me, POST /logout)
│   └── dependencies.py         # 依赖注入 (get_current_user JWT 验证, require_dispatcher RBAC)
│
├── services/                   # 业务逻辑层
│   ├── __init__.py
│   └── auth_service.py         # 认证服务 (Token 生成, 密码验证, 用户查询)
│
├── models/                     # SQLAlchemy ORM 模型
│   ├── __init__.py
│   ├── base.py                 # Base 声明基类
│   ├── user.py                 # User 模型 (id, username, password_hash, role, display_name, is_active)
│   └── log_event.py            # LogEvent 模型 (登录/登出操作日志)
│
├── schemas/                    # Pydantic 请求/响应模型
│   ├── __init__.py
│   ├── user.py                 # UserLoginRequest, UserLoginResponse, UserResponse
│   └── log_event.py            # LogEvent Schema
│
├── config/                     # 配置
│   ├── __init__.py
│   ├── database.py             # SQLAlchemy engine + Session + pydantic-settings (JWT/Database)
│   └── algorithm_config.json   # 算法权重配置 (F005/F006/F007)
│
├── utils/                      # 工具层
│   └── response.py             # success_response / error_response 统一响应构建函数
│
├── scripts/                    # 工具脚本
│   ├── __init__.py
│   ├── init_users.py           # 种子账号初始化 (dispatcher / manager)
│   └── init_log_events.py      # 日志表清空
│
├── algorithms/                 # 算法引擎 (F005/F006/F007/F021, 阶段 3+ 实现)
│   └── __init__.py
│
├── data/                       # 数据文件
│   └── logistics.db            # SQLite 数据库
│
└── alembic/                    # 数据库迁移
    ├── env.py
    ├── script.py.mako
    └── versions/               # 迁移版本文件
```

## API 接口

### 已实现（阶段 1）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/auth/login` | 用户登录，返回 JWT Token | 否 |
| `GET` | `/api/auth/me` | 获取当前用户信息 | Bearer Token |
| `POST` | `/api/auth/logout` | 登出 | Bearer Token |
| `GET` | `/api/health` | 健康检查 | 否 |

### 规划中（阶段 2-8）

详见 `docs/` 目录下的 MVP 开发计划。核心接口包括：

- **基础数据**：`/api/orders`、`/api/nodes`、`/api/vehicles`、`/api/drivers` 等
- **调度**：`POST /api/schedule/global`、`POST /api/schedule/node-dispatch`
- **路线**：`GET /api/routes`、`GET /api/routes/by-vehicle/{code}/coordinates`
- **异常**：`GET/POST /api/exceptions`、`POST /api/exceptions/{code}/replan`
- **模拟**：`POST /api/simulation/deliver`
- **AI**：`POST /api/ai/parse`

## 统一响应格式

所有接口遵循以下格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

| code | HTTP 状态码 | 说明 |
|------|-------------|------|
| `0` | 200 | 成功 |
| `40000` | 400 | 参数校验失败 |
| `40100` | 200 | 用户名或密码错误（登录接口） |
| `40100` | 401 | 未登录或 Token 无效 |
| `40101` | 401 | Token 已过期，请重新登录 |
| `40300` | 403 | 无权限执行此操作 |
| `40400` | 404 | 资源不存在 |
| `50000` | 500 | 服务器内部错误 |

> **注意**：所有 HTTP 异常（401/403/404/422/500）均由 `main.py` 中 `StarletteHTTPException` 全局异常处理器统一转为 `{code, message, data, meta}` 格式，前端可统一通过 `code` 字段判断，无需关注 HTTP 状态码差异。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥（必填） | — |
| `JWT_EXPIRE_SECONDS` | Token 过期秒数 | `86400`（24h） |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./data/logistics.db` |
| `CORS_ORIGINS` | 跨域白名单 | `http://localhost:5173` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | —（阶段 8） |
| `DEMO_MODE_DEFAULT` | 演示模式 | `false` |

## 数据库

- **开发**：SQLite，零配置，数据库文件位于 `data/logistics.db`
- **迁移**：使用 Alembic 管理表结构变更

```bash
# 执行迁移到最新版本
alembic upgrade head

# 生成新的迁移脚本
alembic revision --autogenerate -m "描述"

# 回滚一个版本
alembic downgrade -1
```

## 开发规范

- **分支**：后端使用 `backend/phase-N` 分支，禁止直接在 `main` 上开发
- **Commit**：`feat(backend): 阶段N 功能描述`
- **依赖**：新增 Python 包必须同步更新 `requirements.txt`
- **密钥**：`.env` 不提交 Git，API Key 仅存后端
- **API 契约先行**：每阶段开始前先定接口契约
- **统一响应**：所有接口必须遵循 `{code, message, data, meta}` 格式

## 架构约束

1. **单体优先**：一个 FastAPI 进程承载全部功能，不拆分微服务
2. **双标识策略**：数据库内用自增 `id`，API 层暴露 `*_code` 业务编号
3. **离线可演示**：路径规划不依赖任何地图 API
4. **确定性算法**：调度结果同输入可复现，不使用随机种子
5. **DeepSeek 不伪造**：API 调用失败时降级处理，不伪造 AI 结果
6. **调度时限**：单次调度 ≤ 10 秒返回
7. **全局异常处理**：所有 HTTPException 由 `StarletteHTTPException` 全局处理器统一转为 `{code, message, data, meta}` 格式，前端无需判断 HTTP 状态码差异

## 自测

阶段 1 自测脚本（`test_api.py`，不提交 Git）覆盖以下场景：

| # | 测试项 | HTTP | code | 结果 |
|---|--------|------|------|------|
| 1 | `GET /api/health` | 200 | 0 | ✅ |
| 2 | `POST /api/auth/login` (dispatcher 正常) | 200 | 0 | ✅ |
| 3 | `POST /api/auth/login` (密码错误) | 200 | 40100 | ✅ |
| 4 | `POST /api/auth/login` (用户不存在) | 200 | 40100 | ✅ |
| 5 | `POST /api/auth/login` (manager 正常) | 200 | 0 | ✅ |
| 6 | `GET /api/auth/me` (有效 Token) | 200 | 0 | ✅ |
| 7 | `GET /api/auth/me` (无效 Token) | 401 | 40100 | ✅ |
| 8 | `GET /api/auth/me` (无 Token) | 401 | 40100 | ✅ |
| 9 | `POST /api/auth/logout` (有效 Token) | 200 | 0 | ✅ |
| 10 | `POST /api/auth/logout` (无效 Token) | 401 | 40100 | ✅ |
| 11 | `POST /api/auth/logout` (无 Token) | 401 | 40100 | ✅ |

> manager 403 权限测试及 Token 过期（40101）测试留待阶段 2+ 有受保护路由后验证。

## 相关文档

- [项目宪章](../../.codebuddy/CODEBUDDY.md)
- [系统架构设计说明书](../../docs/architecture/系统架构设计说明书.md)
- [MVP 开发计划 - 后端](../../docs/MVP开发计划-后端.md)
- [阶段 1 开发文档](../../My_doc/阶段1-认证与权限-开发文档.md)
- [阶段 1 API 契约文档](../../My_doc/阶段1-认证与权限-API契约文档.md)

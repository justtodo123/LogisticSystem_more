# 智能物流平台 - 后端

基于 **Python 3.11 + FastAPI 0.110+** 的单体后端服务，承载 API 接口、调度算法和 DeepSeek AI 代理。

## 项目状态

**当前阶段**：阶段 2（基础数据管理）已完成  
**下一阶段**：阶段 3（全局调度 F007 + 打包 F021）

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

# 5. 创建数据库表（阶段 2 暂未使用 Alembic 迁移，直接建表）
python -c "from config.database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"

# 6. 初始化演示数据（创建用户、节点、车辆、司机、订单等）
python scripts/init_demo_data.py

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
│   ├── orders.py              # 订单管理 (GET/POST/PUT/DELETE /api/orders)
│   ├── goods.py               # 货物管理 (GET/POST/PUT/DELETE /api/goods)
│   ├── packages.py            # 包裹管理 (GET/POST/PUT/DELETE /api/packages)
│   ├── vehicles.py            # 车辆管理 (GET/POST/PUT/DELETE /api/vehicles)
│   ├── drivers.py             # 司机管理 (GET/POST/PUT/DELETE /api/drivers)
│   ├── nodes.py               # 节点管理 (GET /api/nodes, POST/PUT/DELETE /api/nodes/storage-centers, /api/nodes/sorting-centers)
│   └── dependencies.py         # 依赖注入 (get_current_user JWT 验证, require_dispatcher RBAC)
│
├── services/                   # 业务逻辑层
│   ├── __init__.py
│   ├── auth_service.py         # 认证服务 (Token 生成, 密码验证, 用户查询)
│   ├── order_service.py        # 订单服务 (CRUD)
│   ├── goods_service.py        # 货物服务 (CRUD)
│   ├── package_service.py      # 包裹服务 (CRUD, 重新打包)
│   ├── vehicle_service.py     # 车辆服务 (CRUD)
│   ├── driver_service.py      # 司机服务 (CRUD)
│   └── node_service.py        # 节点服务 (存储中心/分拣中心 CRUD)
│
├── models/                     # SQLAlchemy ORM 模型
│   ├── __init__.py
│   ├── base.py                 # Base 声明基类
│   ├── user.py                 # User 模型 (id, username, password_hash, role)
│   ├── log_event.py            # LogEvent 模型 (操作日志)
│   ├── node.py                # Node 模型 (所有节点公共属性)
│   ├── storage_center.py      # StorageCenter 模型 (存储中心)
│   ├── sorting_center.py      # SortingCenter 模型 (分拣中心)
│   ├── order.py               # Order 模型 (订单)
│   ├── goods.py               # Goods 模型 (货物)
│   ├── package.py             # Package 模型 (包裹)
│   ├── vehicle.py             # Vehicle 模型 (车辆)
│   └── driver.py              # Driver 模型 (司机)
│
├── schemas/                    # Pydantic 请求/响应模型
│   ├── __init__.py
│   ├── user.py                 # UserLoginRequest, UserLoginResponse, UserResponse
│   ├── order.py               # OrderCreate, OrderUpdate, OrderResponse
│   ├── goods.py               # GoodsCreate, GoodsUpdate, GoodsResponse
│   ├── package.py             # PackageCreate, PackageUpdate, PackageResponse
│   ├── vehicle.py             # VehicleCreate, VehicleUpdate, VehicleResponse
│   ├── driver.py              # DriverCreate, DriverUpdate, DriverResponse
│   └── node.py               # NodeCreate, NodeUpdate, NodeResponse
│
├── core/                       # 核心模块
│   ├── error_codes.py          # 错误码定义
│   └── response_schema.py      # 统一响应 Schema (SuccessResponse, ErrorResponse)
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
│   └── init_demo_data.py      # 演示数据初始化 (用户、节点、车辆、司机、订单、货物)
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

### 已实现（阶段 1-2）

#### 认证与权限（阶段 1）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/auth/login` | 用户登录，返回 JWT Token | 否 |
| `GET` | `/api/auth/me` | 获取当前用户信息 | Bearer Token |
| `POST` | `/api/auth/logout` | 登出 | Bearer Token |
| `GET` | `/api/health` | 健康检查 | 否 |

#### 基础数据管理（阶段 2）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/orders` | 订单列表（分页、筛选） | Bearer Token |
| `GET` | `/api/orders/{code}` | 订单详情 | Bearer Token |
| `POST` | `/api/orders` | 创建订单 | Bearer Token (dispatcher) |
| `PUT` | `/api/orders/{code}` | 编辑订单 | Bearer Token (dispatcher) |
| `DELETE` | `/api/orders/{code}` | 删除订单 | Bearer Token (dispatcher) |
| `GET` | `/api/goods` | 货物列表（分页、筛选） | Bearer Token |
| `GET` | `/api/goods/{code}` | 货物详情 | Bearer Token |
| `POST` | `/api/goods` | 创建货物 | Bearer Token (dispatcher) |
| `PUT` | `/api/goods/{code}` | 编辑货物 | Bearer Token (dispatcher) |
| `DELETE` | `/api/goods/{code}` | 删除货物 | Bearer Token (dispatcher) |
| `GET` | `/api/packages` | 包裹列表（分页、筛选） | Bearer Token |
| `GET` | `/api/packages/{code}` | 包裹详情 | Bearer Token |
| `POST` | `/api/packages` | 创建包裹 | Bearer Token (dispatcher) |
| `PUT` | `/api/packages/{code}` | 编辑包裹 | Bearer Token (dispatcher) |
| `DELETE` | `/api/packages/{code}` | 删除包裹 | Bearer Token (dispatcher) |
| `POST` | `/api/packages/{code}/repack` | 重新打包 | Bearer Token (dispatcher) |
| `GET` | `/api/vehicles` | 车辆列表（分页、筛选） | Bearer Token |
| `GET` | `/api/vehicles/{code}` | 车辆详情 | Bearer Token |
| `POST` | `/api/vehicles` | 创建车辆 | Bearer Token (dispatcher) |
| `PUT` | `/api/vehicles/{code}` | 编辑车辆 | Bearer Token (dispatcher) |
| `DELETE` | `/api/vehicles/{code}` | 删除车辆 | Bearer Token (dispatcher) |
| `GET` | `/api/drivers` | 司机列表（分页、筛选） | Bearer Token |
| `GET` | `/api/drivers/{code}` | 司机详情 | Bearer Token |
| `POST` | `/api/drivers` | 创建司机 | Bearer Token (dispatcher) |
| `PUT` | `/api/drivers/{code}` | 编辑司机 | Bearer Token (dispatcher) |
| `DELETE` | `/api/drivers/{code}` | 删除司机 | Bearer Token (dispatcher) |
| `GET` | `/api/nodes` | 节点列表（分页、筛选） | Bearer Token |
| `GET` | `/api/nodes/{code}` | 节点详情 | Bearer Token |
| `POST` | `/api/nodes/storage-centers` | 创建存储中心 | Bearer Token (dispatcher) |
| `PUT` | `/api/nodes/storage-centers/{code}` | 编辑存储中心 | Bearer Token (dispatcher) |
| `DELETE` | `/api/nodes/storage-centers/{code}` | 删除存储中心 | Bearer Token (dispatcher) |
| `POST` | `/api/nodes/sorting-centers` | 创建分拣中心 | Bearer Token (dispatcher) |
| `PUT` | `/api/nodes/sorting-centers/{code}` | 编辑分拣中心 | Bearer Token (dispatcher) |
| `DELETE` | `/api/nodes/sorting-centers/{code}` | 删除分拣中心 | Bearer Token (dispatcher) |

### 规划中（阶段 3-8）

详见 `docs/` 目录下的 MVP 开发计划。核心接口包括：

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
- **迁移**：阶段 2 暂未使用 Alembic 迁移，直接通过 `Base.metadata.create_all()` 建表。阶段 3+ 将引入 Alembic 管理表结构变更。

```bash
# 阶段 2：直接建表
python -c "from config.database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"

# 阶段 3+：使用 Alembic 迁移（待启用）
# alembic upgrade head
# alembic revision --autogenerate -m "描述"
# alembic downgrade -1
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

## 已知问题与设计决策

### 阶段 2 已知问题

1. **`BigInteger` → `Integer`**：SQLAlchemy 2.0 在 SQLite 上 `BigInteger` 不会自动生成 `AUTOINCREMENT`，所有模型已改为 `Integer`（SQLite 的 INTEGER 支持 64 位）
2. **`Package.dispatch_id` 外键暂未添加**：指向 `node_dispatches` 表（阶段 4 实现），当前为普通 `Integer` 列
3. **Alembic 迁移暂未启用**：阶段 2 直接通过 `Base.metadata.create_all()` 建表，阶段 3+ 将引入 Alembic

### 演示数据规模

初始化脚本 (`scripts/init_demo_data.py`) 生成：
- 5 个存储中心 (L0)
- 2 个 1 级分拣中心 (L1)
- 50 个 0 级分拣中心 (L2)
- 70 辆车（7 个节点 × 10）
- 70 名司机
- 50 个订单（每单 2-7 个货物）
- 15 种货物类型

## 自测

### 阶段 1 自测（认证与权限）

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

### 阶段 2 自测（基础数据管理）

使用 `scripts/_test_api.py`（临时测试脚本，不提交）测试结果：

| 模块 | 接口 | 状态 |
|------|------|------|
| Health | `GET /api/health` | ✅ |
| Auth | `POST /api/auth/login` | ✅ |
| Auth | `GET /api/auth/me` | ✅ |
| Orders | `GET/POST/PUT` | ✅ |
| Goods | `GET/POST/PUT` | ✅ |
| Packages | `GET` | ✅ |
| Vehicles | `GET/POST/PUT/DELETE` | ✅ |
| Drivers | `GET/POST/PUT/DELETE` | ✅ |
| Nodes | `GET/POST/PUT/DELETE` (storage + sorting) | ✅ |

> 测试覆盖率：32/37 接口通过（86%），剩余 5 个为预期失败（重复创建返回 409）

## 相关文档

- [项目宪章](../../.codebuddy/CODEBUDDY.md)
- [系统架构设计说明书](../../docs/architecture/系统架构设计说明书.md)
- [MVP 开发计划 - 后端](../../docs/MVP开发计划-后端.md)
- [阶段 1 开发文档](../../My_doc/阶段1-认证与权限-开发文档.md)
- [阶段 1 API 契约文档](../../My_doc/阶段1-认证与权限-API契约文档.md)
- [阶段 2 开发文档](../../My_doc/阶段2-开发文档.md)

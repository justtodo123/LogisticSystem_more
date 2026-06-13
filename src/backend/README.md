# 智能物流平台 - 后端

基于 **Python 3.11 + FastAPI 0.110+** 的单体后端服务，承载 API 接口、调度算法和 DeepSeek AI 代理。

## 项目状态

**当前阶段**：阶段 5（路径规划与可视化 F006）已完成  
**下一阶段**：阶段 6（模拟送达 F013-1）

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
│   ├── orders.py              # 订单管理 (GET/POST/PUT/DELETE /api/orders + POST /import)
│   ├── goods.py               # 货物管理 (GET/PUT /api/goods)
│   ├── packages.py            # 包裹管理 (GET /api/packages + POST /repack)
│   ├── vehicles.py            # 车辆管理 (GET/POST/PUT/DELETE /api/vehicles)
│   ├── drivers.py             # 司机管理 (GET/POST/PUT/DELETE /api/drivers)
│   ├── nodes.py               # 节点管理 (GET /api/nodes, POST/PUT/DELETE storage-centers/sorting-centers)
│   ├── schedule.py            # 调度管理 (POST /api/schedule/global, POST /api/schedule/node-dispatch, GET 列表/详情)
│   ├── routes.py              # 路径规划 (POST /api/routes/plan, GET /api/routes, GET /api/routes/{code}, GET /api/routes/by-vehicle/{code}/coordinates)
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
│   ├── node_service.py        # 节点服务 (存储中心/分拣中心 CRUD)
│   ├── schedule_service.py    # 调度编排服务 (F007→F021→写库, 单事务)
│   ├── dispatch_service.py    # 节点调度服务 (F005→写库, 单事务)
│   └── route_service.py      # 路径规划服务 (F006→写库, 单事务)
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
│   ├── driver.py              # Driver 模型 (司机)
│   ├── global_schedule.py     # GlobalSchedule 模型 (F007 调度结果)
│   ├── dispatch_batch.py      # DispatchBatch 模型 (F005 调度批次)
│   ├── node_dispatch.py      # NodeDispatch 模型 (F005 节点调度明细)
│   └── route.py              # Route 模型 (F006 路径规划结果)
│
├── schemas/                    # Pydantic 请求/响应模型
│   ├── __init__.py
│   ├── user.py                 # UserLoginRequest, UserLoginResponse, UserResponse
│   ├── order.py               # OrderCreate, OrderUpdate
│   ├── goods.py               # GoodsUpdate
│   ├── package.py             # PackageRepack
│   ├── vehicle.py             # VehicleCreate, VehicleUpdate
│   ├── driver.py              # DriverCreate, DriverUpdate
│   ├── node.py                # StorageCenterCreate/Update, SortingCenterCreate/Update
│   ├── dispatch.py             # NodeDispatchRequest, DispatchBatchResponse, NodeDispatchResponse
│   ├── route.py               # RoutePlanRequest, RouteListResponse, RouteDetailResponse, RouteCoordinatesResponse
│   └── log_event.py           # LogEventResponse
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
├── algorithms/                 # 算法引擎 (F005/F006/F007/F021)
│   ├── __init__.py
│   ├── global_schedule.py      # F007 全局调度 (贪心算法, L0→L1→L2 路径规划)
│   ├── packaging.py            # F021 打包 (L0→L1 按节点对, L1→L2 按订单)
│   ├── node_dispatch.py       # F005 节点调度 (L0→L1, L1→L2 两次串行调用)
│   └── route_planning.py     # F006 路径规划 (Haversine + 2-opt 优化)
│
├── tests/                      # 测试
│   ├── conftest.py             # 测试夹具与配置
│   ├── phase3_api_verification.py  # 阶段3 API 集成验证脚本
│   ├── test_api/               # API 层测试
│   │   ├── test_schedule.py    # 调度接口测试
│   │   └── test_routes.py     # 路径规划接口测试
│   ├── test_services/          # 服务层测试
│   │   ├── test_schedule_service.py  # 调度编排服务测试
│   │   ├── test_dispatch_service.py # 节点调度服务测试
│   │   └── test_route_service.py    # 路径规划服务测试
│   ├── test_algorithms/        # 算法层测试
│   │   ├── test_global_schedule.py   # F007 全局调度算法测试
│   │   ├── test_packaging.py         # F021 打包算法测试
│   │   ├── test_node_dispatch.py    # F005 节点调度算法测试
│   │   └── test_route_planning.py  # F006 路径规划算法测试
│   └── test_integration/       # 集成测试
│       └── test_routes_integration.py  # 路径规划集成测试
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

### 已实现（阶段 1-3）

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
| `PUT` | `/api/goods/{code}` | 编辑货物 | Bearer Token (dispatcher) |
| `GET` | `/api/packages` | 包裹列表（分页、筛选） | Bearer Token |
| `GET` | `/api/packages/{code}` | 包裹详情 | Bearer Token |
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

#### 全局调度（阶段 3）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/schedule/global` | 触发全局调度 (F007 + F021) | Bearer Token (dispatcher) |
| `GET` | `/api/schedule/global` | 历史调度方案列表（分页） | Bearer Token |
| `GET` | `/api/schedule/global/{code}` | 调度方案详情（含 goods_schedules + packages） | Bearer Token |

#### 节点调度（阶段 4）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/schedule/node-dispatch` | 触发节点调度 (F005) | Bearer Token (dispatcher) |
| `GET` | `/api/schedule/batches` | 调度批次列表（分页、筛选） | Bearer Token |
| `GET` | `/api/schedule/batches/{code}` | 调度批次详情（含 dispatches） | Bearer Token |

#### 路径规划（阶段 5）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/routes/plan` | 手动触发路径规划 (F006) | Bearer Token (dispatcher) |
| `GET` | `/api/routes` | 路线列表（分页、筛选） | Bearer Token |
| `GET` | `/api/routes/{code}` | 路线详情（含 route_segments） | Bearer Token |
| `GET` | `/api/routes/by-vehicle/{code}/coordinates` | 车辆路线坐标（供可视化） | Bearer Token |

### 规划中（阶段 6-8）

详见 `docs/` 目录下的 MVP 开发计划。核心接口包括：

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
| `40001` | 200 | 全局调度失败（业务错误，如"没有找到符合条件的订单"） |
| `40100` | 200 | 用户名或密码错误（登录接口） |
| `40100` | 401 | 未登录或 Token 无效 |
| `40101` | 401 | Token 已过期，请重新登录 |
| `40300` | 403 | 无权限执行此操作 |
| `40400` | 404 | 资源不存在 |
| `40401` | 200 | 调度方案不存在 |
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
- **迁移**：已启用 Alembic 迁移管理表结构变更（阶段 3 引入）

```bash
# 初始化/更新数据库（使用 Alembic 迁移）
alembic upgrade head

# 创建新的迁移版本
alembic revision --autogenerate -m "描述"

# 回滚到上一个版本
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

## 已知问题与设计决策

### 阶段 4 已知问题

1. **`BigInteger` → `Integer`**：SQLAlchemy 2.0 在 SQLite 上 `BigInteger` 不会自动生成 `AUTOINCREMENT`，所有模型已改为 `Integer`（SQLite 的 INTEGER 支持 64 位）
2. **调度算法仅支持 `traditional`**：DeepSeek AI 调度（`algorithm=deepseek`）将在阶段 8 实现
3. **F005 算法简化**：当前车辆匹配仅考虑载重，未考虑距离评分（阶段 5 或阶段 6 补充）
4. **演示数据车辆载重**：已调整为 50.0（原 10.0 不足以承载单个包裹重量）

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

测试时间：2026-06-13，结果：**63/63 通过（100%）**

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 数据完整性 | 节点57个（L0:5, L1:2, L2:50）、车辆70、司机70、订单53、货物200 | ✅ |
| Orders | GET/POST/PUT/DELETE + 导入 + 状态筛选 + 不含id | ✅ |
| Goods | GET列表/详情 + PUT编辑 + 按order_code/status筛选 | ✅ |
| Packages | GET列表/详情 + repack（状态校验） | ✅ |
| Vehicles | GET/POST/PUT/DELETE + 按status/node_code筛选 | ✅ |
| Drivers | GET/POST/PUT/DELETE + 按node_code筛选 | ✅ |
| Nodes | GET列表/详情 + level筛选 + node_type筛选 + 存储中心CRUD + 分拣中心CRUD | ✅ |
| 权限 | manager 全部写操作返回403、无Token返回401 | ✅ |
| 业务校验 | 订单目的地校验（必须0级分拣中心）、删除配送中订单拒绝、repack状态校验 | ✅ |
| 响应格式 | 统一{code, message, data, meta} + 分页含total/items + 不含数据库id | ✅ |

### 阶段 3 自测（全局调度 F007 + F021）

测试时间：2026-06-13，结果：**全部通过**

| 类别 | 测试项 | 结果 |
|------|--------|------|
| F007 算法 | 贪心算法选择 L1、硬约束检查（容量/同订单汇聚/存储时长）、评分计算 | ✅ |
| F021 打包 | L0→L1 按节点对打包、L1→L2 按订单打包、货物状态更新 | ✅ |
| API 集成 | POST /api/schedule/global 触发调度、GET 列表/详情、调度结果可复现 | ✅ |
| 事务原子性 | global_schedules + packages + orders/goods 状态更新单事务 | ✅ |
| 权限 | dispatcher 可触发调度、manager 返回 403 | ✅ |
| 错误处理 | 无 pending 订单 → 40001、不存在的 schedule_code → 40401 | ✅ |
| 数据完整性 | 2 条调度记录、59 个包裹、207 个货物状态 packed、53 个订单状态 delivering | ✅ |

### 阶段 4 自测（节点间调度 F005）

测试时间：2026-06-14，结果：**全部通过**

| 类别 | 测试项 | 结果 |
|------|--------|------|
| F005 算法 | L0→L1 调度、L1→L2 调度、车辆匹配（载重/节点优先级）、返回任务添加 | ✅ |
| F005 算法 | 车辆不足错误、包裹状态错误、L0→L1 未完成错误 | ✅ |
| API 集成 | POST /api/schedule/node-dispatch 触发调度、GET /api/schedule/batches 列表、GET /api/schedule/batches/{code} 详情 | ✅ |
| 事务原子性 | dispatch_batches + node_dispatches + packages/goods/vehicles/drivers 状态更新单事务 | ✅ |
| 权限 | dispatcher 可触发调度、manager 返回 403 | ✅ |
| 错误处理 | 无可用车辆 → 40001、L0→L1 未完成 → 40001、不存在的 schedule_code → 40401 | ✅ |
| 数据完整性 | 调度批次、节点调度明细、包裹状态更新、车辆/司机状态更新 | ✅ |

### 阶段 5 自测（路径规划 F006）

测试时间：2026-06-14，结果：**25/25 通过（100%）**

| 类别 | 测试项 | 结果 |
|------|--------|------|
| F006 算法 | Haversine 距离计算、路径路段生成、碳排放计算 | ✅ |
| F006 算法 | 2-opt 优化（MVP不触发）、空任务列表错误、节点不存在错误 | ✅ |
| API 集成 | POST /api/routes/plan 触发路径规划、GET /api/routes 列表、GET /api/routes/{code} 详情 | ✅ |
| API 集成 | GET /api/routes/by-vehicle/{code}/coordinates 车辆路线坐标 | ✅ |
| 事务原子性 | routes 表写入与 F005 在同一个事务中 | ✅ |
| 权限 | dispatcher 可触发路径规划、manager 返回 403 | ✅ |
| 错误处理 | 批次不存在 → 40001、路线不存在 → 40400、车辆不存在 → 40400 | ✅ |
| 数据完整性 | 路线记录、route_segments JSON、总距离/时间/碳排放 | ✅ |
| 集成测试 | 完整路径规划流程（API→算法→数据库→查询） | ✅ |

## 相关文档

- [项目宪章](../../.codebuddy/CODEBUDDY.md)
- [系统架构设计说明书](../../docs/architecture/系统架构设计说明书.md)
- [MVP 开发计划 - 后端](../../docs/MVP开发计划-后端.md)
- [阶段 2 开发文档](../../My_doc/阶段2-开发文档.md)
- [阶段 2 API 契约文档](../../My_doc/阶段2-API契约文档.md)（V1.4）
- [阶段 2 测试报告](../../My_doc/阶段2-测试报告.md)（63/63 通过）
- [联调反馈 - 阶段2 - 致后端](../../My_doc/联调反馈-阶段2-致后端.md)
- [阶段 3 开发文档](../../My_doc/阶段3开发文档-全局调度F007+F021.md)
- [阶段 3 API 契约文档](../../docs/api-contract/api-contract-phase3.md)（V1.0）
- [阶段 4 开发文档](../../My_doc/阶段4开发文档.md)
- [阶段 4 API 契约文档](../../My_doc/阶段4-API契约文档.md)（V1.0）
- [阶段 5 开发文档](../../My_doc/阶段5开发文档-F006路径规划.md)
- [阶段 5 API 契约文档](../../My_doc/阶段5-API契约文档.md)（V1.0）

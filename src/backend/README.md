# 智能物流平台 - 后端

基于 **Python 3.11 + FastAPI 0.110+** 的单体后端服务，承载 API 接口、调度算法和 DeepSeek AI 代理。

## 项目状态

**当前阶段**：阶段 4（节点间调度 F005）已完成  
**下一阶段**：阶段 5（路径规划与可视化 F006）

**阶段4最新更新**：
- 修复 `demo_mode` 逻辑，使其符合项目宪章设计
- `demo_mode=true`：一次调用完成 L0→L1 和 L1→L2 两次调度
- `demo_mode=false`：首次调用仅执行 L0→L1，第二次调用才执行 L1→L2
- 自动检测调用阶段（通过检查是否已有 `l0_l1_done` 状态的批次）
- ✅ **状态机实现完成** (2026-06-17)：实现所有状态流转逻辑，包括 F005 调用后、模拟送达、重新打包等场景
- ✅ **单元测试通过** (2026-06-17)：5/5 测试通过，验证状态流转正确性

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
python -m  scripts.init_demo_data

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
│   └── state_machine.py      # 状态机服务 (管理所有状态流转) ✅ 新增 (2026-06-17)
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
│   └── node_dispatch.py      # NodeDispatch 模型 (F005 节点调度明细)
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
│   └── node_dispatch.py       # F005 节点调度 (L0→L1, L1→L2 两次串行调用, 支持demo_mode)
│
├── tests/                      # 测试
│   ├── conftest.py             # 测试夹具与配置
│   ├── phase3_api_verification.py  # 阶段3 API 集成验证脚本
│   ├── test_api/               # API 层测试
│   │   └── test_schedule.py    # 调度接口测试
│   ├── test_services/          # 服务层测试
│   │   ├── test_schedule_service.py  # 调度编排服务测试
│   │   └── test_dispatch_service.py # 节点调度服务测试
│   └── test_algorithms/        # 算法层测试
│       ├── test_global_schedule.py   # F007 全局调度算法测试
│       ├── test_packaging.py         # F021 打包算法测试
│       └── test_node_dispatch.py    # F005 节点调度算法测试
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

### 规划中（阶段 5-8）

详见 `docs/` 目录下的 MVP 开发计划。核心接口包括：

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

测试时间：2026-06-14，更新：2026-06-17，结果：**全部通过**

| 类别 | 测试项 | 结果 |
|------|--------|------|
| F005 算法 | L0→L1 调度、L1→L2 调度、车辆匹配（载重/节点优先级）、返回任务添加 | ✅ |
| F005 算法 | 车辆不足错误、包裹状态错误、L0→L1 未完成错误 | ✅ |
| F005 算法 | demo_mode=true 一次完成两次调度 | ✅ |
| F005 算法 | demo_mode=false 分阶段调度（首次L0→L1，第二次L1→L2） | ✅ |
| F005 算法 | 自动检测调用阶段（通过检查是否已有 l0_l1_done 状态的批次） | ✅ |
| ✅ 状态机 | F005调用后状态更新（货物、包裹、车辆、司机）| ✅ (2026-06-17) |
| ✅ 状态机 | L0→L1模拟送达后状态更新（包裹、货物、批次、车辆、司机）| ✅ (2026-06-17) |
| ✅ 状态机 | L1重新打包后状态更新（货物、新包裹）| ✅ (2026-06-17) |
| ✅ 状态机 | L1→L2模拟送达后状态更新（包裹、货物、订单、批次、车辆、司机）| ✅ (2026-06-17) |
| ✅ 单元测试 | 5/5 测试通过，验证状态流转正确性 | ✅ (2026-06-17) |
| API 集成 | POST /api/schedule/node-dispatch 触发调度、GET /api/schedule/batches 列表、GET /api/schedule/batches/{code} 详情 | ✅ |
| 事务原子性 | dispatch_batches + node_dispatches + packages/goods/vehicles/drivers 状态更新单事务 | ✅ |
| 权限 | dispatcher 可触发调度、manager 返回 403 | ✅ |
| 错误处理 | 无可用车辆 → 40001、L0→L1 未完成 → 40001、不存在的 schedule_code → 40401 | ✅ |
| 数据完整性 | 调度批次、节点调度明细、包裹状态更新、车辆/司机状态更新 | ✅ |

## demo_mode 使用指南

### 概述

`POST /api/schedule/node-dispatch` 接口支持两种模式：
- **`demo_mode=true`**：演示模式，一次调用完成 L0→L1 和 L1→L2 两次调度（用于课堂演示）
- **`demo_mode=false`**：正常模式，分两次调用，首次执行 L0→L1，第二次执行 L1→L2（需等待 L1 送达）

### demo_mode=true（演示模式）

**使用场景**：课堂演示、快速测试完整链路

**请求示例**：
```json
{
  "schedule_code": "GS20260614001",
  "demo_mode": true
}
```

**响应结果**（HTTP 200）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "completed",
    "dispatches": [
      {
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          },
          {
            "from_node_code": "L1001",
            "to_node_code": "SC001",
            "package_codes": [],
            "is_return": true
          }
        ],
        "total_distance": 25.3,
        "total_time": 0.42
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**关键字段说明**：
- `status`: `"completed"` - 批次已完成（L0→L1 和 L1→L2 都已完成）
- `dispatches`: 包含所有调度明细（L0→L1 + L1→L2）
- `tasks[].is_return`: `false` = 去程任务，`true` = 返程任务

**后续操作**：
1. **查看调度批次详情**：`GET /api/schedule/batches/{batch_code}`
2. **路径规划**（阶段5，当前未实现）：`POST /api/routes/plan`（为每辆车规划路径）
3. **模拟送达**（阶段6，当前未实现）：`POST /api/simulation/deliver`（模拟货物送达）

> **⚠️ 注意**：路径规划和模拟送达功能当前未实现，计划分别在阶段5和阶段6实现。当前阶段4只能完成到节点调度。

### demo_mode=false（正常模式）

**使用场景**：生产环境、真实物流调度

**第一次调用**（执行 L0→L1 调度）：

请求：
```json
{
  "schedule_code": "GS20260614001",
  "demo_mode": false
}
```

响应（HTTP 200）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "l0_l1_done",
    "dispatches": [
      {
        "vehicle_code": "VEHSC00101",
        "driver_code": "DRVSC00101",
        "tasks": [
          {
            "from_node_code": "SC001",
            "to_node_code": "L1001",
            "package_codes": ["PKG202606140001"],
            "is_return": false
          }
        ],
        "total_distance": 12.5,
        "total_time": 0.21
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**关键字段说明**：
- `status`: `"l0_l1_done"` - L0→L1 调度已完成，等待 L1 送达
- `dispatches`: 只包含 L0→L1 的调度明细

**后续操作**（等待 L1 送达）：
1. **模拟送达**（阶段6，**当前未实现**）：`POST /api/simulation/deliver`
   - 将 L0→L1 的包裹状态更新为 `delivered`
   - 货物状态更新为 `pending_pack`（需要在 L1 重新打包）
   
   > **⚠️ 注意**：模拟送达功能计划在阶段6实现，当前阶段4无法执行此操作。
   
2. **重新打包**（自动，需模拟送达后触发）：L1 送达后，系统自动触发重新打包（F021）
   - 将货物打包成 L1→L2 的包裹

**第二次调用**（执行 L1→L2 调度）：

请求（使用同一个 `schedule_code`）：
```json
{
  "schedule_code": "GS20260614001",
  "demo_mode": false
}
```

响应（HTTP 200）：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260614001",
    "status": "completed",
    "dispatches": [
      {
        "vehicle_code": "VEHL100101",
        "driver_code": "DRVL100101",
        "tasks": [
          {
            "from_node_code": "L1001",
            "to_node_code": "SO001",
            "package_codes": ["PKG202606140051"],
            "is_return": false
          }
        ],
        "total_distance": 8.3,
        "total_time": 0.14
      }
    ]
  },
  "meta": {
    "degraded": false,
    "degraded_reason": null
  }
}
```

**关键字段说明**：
- `status`: `"completed"` - 批次已完成（L1→L2 也已完成）
- `dispatches`: 包含 L1→L2 的调度明细

### 自动检测调用阶段

系统会自动检测当前应该执行哪个阶段的调度：
- 如果不存在 `l0_l1_done` 状态的批次 → 执行 L0→L1 调度
- 如果已存在 `l0_l1_done` 状态的批次 → 执行 L1→L2 调度

**无需手动指定阶段**，只需多次调用同一接口即可。

## 完整链路指南（阶段 3 → 4 → 5 → 6）

### 概述

完整物流调度链路包含以下阶段：
1. **阶段 3**：全局调度（F007）+ 打包（F021）
2. **阶段 4**：节点间调度（F005）
3. **阶段 6**：模拟送达（F013-1）
4. **阶段 5**：路径规划（F006）

### ⚠️ 重要说明

**当前阶段4的限制**：
- ✅ **已实现**：阶段3（全局调度）+ 阶段4（节点调度）
- ❌ **未实现**：阶段5（路径规划）、阶段6（模拟送达）
- ⚠️ **影响**：完整链路（阶段3→4→5→6）在现阶段**无法完全测试**

**可以完成的操作**：
1. 触发全局调度（阶段3）
2. 触发节点调度（阶段4）
3. 查看调度批次和明细
4. 验证状态变更（包裹、车辆、司机）

**无法完成的操作**（需等待阶段5和阶段6）：
1. 模拟送达（阶段6）- 无法将包裹状态更新为 `delivered`
2. 路径规划（阶段5）- 无法为车辆规划最优路径
3. 完成完整链路测试

---

### 完整链路步骤

#### 步骤 1：全局调度（阶段 3）

**接口**：`POST /api/schedule/global`

**请求**：
```json
{
  "order_codes": ["O001", "O002"],
  "algorithm": "traditional"
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260614001",
    "total_orders": 2,
    "total_packages": 5,
    "goods_schedules": [...]
  }
}
```

**状态变更**：
- 订单状态：`pending` → `delivering`
- 货物状态：`pending_pack` → `packed`
- 包裹状态：`pending_pack` → `packed`

#### 步骤 2：节点调度（阶段 4）

**接口**：`POST /api/schedule/node-dispatch`

**演示模式（推荐用于测试）**：
```json
{
  "schedule_code": "GS20260614001",
  "demo_mode": true
}
```

**响应**：`status="completed"`，可直接进入步骤 4（路径规划）

**正常模式**：
```json
{
  "schedule_code": "GS20260614001",
  "demo_mode": false
}
```

**第一次调用响应**：`status="l0_l1_done"`，需执行步骤 3（模拟送达）

**状态变更**（L0→L1 完成后）：
- 包裹状态：`packed` → `in_transit`
- 货物状态：`packed` → `in_transit`
- 车辆状态：`idle` → `delivering`
- 司机状态：`idle` → `busy`

#### 步骤 3：模拟送达（阶段 6）

**接口**：`POST /api/simulation/deliver`

**请求**：
```json
{
  "batch_code": "BATCH20260614001",
  "level": 0
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "delivered_packages": 5,
    "delivered_goods": 15
  }
}
```

**状态变更**（L0→L1 送达后）：
- 包裹状态：`in_transit` → `delivered`
- 货物状态：`in_transit` → `pending_pack`（需在 L1 重新打包）
- 车辆状态：`delivering` → `idle`
- 司机状态：`busy` → `idle`

**重新打包**（自动触发）：
- 系统自动将 `pending_pack` 的货物打包成 L1→L2 的包裹
- 包裹状态：`pending_pack` → `packed`

**第二次调用节点调度**（L1→L2）：
```json
{
  "schedule_code": "GS20260614001",
  "demo_mode": false
}
```

**响应**：`status="completed"`

#### 步骤 4：路径规划（阶段 5）

**接口**：`POST /api/routes/plan`

**请求**：
```json
{
  "batch_code": "BATCH20260614001"
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "routes": [
      {
        "route_code": "RT20260614001",
        "vehicle_code": "VEHSC00101",
        "total_distance": 25.3,
        "total_time": 0.42,
        "route_segments": [...]
      }
    ]
  }
}
```

**状态变更**：
- 路线已规划，可查看路线详情：`GET /api/routes/{route_code}`
- 查看路线坐标：`GET /api/routes/by-vehicle/{vehicle_code}/coordinates`

#### 步骤 5：L1→L2 模拟送达（阶段 6）

**接口**：`POST /api/simulation/deliver`

**请求**：
```json
{
  "batch_code": "BATCH20260614001",
  "level": 1
}
```

**响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "delivered_packages": 8,
    "delivered_goods": 15,
    "completed_orders": 2
  }
}
```

**状态变更**（L1→L2 送达后）：
- 包裹状态：`in_transit` → `delivered`
- 货物状态：`in_transit` → `delivered`
- 订单状态：所有货物送达 → `completed`
- 批次状态：`completed`
- 车辆状态：`delivering` → `idle`
- 司机状态：`busy` → `idle`

### 完整链路示意图

```
阶段 3: POST /api/schedule/global
  ↓
  订单: pending → delivering
  货物: pending_pack → packed
  包裹: pending_pack → packed
  ↓
阶段 4: POST /api/schedule/node-dispatch (demo_mode=true)
  ↓
  批次: pending → completed (一次性完成 L0→L1 和 L1→L2)
  包裹: packed → in_transit
  车辆: idle → delivering
  司机: idle → busy
  ↓
阶段 6: POST /api/simulation/deliver (level=0 和 level=1)
  ↓
  包裹: in_transit → delivered
  货物: in_transit → delivered
  订单: delivering → completed
  车辆: delivering → idle
  司机: busy → idle
  ↓
阶段 5: POST /api/routes/plan
  ↓
  路线规划完成，可查看路线图
```

### 常见问题

**Q1: demo_mode=true 和 false 的区别是什么？**

A: 
- `demo_mode=true`：跳过 L1 实际送达等待，一次调用完成两次调度，适合演示
- `demo_mode=false`：分两次调用，首次 L0→L1，第二次 L1→L2，需等待 L1 送达

**Q2: 如何查看调度批次详情？**

A: 使用 `GET /api/schedule/batches/{batch_code}` 接口，可查看完整的调度明细（dispatches）

**Q3: 如何知道批次状态？**

A: 使用 `GET /api/schedule/batches` 接口，查看 `status` 字段：
- `pending`: 批次已创建，但未执行调度
- `l0_l1_done`: L0→L1 调度已完成，等待 L1 送达
- `completed`: L1→L2 调度已完成（或 demo_mode=true 时一次性完成）
- `failed`: 调度失败

**Q4: 如果 L0→L1 调度失败怎么办？**

A: 批次状态变为 `failed`，不会执行 L1→L2 调度。需要检查错误信息，解决问题后重新调用。

**Q5: 阶段 4 完成后，如何进入阶段 5？**

A: 阶段 4 完成后，可以调用阶段 5 的路径规划接口（`POST /api/routes/plan`），为每辆车规划最优路径。

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
- [阶段 4 API 契约文档](../../docs/api-contract/api-contract-phase4.md)（V1.1）

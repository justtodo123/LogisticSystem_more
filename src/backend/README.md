# 智能物流平台 - 后端

基于 **Python 3.11 + FastAPI 0.110+** 的单体后端服务，承载 API 接口、调度算法和 DeepSeek AI 代理。

## 项目状态

**当前阶段**：P1-2（全局调度增强）✅ 已完成  
**项目状态**：🎉 全部 8 阶段 MVP + P1-1 + P1-2 开发完成

**P1-2 最新更新** (2026-06-24)：
- ✅ **预览 → 确认两步流**：`POST /api/schedule/global` 默认 preview 模式，生成 draft 方案（仅 F007，不打包）
- ✅ **确认接口**：`POST /api/schedule/confirm/{code}` 执行 F021 打包 + 状态更新，draft → active
- ✅ **丢弃接口**：`DELETE /api/schedule/draft/{code}` 手动丢弃未确认 draft 方案
- ✅ **active 重复检查**：同一批订单已存在 active 方案时拒绝 preview，避免冲突
- ✅ **confirm 状态校验**：订单状态已变化时拒绝确认（40003），异常时自动删除 draft（50001）
- ✅ **`global_schedules` 新增 `status` 字段**：`draft` / `active`，Alembic 迁移 c78f9b436833
- ✅ **列表默认过滤**：`GET /api/schedule/global` 默认仅返回 `status=active` 方案
- ✅ **重规划兼容**：`is_replan=True` 跳过 active 检查，confirm 允许 delivering 状态订单
- ✅ **测试全部通过**：298/298 测试通过（含 P1-2 新增的 confirm/discard/replan 用例）

**P1-1 最新更新** (2026-06-24)：
- ✅ **AI 自然语言调度完成**：`POST /api/ai/parse` 接收自然语言 → DeepSeek 解析为算法参数 → 自动执行完整调度链路
- ✅ **四种参数模式**：`ai`（纯 DeepSeek 解析）/ `manual`（纯手动权重）/ `hybrid`（AI + 权重覆盖）/ `default`（默认参数）
- ✅ **两种执行模式**：新建调度（全部 pending 订单）+ 版本化重规划（指定 `schedule_codes`）
- ✅ **dry-run 模式**：`execute=false` 仅返回解析参数，不执行调度不写库
- ✅ **系统上下文增强**：DeepSeek 提示词自动注入待分配订单、可用车辆、历史方案指标（对比评分/距离/时间）
- ✅ **DeepSeek 降级策略**：API 调用失败自动 fallback 默认参数，`meta.degraded=true` 明确告知用户
- ✅ **DeepSeek 调用埋点**：每次调用记录到 `log_events`（成功/失败/degraded）
- ✅ **批量重规划**：`schedule_codes` 支持多条，逐条生成新版本
- ✅ **P1 占位**：`/api/ai/explain`、`/api/ai/review`、`/api/ai/analyze-exception` 返回 501

**P1-1 最新更新** (2026-06-24)：
- ✅ **P1-05 score 归一化**：全局调度方案 API 响应新增 `score_display` 字段（0~100 整数，越高越好），保留原 `score` 字段确保向后兼容
- ✅ **P1-06 全局方案 DTO 优化**：`GET /api/schedule/global/{code}` 响应中 `goods_schedules.path` 从字符串数组改为对象数组（含 `node_code` + `node_name`）
- ✅ **P1-06 货物描述字段**：`goods_schedules` 每项新增 `goods_name`、`goods_type`、`weight`、`volume`、`node_code`、`order_code`
- ✅ **P1-07 节点调度 DTO 优化**：`tasks` 新增 `from_node_name`、`to_node_name`，`package_codes` 展开为 `package_details`（含包裹详情和货物详情）
- ✅ **P1-07 过滤参数**：`GET /api/schedule/batches/{code}` 新增 `vehicle_code`、`level_phase` 过滤参数
- ✅ **P1-07 新增端点**：`GET /batches/{batch_code}/dispatches`、`GET /{schedule_code}/dispatches`、`GET /dispatches/{dispatch_code}`
- ✅ **API 契约文档**：更新 `docs/api-contract/api-contract-p1-1.md` 记录所有变更

**阶段4最新更新** (2026-06-17)：
- **阶段4实现范围**：仅完整实现 `demo_mode=true`，`demo_mode=false` 完整流程推迟到阶段6
- `demo_mode=true`：一次调用完成 L0→L1 和 L1→L2 两次调度（含自动模拟送达 + L1 重新打包 + 自动送达L2），货物从L0直达L2
- `demo_mode=false`：代码框架已预留（`_check_packages_by_level()` 智能检测 + 4种场景），但完整流程需阶段6的模拟送达接口配合
- ✅ **状态机实现完成** (2026-06-17)：实现所有状态流转逻辑，包括 F005 调用后、模拟送达、重新打包等场景
- ✅ **单元测试通过** (2026-06-17)：5/5 测试通过，验证状态流转正确性

**阶段5最新更新** (2026-06-18)：
- ✅ **单元测试完成**：创建算法层、服务层、API层和集成测试，共 35 个测试全部通过
- ✅ **算法层测试** (`tests/test_algorithms/test_route_planning.py`)：12/12 通过，测试 Haversine 距离计算、路线编码生成、路径规划算法
- ✅ **服务层测试** (`tests/test_services/test_route_service.py`)：13/13 通过，测试 RouteService 的所有方法
- ✅ **API层测试** (`tests/test_routes_api.py`)：6/6 通过，测试路径规划 API 端点
- ✅ **集成测试** (`tests/test_routes_integration.py`)：4/4 通过，测试完整路径规划流程
- ✅ **测试覆盖完整**：从算法层到服务层、API层再到集成测试，确保阶段5功能正确性

**阶段6最新更新** (2026-06-18)：
- ✅ **模拟送达功能完成**：实现状态流转逻辑，包括 L0→L1 和 L1→L2 送达
- ✅ **功能边界清理**：移除自动触发逻辑（重新打包/F005/重新调度），模拟送达仅负责状态流转
- ✅ **状态流转修复**：模拟送达第一次后货物状态从 `in_transit` → `packed`（F021 已生成 L1→L2 包裹，无需重新打包）
- ✅ **单元测试完成**：7/7 测试通过，验证状态流转正确性

**阶段7最新更新** (2026-06-22)：
- ✅ **方案A实施完成**：新建 `ReplanService` + `ExceptionService`，不修改现有调度/路径规划服务层
- ✅ **异常事件 CRUD**：创建、列表（分页/筛选）、详情、更新、标记已解决 5 个 API 端点
- ✅ **重规划双模式**：`redispatch`（F007→F021→F005→F006 全链路） + `reroute`（仅 F006 路径规划）
- ✅ **版本链实现**：重规划生成新版记录，`version+1`、`parent_id` 指向前一版本、`is_replan=true`
- ✅ **异常自动关联**：创建异常时自动将关联订单/货物/包裹状态置为 `exception`
- ✅ **repack_at_l1 精确匹配修复**：修复多订单同路线场景下包裹错误复用导致遗漏的BUG
- ✅ **单元测试完成**：32/32 全部通过（覆盖异常服务、重规划服务、集成测试）

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
python -m scripts.init_demo_data

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
│   ├── exception_events.py    # 异常管理 (GET/POST /api/exceptions, POST /replan, PUT /resolve)  [阶段7]
│   ├── simulation.py          # 模拟送达 (POST /api/simulation/deliver, GET /status)  [阶段6]
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
│   ├── route_service.py       # 路径规划服务 (F006→写库, 单事务)
│   ├── exception_service.py   # 异常事件服务 (CRUD + 触发重规划)  [阶段7]
│   ├── replan_service.py      # 重规划服务 (redispatch/reroute + 版本链)  [阶段7]
│   ├── simulation_service.py  # 模拟送达服务 (状态流转)  [阶段6]
│   └── state_machine.py       # 状态机服务 (状态流转逻辑)
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
│   ├── route.py              # Route 模型 (F006 路径规划结果)
│   └── exception_event.py    # ExceptionEvent 模型 (异常事件)  [阶段7]
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
│   └── exception_event.py     # CreateExceptionEvent, TriggerReplan, UpdateException, ExceptionEventResponse  [阶段7]
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
│   ├── init_users.py          # 用户初始化
│   ├── init_demo_data.py      # 演示数据初始化 (用户、节点、车辆、司机、订单、货物)
│   └── init_log_events.py     # 日志事件初始化
│
├── algorithms/                 # 算法引擎 (F005/F006/F007/F021)
│   ├── __init__.py
│   ├── global_schedule.py      # F007 全局调度 (贪心算法, L0→L1→L2 路径规划)
│   ├── packaging.py            # F021 打包 (L0→L1 按节点对, L1→L2 按订单)
│   ├── node_dispatch.py       # F005 节点调度 (L0→L1, L1→L2 两次串行调用, 支持demo_mode)
│   └── route_planning.py      # F006 路径规划 (Haversine + 2-opt)
│
├── tests/                      # 测试
│   ├── conftest.py             # 测试夹具与配置
│   ├── test_routes_api.py      # 路径规划 API 测试 (6个测试)
│   ├── test_routes_integration.py  # 路径规划集成测试 (4个测试)
│   ├── test_algorithms/        # 算法层测试
│   │   ├── test_global_schedule.py   # F007 全局调度算法测试
│   │   ├── test_packaging.py         # F021 打包算法测试
│   │   ├── test_node_dispatch.py    # F005 节点调度算法测试
│   │   └── test_route_planning.py   # F006 路径规划算法测试 (12个测试)
│   ├── test_services/          # 服务层测试
│   │   ├── test_schedule_service.py  # 调度编排服务测试
│   │   ├── test_route_service.py     # 路径规划服务测试 (13个测试)
│   │   ├── test_exception_service.py # 异常事件服务测试 (19个测试)  [阶段7]
│   │   ├── test_state_machine.py     # 状态机测试 (7个测试)  [阶段6]
│   │   └── test_dispatch_service.py  # 调度服务测试
│   ├── test_api/               # API 层测试
│   │   └── test_schedule.py    # 调度接口测试
│   └── tests/integration/      # 集成测试
│       ├── test_full_dispatch_flow.py       # 完整调度链路 F007→F021→F005→F006
│       ├── test_dispatch_pipeline.py        # 调度管道集成测试  [阶段7]
│       ├── test_auto_redispatch.py          # 自动重规划集成测试  [阶段7]
│       └── test_exception_replan.py         # 异常重规划集成测试  [阶段7]
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

### 已实现（阶段 1-8 + P1-1 + P1-2）

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

#### 全局调度（阶段 3 + P1-1 优化 + P1-2 增强）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/schedule/global` | 预览调度方案 (F007)，生成 draft，不打包不更新状态 | Bearer Token (dispatcher) |
| `POST` | `/api/schedule/confirm/{code}` | 确认 draft 方案，执行 F021 打包 + 状态更新 → active | Bearer Token (dispatcher) |
| `DELETE` | `/api/schedule/draft/{code}` | 丢弃未确认的 draft 方案 | Bearer Token (dispatcher) |
| `GET` | `/api/schedule/global` | 历史方案列表（分页，含 score_display，默认过滤 draft） | Bearer Token |
| `GET` | `/api/schedule/global/{code}` | 调度方案详情（含 goods_schedules + packages + score_display + status） | Bearer Token |

> **P1-1 优化**：`GET /api/schedule/global/{code}` 响应中 `goods_schedules.path` 改为对象数组（含 `node_code` + `node_name`），每项新增 `goods_name`、`goods_type`、`weight`、`volume`、`node_code`、`order_code`；所有全局调度接口返回 `score_display`（0~100 归一化百分制）
>
> **P1-2 增强**：全局调度改为两步流（preview → confirm），响应新增 `status` 字段（`draft` / `active`）；列表默认过滤 draft；支持 `?status=draft` 查询预览方案

#### 节点调度（阶段 4 + P1-1 优化）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/schedule/node-dispatch` | 触发节点调度 (F005) | Bearer Token (dispatcher) |
| `GET` | `/api/schedule/batches` | 调度批次列表（分页、筛选） | Bearer Token |
| `GET` | `/api/schedule/batches/{code}` | 调度批次详情（含 dispatches，支持过滤） | Bearer Token |
| `GET` | `/api/schedule/batches/{batch_code}/dispatches` | 按批次查询调度明细（P1-07 新增） | Bearer Token |
| `GET` | `/api/schedule/{schedule_code}/dispatches` | 按方案查询所有调度明细（P1-07 新增） | Bearer Token |
| `GET` | `/api/schedule/dispatches/{dispatch_code}` | 查询单个调度明细详情（P1-07 新增） | Bearer Token |

> **P1-1 优化**：`GET /api/schedule/batches/{code}` 响应中 `tasks` 新增 `from_node_name`、`to_node_name`，`package_codes` 展开为 `package_details`（含包裹详情和货物详情）；支持 `vehicle_code`、`level_phase` 过滤参数

#### 路径规划（阶段 5）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/routes/plan` | 手动触发路径规划 (F006) | Bearer Token (dispatcher) |
| `GET` | `/api/routes` | 路线列表（分页、筛选） | Bearer Token |
| `GET` | `/api/routes/{code}` | 路线详情（含 route_segments） | Bearer Token |
| `GET` | `/api/routes/by-vehicle/{code}/coordinates` | 车辆路线坐标（供可视化） | Bearer Token |

#### 模拟送达（阶段 6）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/simulation/deliver` | 模拟送达，驱动状态流转 | Bearer Token (dispatcher) |
| `GET` | `/api/simulation/status/{batch_code}` | 查询送达状态和待重新打包货物（P1） | Bearer Token (dispatcher/manager) |
| `POST` | `/api/simulation/deliver-batch` | 批量送达同一批次所有车辆（P1） | Bearer Token (dispatcher) |

#### 异常管理（阶段 7）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/exceptions` | 异常事件列表（分页、筛选） | Bearer Token |
| `POST` | `/api/exceptions` | 创建异常事件 | Bearer Token (dispatcher) |
| `GET` | `/api/exceptions/{event_code}` | 异常事件详情 | Bearer Token |
| `POST` | `/api/exceptions/{event_code}/replan` | 触发重规划（redispatch 或 reroute） | Bearer Token (dispatcher) |
| `PUT` | `/api/exceptions/{event_code}` | 更新异常事件 | Bearer Token (dispatcher) |
| `PUT` | `/api/exceptions/{event_code}/resolve` | 标记异常已解决（status → resolved，记录 resolved_at） | Bearer Token (dispatcher) |

> **异常事件模型**：`exception_events` 表字段 — `event_code`、`exception_type`（road / package / node）、`exception_subtype`（congestion / damage / capacity_limit）、`target_type`（node / package / route / vehicle）、`target_code`、`recommended_action`（redispatch / reroute）、`related_schedule_code`、`replan_batch_code`、`description`、`status`（open / resolved）、`resolved_at`、`created_at`。

---

### Redispatch（重调度）完整使用指南

#### 功能定义

`redispatch` 是**全链路重规划**操作。当遇到节点异常（容量不足、维修关停、存储时长超限）或车辆异常时，对原调度方案重新执行 F007→F021→F005→F006 完整调度链路。新旧方案通过**版本链**关联，原方案完整保留便于对比。

#### 前置条件

| 条件 | 说明 | 如何满足 |
|------|------|---------|
| **全局调度已完成** | 必须存在 `related_schedule_code` 对应的 `GlobalSchedule` 记录 | `POST /api/schedule/global` 执行成功 |
| 节点调度 **不要求** 完成 | `redispatch` 内部自行调用 `DispatchService` 执行 F005+F006，无需事先完成节点调度 | — |
| 订单/货物/包裹处于调度链路中 | `related_schedule_code` 关联的订单应处于 `delivering` 或 `exception` 状态 | 全局调度后订单自动为 `delivering` |

> **关键设计**：`redispatch` 只需完成阶段3（全局调度）即可使用。`ReplanService.redispatch()` 内部按顺序调用 `ScheduleService`（F007+F021）→ `DispatchService`（F005+F006），**不需要预先执行节点间调度**。创建异常事件时仅自动将关联实体的状态标记为 `exception`，作为重调度时的筛选条件。

#### 适用场景

| 异常类型 | exception_subtype | 触发条件 | target_type |
|---------|-------------------|---------|-------------|
| `node` | `capacity_limit` | 分拣中心容量不足，部分货物需重新分配 L1 | `node` |
| `node` | `storage_timeout` | 存储中心货物积压超时 | `node` |
| `node` | `node_maintenance` | 节点维修关停 | `node` |
| `vehicle` | `vehicle_breakdown` | 车辆故障无法完成任务 | `vehicle` |
| ~~`package`~~ | ~~`package_damage`~~ | ~~包裹损坏需整体重新调度~~ | ~~`package`~~ (暂未实现) |

#### 响应格式

**创建异常事件** `POST /api/exceptions`：

```json
// 请求体
{
  "exception_type": "node",
  "exception_subtype": "capacity_limit",
  "target_type": "node",
  "target_code": "L1001",
  "recommended_action": "redispatch",
  "related_schedule_code": "GS20260622001",
  "description": "L1001 容量不足，部分货物需重新分配 L1 节点"
}
// 成功响应 (code=0)，data 中包含新创建的异常事件详情
```

> **触发时自动状态变更**：创建异常事件后，系统自动将 `related_schedule_code` 关联的：
> - 订单状态：`delivering` → `exception`
> - 货物状态：`packed` / `in_transit` → `exception`
> - 包裹状态：`packed` / `in_transit` / `pending_pack` → `exception`
> - 若 `target_type=vehicle`：车辆状态 → `disabled`，且按 `dispatch_id` 批量更新关联包裹和货物

**触发重规划** `POST /api/exceptions/{event_code}/replan`：

```json
// 请求体
{
  "action": "redispatch",
  "reason": "L1001 容量溢出 120%，分流 3 票货物至 L1002"
}
// 成功响应 (code=0)
{
  "code": 0,
  "message": "success",
  "data": {
    "schedule_code": "GS20260622002",
    "new_schedule_code": "GS20260622002",
    "batch_code": "BATCH20260622002",
    "version": 2,
    "is_replan": true,
    "replan_reason": "L1001 容量溢出 120%，分流 3 票货物至 L1002",
    "original_schedule_code": "GS20260622001"
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

#### 完整调用顺序（6 步）

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1  创建异常事件                                                 │
│         POST /api/exceptions                                        │
│         入参: exception_type=node, recommended_action=redispatch     │
│         出参: event_code="EX..."                                     │
│         副作用: 订单/货物/包裹 → exception，车辆 → disabled           │
├─────────────────────────────────────────────────────────────────────┤
│ Step 2  [可选] 查询异常确认                                          │
│         GET /api/exceptions/{event_code}                            │
│         确认 status=open, recommended_action=redispatch              │
├─────────────────────────────────────────────────────────────────────┤
│ Step 3  触发重规划                                                   │
│         POST /api/exceptions/{event_code}/replan                    │
│         入参: { action: "redispatch", reason: "..." }                │
│         ReplanService.redispatch() 内部调用链:                       │
│           a) 读原调度方案 (GlobalSchedule)                           │
│           b) 获取 order_codes + algorithm_type                      │
│           c) 提取 excluded_nodes（来自 event.target_code）            │
│           d) 调用 ScheduleService.create_global_schedule()           │
│              → F007 全局调度 + F021 打包（仅对 exception 订单）       │
│           e) 更新新方案版本链: version+1, parent_id, is_replan        │
│           f) 调用 DispatchService.create_node_dispatch()             │
│              → F005 节点调度 (demo_mode=false, 仅调度 exception 包裹) │
│              → F006 路径规划自动触发                                 │
│         出参: new_schedule_code, batch_code, version                 │
├─────────────────────────────────────────────────────────────────────┤
│ Step 4  [可选] 验证新方案                                            │
│         GET /api/schedule/global/{new_schedule_code}                │
│         对比新旧方案的 goods_schedules + packages 差异               │
├─────────────────────────────────────────────────────────────────────┤
│ Step 5  标记异常已解决                                               │
│         PUT /api/exceptions/{event_code}/resolve                    │
│         副作用: status → resolved, resolved_at = now()               │
├─────────────────────────────────────────────────────────────────────┤
│ Step 6  [可选] 模拟送达验证                                          │
│         POST /api/simulation/deliver (分批送达)                      │
│         或直接调用 demo_mode=true 自动化流程                         │
└─────────────────────────────────────────────────────────────────────┘
```

#### 版本链机制

重规划生成的每条新记录（`GlobalSchedule`、`DispatchBatch`、`NodeDispatch`、`Route`）均通过以下字段形成版本链：

| 字段 | 说明 | 示例 |
|------|------|------|
| `version` | 版本号，原方案=1，每次重规划+1 | `2` |
| `parent_id` | 指向前一版本的数据库 `id` | `1` |
| `is_replan` | 标记为重规划记录 | `true` |
| `replan_reason` | 重规划原因（人工填写） | `"L1001 容量溢出"` |

> **对比查询**：通过 `parent_id` 可追溯完整版本链，前端可展示"原方案 vs 新方案"对比视图。

---

### Reroute（重路径规划）完整使用指南

#### 功能定义

`reroute` 是**轻量级重规划**操作。当遇到道路异常（拥堵、封闭）或单条路径需调整时，仅重新执行 F006 路径规划，**不重新调度**。操作粒度精确到单条路线，影响范围最小。

#### 前置条件

| 条件 | 说明 | 如何满足 |
|------|------|---------|
| **节点调度已完成** | `target_code` 必须指向一条已存在的 `Route` 记录，Route 由 F005 完成后自动触发 F006 生成 | `POST /api/schedule/node-dispatch` 执行成功（F005 完成后自动执行 F006） |
| 目标路线存在 | `target_type=route` + `target_code` 对应的 Route 记录必须存在于 `routes` 表 | 可通过 `GET /api/routes` 确认 |
| 关联调度方案存在 | `related_schedule_code` 对应的 `GlobalSchedule` 记录必须存在 | `POST /api/schedule/global` 执行成功 |

> **关键设计**：`reroute` 需要完成阶段4（节点间调度），因为其操作对象是 F006 生成的 `Route` 记录。若仅完成全局调度（阶段3）而未执行节点调度（阶段4），则 `routes` 表中没有记录，无法触发 `reroute`。`reroute` 不修改订单/货物/包裹状态（与 `redispatch` 不同），仅生成新路线记录。

#### 适用场景

| 异常类型 | exception_subtype | 触发条件 | target_type |
|---------|-------------------|---------|-------------|
| `road` | `road_closed` | 道路封闭，需绕行 | `route` |
| `road` | `congestion` | 严重拥堵，需重新规划路径 | `route` |
| `road` | `road_accident` | 交通事故导致路段不可用 | `route` |

#### 响应格式

**创建异常事件** `POST /api/exceptions`：

```json
// 请求体（注意 reroute 强制要求 target_type="route", target_code 必填）
{
  "exception_type": "road",
  "exception_subtype": "road_closed",
  "target_type": "route",
  "target_code": "RT202606220001",
  "recommended_action": "reroute",
  "related_schedule_code": "GS20260622001",
  "description": "L1001→L2034 路段施工封闭，需重新规划路线"
}
// 成功响应 (code=0)
```

**触发重规划** `POST /api/exceptions/{event_code}/replan`：

```json
// 请求体
{
  "action": "reroute",
  "reason": "原路线途经封闭路段，绕行替代路径"
}
// 成功响应 (code=0)
{
  "code": 0,
  "message": "success",
  "data": {
    "batch_code": "BATCH20260622001",
    "route_codes": ["RT202606220002"],
    "new_route_code": "RT202606220002",
    "version": 2,
    "is_replan": true,
    "replan_reason": "原路线途经封闭路段，绕行替代路径",
    "original_route_code": "RT202606220001"
  },
  "meta": { "degraded": false, "degraded_reason": null }
}
```

#### 完整调用顺序（6 步）

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1  创建异常事件                                                 │
│         POST /api/exceptions                                        │
│         入参: exception_type=road, recommended_action=reroute        │
│         入参: target_type=route, target_code="RT..." (必填!)         │
│         出参: event_code="EX..."                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Step 2  [可选] 查询异常确认                                          │
│         GET /api/exceptions/{event_code}                            │
│         确认 status=open, target_type=route, target_code 有效         │
├─────────────────────────────────────────────────────────────────────┤
│ Step 3  触发重规划                                                   │
│         POST /api/exceptions/{event_code}/replan                    │
│         入参: { action: "reroute", reason: "..." }                   │
│         ExceptionService.trigger_replan() 内部调用链:                 │
│           a) 通过 event.target_code 查找原 Route                     │
│           b) 通过 Route.dispatch_id → NodeDispatch                   │
│           c) 通过 NodeDispatch.dispatch_batch_id → DispatchBatch      │
│           d) 提取 excluded_vehicles（原车辆排除，避免重复分配）        │
│           e) 调用 ReplanService.reroute():                           │
│              → 读取原 Route + 关联 dispatch + batch                  │
│              → 调用 RouteService.create_route_planning()             │
│              → F006 仅为该 dispatch_code 重新规划路径                 │
│              → 更新新 Route 版本链                                   │
│         出参: route_codes, batch_code, version                      │
├─────────────────────────────────────────────────────────────────────┤
│ Step 4  [可选] 对比新旧路线                                          │
│         GET /api/routes/{new_route_code}                            │
│         GET /api/routes/by-vehicle/{vehicle_code}/coordinates        │
│         前端可并排展示新旧路线坐标轨迹                                │
├─────────────────────────────────────────────────────────────────────┤
│ Step 5  标记异常已解决                                               │
│         PUT /api/exceptions/{event_code}/resolve                    │
│         副作用: status → resolved, resolved_at = now()               │
├─────────────────────────────────────────────────────────────────────┤
│ Step 6  [可选] 继续配送                                              │
│         使用新路线继续模拟送达 → POST /api/simulation/deliver         │
└─────────────────────────────────────────────────────────────────────┘
```

#### 与 Redispatch 的关键差异

| 对比维度 | Redispatch | Reroute |
|---------|-----------|---------|
| **前置条件** | 仅需全局调度完成（`schedule_code` 存在） | 需节点调度完成（`Route` 记录存在） |
| **重新调度** | ✅ 全链路 F007→F021→F005→F006 | ❌ 仅 F006 |
| **影响范围** | 整个调度方案（可能跨节点） | 单条路线（单次运输） |
| **版本链对象** | GlobalSchedule + DispatchBatch + NodeDispatch + Route | Route |
| **状态重置** | 订单/货物/包裹 → exception | 不修改状态 |
| **排除参数** | excluded_nodes（跳过故障节点） | excluded_vehicles（跳过故障车辆） |
| **执行耗时** | 较长（≈全调度时间） | 较短（单次路径规划） |

---

#### AI 助手（阶段 8）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/ai/parse` | 自然语言解析 → 调度执行（F014，P0 核心） | Bearer Token |
| `POST` | `/api/ai/explain` | 方案解释（F015，P1 占位 501） | Bearer Token |
| `POST` | `/api/ai/review` | 方案审查（F016，P1 占位 501） | Bearer Token |
| `POST` | `/api/ai/analyze-exception` | 异常分析（F017，P1 占位 501） | Bearer Token |

##### POST /api/ai/parse — 三步模型

**步骤1** — 确定参数来源（4 种模式）：

| 条件 | 模式 | 说明 |
|------|------|------|
| 有 `message`，无 `weights` | `ai` | DeepSeek 解析自然语言 → 算法参数 |
| 无 `message`，有 `weights` | `manual` | 直接使用手动权重，不调 DeepSeek |
| 有 `message`，有 `weights` | `hybrid` | DeepSeek 解析后用 `weights` 覆盖部分参数 |
| 无 `message`，无 `weights` | `default` | 使用 `algorithm_config.json` 默认值 |

**步骤2** — 确定执行目标：

| `schedule_codes` | 模式 | 说明 |
|:-:|------|------|
| 空 | 新建调度 | 对全部 `pending` 订单执行 F007→F021→F005→F006 |
| 非空 | 版本化重规划 | 逐条对指定方案生成新版本（走 `ReplanService.redispatch()`） |

**步骤3** — `execute` 控制：

| `execute` | 说明 |
|:-:|------|
| `true`（默认） | 完整执行调度链路并写库 |
| `false` | dry-run：仅返回解析参数，不写库 |

**请求体** (`AiParseRequest`)：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | 否 | 自然语言指令 |
| `weights` | object | 否 | 手动权重（结构与 `algorithm_config.json` 一致） |
| `schedule_codes` | string[] | 否 | 目标方案编号列表（非空=重规划） |
| `execute` | boolean | 否 | 是否执行调度链路（默认 `true`） |

**请求示例**：

```json
// ① AI 重规划（最常用）
{"message": "优先缩短距离，多用电车", "schedule_codes": ["GS20260623001"]}

// ② AI 新建调度
{"message": "优先时效，减少总时间"}

// ③ dry-run 预览
{"message": "缩短距离，减少碳排放", "execute": false}

// ④ 纯手动权重
{"weights": {"global_schedule": {"weights": {"distance": 0.9, "time": 0.05, "package_count": 0.05}}}, "schedule_codes": ["GS20260623001"]}

// ⑤ 默认参数（无 message 无 weights）
{"schedule_codes": ["GS20260623001"]}
```

**响应格式**：

```json
// dry-run 成功
{
  "code": 0, "message": "success (dry-run)",
  "data": {
    "algorithm_params": {"global_schedule": {...}, "node_dispatch": {...}, "route_planning": {...}},
    "mode": "ai",
    "is_replan": false,
    "executed": false,
    "reference_codes": null
  },
  "meta": {"degraded": false, "degraded_reason": null}
}

// AI 重规划成功
{
  "code": 0, "message": "success",
  "data": {
    "schedule_code": "GS20260623010",
    "algorithm_params": {...},
    "mode": "ai",
    "is_replan": true,
    "status": "draft",
    "reference_codes": ["GS20260623008"]
  },
  "meta": {"degraded": false, "degraded_reason": null}
}

// DeepSeek 降级
{
  "code": 0, "message": "success",
  "data": {"schedule_code": "GS20260623012", "mode": "ai", ...},
  "meta": {"degraded": true, "degraded_reason": "DeepSeek API 调用超时（30秒）"}
}
```

**DeepSeek 降级策略**：

| 失败场景 | 处理方式 | `degraded` |
|---------|---------|:-:|
| API Key 未配置 | 使用默认算法参数完成调度 | `true` |
| 网络超时（30s） | fallback 默认参数 | `true` |
| HTTP 错误（4xx/5xx） | fallback 默认参数 | `true` |
| 返回格式无法解析 | fallback 默认参数 | `true` |
| 调用成功 | 使用 DeepSeek 返回参数 | `false` |

> ⚠️ **关键原则**：DeepSeek 调用失败时使用默认参数完成调度，绝不伪造 AI 成功结果。前端需在 `meta.degraded === true` 时提示用户当前使用了默认参数。

**错误码**：

| code | HTTP | 说明 |
|------|------|------|
| 0 | 200 | 成功 |
| 40000 | 400 | 参数校验失败 |
| 40001 | 200 | 全局调度/节点调度/路径规划业务失败 |
| 40300 | 403 | 无权限（manager 角色） |
| 50000 | 500 | 服务器内部错误 |

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
| `40002` | 200 | 已有活跃方案，不允许重复调度（P1-2 新增） |
| `40003` | 200 | 订单状态已变化，请重新预览（P1-2 新增） |
| `40100` | 200 | 用户名或密码错误（登录接口） |
| `40100` | 401 | 未登录或 Token 无效 |
| `40101` | 401 | Token 已过期，请重新登录 |
| `40300` | 403 | 无权限执行此操作 |
| `40400` | 404 | 资源不存在 |
| `40401` | 200 | 调度方案不存在 |
| `50000` | 500 | 服务器内部错误 |
| `50001` | 200 | 确认失败，draft 已丢弃，请重新预览（P1-2 新增） |

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

### 阶段 7 设计决策

1. **方案A — 不修改现有服务层**：`ReplanService` 直接调用 `ScheduleService`、`DispatchService`、`RouteService`，版本链逻辑完全在 `ReplanService` 中实现。原服务层代码零修改，确保回归安全。
2. **重规划仅调度 exception 状态实体**：`is_replan=True` 标记传入各服务层，仅对 `exception` 状态的订单/包裹进行调度，正常配送中的实体不受影响。
3. **reroute 不修改状态**：与 redispatch 不同，reroute 不重置订单/货物/包裹为 exception，仅生成新路线记录。原路线保留用于对比。
4. **repack_at_l1 精确匹配修复**：修复 `.first()` 改为 `.all()` + `order_code` 精确匹配，解决多订单同路线场景下包裹错误复用导致遗漏的 BUG。

### P1-2 设计决策

1. **两步流替代直接落库**：P1-2 移除 `POST /api/schedule/global` 的直接落库模式，改为 preview（仅 F007，draft）→ confirm（F021 打包 + 状态更新，active）。用户在确认前可丢弃 draft 方案。
2. **active 方案唯一性**：同一批订单在同一时间仅允许一个 active 方案，防止调度冲突。重规划（is_replan=True）跳过此检查。
3. **confirm 原子性**：confirm 中的 F021 打包 + 订单/货物状态更新在单事务中执行。若失败，draft 方案自动删除，用户需重新 preview。
4. **状态校验机制**：confirm 时校验订单状态是否仍为 pending/exception（重规划时允许 delivering），状态已变化则拒绝确认并返回 40003。
5. **draft 物理删除**：丢弃 draft 时直接物理删除记录（不软删除），避免垃圾数据累积。删除成功后仅返回瞬态 `status: "discarded"` 告知前端。

### 阶段 8 设计决策

1. **三步模型解耦**：`_resolve_params`（参数来源）→ 执行目标判定（新建/重规划）→ `_execute_*`（调度链路），三层独立可测。
2. **AI 重规划走 ReplanService**：AI 驱动的重规划复用 `ReplanService.redispatch()`，与异常驱动的重规划共享版本链逻辑。差异：AI 重规划不传 `event` 参数 → 自动重置货物状态为 `pending_pack` → `demo_mode=true` 完成全链路。
3. **hybrid 模式权重合并**：DeepSeek 参数作为基础，手动 `weights` 覆盖匹配的 section 字段，支持部分覆盖。
4. **系统上下文最小化**：DeepSeek 提示词注入待分配订单数 + 可用车辆数 + 历史方案指标（距离/时间/货物数/评分），不泄露车辆编号等敏感细节。
5. **所有参数模式统一接口**：单一 `POST /api/ai/parse` 支持 AI/手动/混合/默认 四种参数来源 × 新建/重规划 两种执行目标 × 执行/dry-run 两种 write 模式，前端无需多接口调用。

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
| F005 算法 | 车辆不足错误、包裹状态错误、无可调度包裹错误 | ✅ |
| F005 算法 | demo_mode=true 一次调用完成 L0→L2 全链路（含自动模拟送达 + 重新打包） | ✅ |
| F005 算法 | demo_mode=false 代码框架预留（智能检测4种场景），阶段6完整验证 | ⚠️ 框架已就绪 |
| F005 算法 | 智能检测调用阶段（通过 `_check_packages_by_level()` + 批次状态） | ✅ |
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

### 阶段 5 自测（路径规划 F006）

测试时间：2026-06-14，更新：2026-06-18，结果：**35/35 通过（100%）**

### 阶段 6 自测（模拟送达 F013-1）

测试时间：2026-06-18，结果：**7/7 通过（100%）**

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 模拟送达 | test_deliver_by_vehicle_success：按车辆送达 | ✅ |
| 模拟送达 | test_deliver_by_package_success：按包裹送达 | ✅ |
| 模拟送达 | test_deliver_all_success：全部送达 | ✅ |
| 模拟送达 | test_deliver_no_packages_in_transit：无可送达包裹 | ✅ |
| 模拟送达 | test_deliver_package_not_in_transit：包裹状态错误 | ✅ |
| 模拟送达 | test_deliver_vehicle_not_busy：车辆状态无效 | ✅ |
| 模拟送达 | test_deliver_nonexistent_vehicle：不存在的车辆 | ✅ |

#### 算法层测试 (12/12)

| 类别 | 测试项 | 结果 |
|------|--------|------|
| Haversine 距离 | 同一坐标距离为0、不同坐标距离正确、长距离计算 | ✅ |
| 路线编码生成 | 第一个编码格式正确、多个编码序号递增 | ✅ |
| 路径规划算法 | L0→L1 路径规划成功、L1→L2 路径规划成功 | ✅ |
| 路径规划算法 | 返程路径生成、空任务列表错误、节点不存在错误 | ✅ |
| 路径规划算法 | 车辆不存在错误、距离和时间计算正确 | ✅ |

#### 服务层测试 (13/13)

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 创建路径规划 | 成功创建、批次不存在错误、无调度明细错误 | ✅ |
| 查询路线 | 查询路线列表、分页、筛选（车辆编码/调度编码） | ✅ |
| 查询详情 | 查询路线详情、路线不存在错误 | ✅ |
| 查询坐标 | 查询车辆路线坐标、路线不存在错误、车辆不存在错误 | ✅ |

#### 集成测试 (2/2)

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 完整调度链路 | demo_mode=true 完整流程 F007→F021→F005→F006 | ✅ |
| 完整调度链路 | 分步执行完整流程 F007→F021→F005→F006 | ✅ |

#### 自测验收清单

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

### 阶段 7 自测（异常与重规划）

测试时间：2026-06-22，结果：**32/32 通过（100%）**

#### 异常服务单元测试 (19/19)

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 创建异常 | 道路异常创建成功、包裹异常创建成功、节点异常创建成功 | ✅ |
| 创建异常 | 缺少必填字段报错、无效异常类型报错、无效 action 报错 | ✅ |
| 创建异常 | reroute 必须 target_type=route、必须提供 target_code | ✅ |
| 创建异常 | redispatch 建议 target_type=node/vehicle/package | ✅ |
| 创建异常 | 关联订单/货物/包裹状态 → exception、车辆异常 → disabled | ✅ |
| 查询异常 | 列表查询（分页）、按 status/exception_type 筛选 | ✅ |
| 查询异常 | 详情查询、不存在异常报错 | ✅ |
| 更新异常 | 更新 status → resolved（自动 recorded_at）、不存在报错 | ✅ |
| 标记解决 | 正常标记、重复标记报错 | ✅ |

#### 重规划集成测试

| 类别 | 测试项 | 结果 |
|------|--------|------|
| Redispatch | 节点异常触发完整重调度（F007→F021→F005→F006） | ✅ |
| Redispatch | excluded_nodes 正确排除故障节点 | ✅ |
| Redispatch | 新版调度方案版本链正确（version+1, parent_id, is_replan） | ✅ |
| Redispatch | 原调度方案完整保留不受影响 | ✅ |
| Reroute | 道路异常触发仅 F006 路径重规划 | ✅ |
| Reroute | excluded_vehicles 正确排除故障车辆 | ✅ |
| Reroute | 新路线版本链正确 | ✅ |
| Reroute | repack_at_l1 多订单同路线精确匹配（修复 BUG） | ✅ |
| 异常管理 | 已解决异常再次触发重规划拒绝 | ✅ |
| 异常管理 | 不存在异常触发重规划报错 | ✅ |
| 异常管理 | 缺失 related_schedule_code 触发 redispatch 报错 | ✅ |
| 异常管理 | missing route target_code 触发 reroute 报错 | ✅ |

#### 自测验收清单

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 异常事件 CRUD | POST 创建、GET 列表/详情、PUT 更新、PUT /resolve 标记解决 | ✅ |
| 文件不修改原则 | schedule_service.py、dispatch_service.py、route_service.py 未修改 | ✅ |
| 版本链 | 重规划后的记录 version+1、parent_id 正确、is_replan=true | ✅ |
| Redispatch | 完整调用链：创建异常 → 触发重规划 → 验证方案 → 标记解决 | ✅ |
| Reroute | 完整调用链：创建异常 → 触发重规划 → 对比路线 → 标记解决 | ✅ |
| 错误处理 | 无效 action → 400、不存在异常 → 40401、已解决再触发 → 40001 | ✅ |
| 权限 | dispatcher 可触发重规划、manager 返回 403 | ✅ |
| 数据完整性 | exception_events 表所有字段正常写入、状态流转正确 | ✅ |

### 阶段 8 自测（AI 助手与收尾 F014）

测试时间：2026-06-23，结果：**全部通过**

#### AI 解析与调度测试

| # | 场景 | 模式 | 耗时 | degraded | 全链路 | 结果 |
|---|------|------|------|----------|--------|------|
| T1 | dry-run（仅 AI 解析参数） | ai | 7.1s | ❌ false | N/A | ✅ |
| T2 | AI 重规划 `GS20260623008` | ai+replan | 28.2s | ❌ false | ✅ | ✅ |
| T3 | 手动权重重规划 `GS20260623001` | manual+replan | 2.3s | ❌ false | ✅ | ✅ |

#### T2 全链路验证（AI 重规划）

| 步骤 | 数据 | 状态 |
|------|------|------|
| F007 全局调度 | `GS20260623010` v2 (parent=GS20260623008) | ✅ |
| F021 打包 | `PKG202606230015` (L0→L1), `PKG202606230016` (L1→L2) | ✅ |
| F005 节点调度 | `BATCH20260623005` completed, L0→L1=1, L1→L2=1 | ✅ |
| F005 派车 | `DISP20260623007` (phase=0), `DISP20260623008` (phase=1) | ✅ |
| F006 路径规划 | `ROUTE20260623003` (22.15km), `ROUTE20260623004` (25.49km) | ✅ |

#### 自测验收清单

| 类别 | 测试项 | 结果 |
|------|--------|------|
| AI 解析 | DeepSeek 自然语言 → 算法参数 JSON（含上下文注入） | ✅ |
| AI 重规划 | 自然语言驱动版本化重规划（F007→F021→F005→F006） | ✅ |
| 手动权重 | 纯手动参数（不走 DeepSeek）正确调度 | ✅ |
| dry-run | `execute=false` 仅返回参数不写库 | ✅ |
| DeepSeek 埋点 | 每次调用记录到 `log_events` | ✅ |
| DeepSeek 降级 | API 失败 → fallback 默认参数 → `meta.degraded=true` | ✅ |
| 批量重规划 | `schedule_codes` 多条逐条生成新版本 | ✅ |
| P1 占位 | `/explain`、`/review`、`/analyze-exception` 返回 501 | ✅ |
| 权限 | dispatcher 可调用、manager 返回 403 | ✅ |
| 版本链 | 重规划后 version+1、parent_id 正确、is_replan=true | ✅ |

### P1-2 自测（预览/确认模式）

测试时间：2026-06-24，结果：**298/298 通过（100%）**

#### 新增功能测试

| 类别 | 测试项 | 结果 |
|------|--------|------|
| 预览模式 | preview=True 生成 draft，订单状态不变，package_count=0 | ✅ |
| 确认流程 | confirm 后 status→active，订单→delivering，包裹生成 | ✅ |
| 拒绝确认 | 订单状态已变化 confirm 返回 40003，draft 被删除 | ✅ |
| 异常回滚 | confirm 异常时 draft 被删除，返回 50001 | ✅ |
| 丢弃 draft | DELETE draft 成功删除，active 方案拒绝 | ✅ |
| 重复预览 | 同批订单已有 active 方案时返回 40002 | ✅ |
| 列表过滤 | 默认不返回 draft，?status=draft 可查预览方案 | ✅ |
| 重规划兼容 | is_replan 跳过 active 检查，confirm 允许 delivering 状态 | ✅ |

#### 回归验证

| 类别 | 测试数 | 结果 |
|------|--------|------|
| 阶段 1-8 全部测试 | 298 | ✅ 100% 通过 |
| P1-1 优化测试 | 包含 | ✅ 无回归 |
| P1-2 新增用例 | 包含 | ✅ 全部通过 |

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
- [阶段 5 API 契约文档](../../docs/api-contract/api-contract-phase5.md)（V1.0）
- [阶段 7 开发文档](../../My_doc/阶段7开发文档.md)（V3.0）
- [阶段 7 API 契约文档](../../docs/api-contract/api-contract-phase7.md)（V1.0）
- [阶段 8 API 契约文档](../../docs/api-contract/api-contract-phase8.md)（V1.0）
- [P1-2 API 契约文档](../../docs/api-contract/api-contract-p1-2.md)（V1.0）

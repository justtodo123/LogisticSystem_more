# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

> **注意**：`.gitignore` 第 21 行默认忽略了 `CODEBUDDY.md`。如需提交此文件到 Git，请从 `.gitignore` 中移除对应条目。

## 项目概述

"DeepSeek 路径优化 - 智能物流平台"是华中科技大学软件学院 2026 年 6 月教学实训项目，2 人团队、4 周开发周期。构建三级物流网络调度演示系统，核心闭环：订单 → 全局调度(F007) → 打包(F021) → 节点间调度(F005) → 路径规划(F006) → 路线可视化(F010)。当前处于 **MVP 阶段 0（工程初始化）**，代码尚未开始编写。

## 常用命令

```bash
# 后端 (Python 3.11 + FastAPI)
cd backend
uvicorn main:app --reload --port 8000         # 启动后端开发服务器

# 前端 (Vue 3 + TypeScript + Vite)
cd frontend
npm install                                    # 安装依赖
npm run dev                                    # 启动前端开发服务器 (:5173)

# 数据库迁移
cd backend
alembic upgrade head                           # 执行迁移到最新版本

# 演示数据初始化（首次启动后执行）
cd backend
python scripts/init_demo_data.py               # 生成虚拟城市演示数据
```

所有命令均为计划中的命令（项目尚未编码），具体以实际 `package.json` 和项目配置为准。前端 Vite 开发服务器通过代理将 `/api` 请求转发至后端 `localhost:8000`。

## 架构概览

### 核心原则

- **单体优先**：一个 FastAPI 进程承载 API + 算法 + DeepSeek 代理，不拆分微服务。
- **离线可演示**：路径规划默认 Haversine + 2-opt，使用虚拟城市坐标（中心 30.5°N, 114.3°E），不依赖任何地图 API。
- **API 契约先行**：每个开发阶段开始前，后端先输出 OpenAPI 规范；前端可用 Mock 数据并行开发。
- **双标识策略**：数据库内部使用自增 `id` 做外键关联；API 层统一暴露 `*_code` 业务编号（如 `order_code`、`schedule_code`）。
- **可演示优先**：约束满足优于最优解；DeepSeek 失败时降级为默认算法参数并明确告知用户，不伪造 AI 成功。
- **4 周范围控制**：仅实现 P0 功能；P1 保留接口占位（返回 501），P2 不实现。

### 技术栈（不可随意替换）

| 层 | 技术 | 备注 |
| --- | --- | --- |
| 前端 | Vue 3.4+ + TypeScript 5.x + Vite 5.x | Element Plus 2.x 组件库、Pinia 2.x 状态管理、Axios |
| 后端 | Python 3.11 + FastAPI 0.110+ | Uvicorn ASGI 服务器 |
| ORM | SQLAlchemy 2.0+ | Pydantic v2 数据校验、Alembic 迁移 |
| 数据库 | SQLite（开发） / MySQL 8.0（可选生产） | 零配置，单文件 `backend/data/logistics.db` |
| 算法 | NumPy + 自研 Haversine + 自研 2-opt | P0 纯传统算法，P1 预留 PyTorch |
| AI 编排 | DeepSeek API（OpenAI 兼容接口） | API Key 仅存后端 `.env`，日志脱敏 |
| 认证 | PyJWT + passlib[bcrypt] | JWT 24h 过期，RBAC 角色权限 |
| 可视化 | SVG + Canvas 混合 | P0 用 SVG 静态图，P1 预留 Canvas 动画 |

### 项目目录结构（计划）

```
LogisticsSystem/
├── frontend/                 # Vue 3 + Vite + TypeScript
│   └── src/
│       ├── api/              # Axios 封装，统一 Token 注入与错误拦截
│       ├── views/            # 页面组件（调度工作台、基础数据管理等）
│       ├── components/       # 通用组件 + SVG 路线可视化组件
│       ├── stores/           # Pinia 状态（用户会话、调度方案等）
│       └── router/           # Vue Router + 角色路由守卫
├── backend/
│   ├── main.py               # FastAPI 应用入口，注册路由与中间件
│   ├── api/                  # 路由层（auth、base、schedule、routes、exceptions、simulation、ai）
│   ├── services/             # 业务逻辑层（调度编排、DeepSeek 代理、模拟送达等）
│   ├── algorithms/           # 算法引擎 F007/F005/F006/F021
│   ├── models/               # SQLAlchemy ORM 模型（15 张表）
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── config/               # database.py、algorithm_config.json
│   ├── scripts/              # init_demo_data.py 演示数据初始化
│   └── data/                 # logistics.db、archive/
└── docs/
    ├── prds/                 # 产品需求文档
    ├── architecture/         # 系统架构设计说明书
    └── develop_plan/         # MVP 开发计划（被 .gitignore 忽略）
```

### 分层架构与请求流转

前端 Vue 3 SPA 通过 Axios 发送 HTTP 请求 → Vite 开发代理转发 `/api` 到后端 8000 端口 → FastAPI 路由层先经过 JWT 认证中间件和 RBAC 权限依赖 → 路由分发到对应服务层 → 服务层调用算法引擎或 ORM → 结果通过统一 JSON 响应格式返回。

```
UI → Axios → Vite Proxy → FastAPI Router → Auth Middleware → RBAC Guard → Service → Algorithm/ORM → SQLite
```

### 15 张 MVP 表

系统表：`users`（预置 dispatcher/manager 账号，bcrypt 哈希密码）
基础数据：`nodes`、`storage_centers`、`sorting_centers`、`orders`、`goods`、`packages`、`vehicles`、`drivers`
调度结果：`global_schedules`（F007 输出）、`dispatch_batches`（F005 批次聚合）、`node_dispatches`（单车调度明细）、`routes`（F006 路径规划）
异常与日志：`exception_events`、`log_events`

每张业务表同时有内部 `id`（BIGINT 自增 PK）和外部 `*_code`（VARCHAR UNIQUE）。调度结果表（global_schedules、dispatch_batches、node_dispatches、routes）均含版本链字段：`version`、`parent_id`（自关联）、`replan_reason`、`is_replan`。

### 核心调度链路（串行依赖）

这是整个系统最关键的业务流程，必须严格按顺序执行：

```
POST /api/schedule/global
  → F007 全局调度（规则评分 + 启发式，为每票货物规划 L0→L1→L2 路径）
  → 写入 global_schedules
  → F021 打包（L0→L1 按 from/to 节点对合并；L1→L2 按同订单合并）
  → 写入 packages
  → 返回 schedule_code

POST /api/schedule/node-dispatch {schedule_code, demo_mode}
  → F005 第一次调用（层级 L0→L1，查询已打包包裹，分配车辆与空闲司机）
  → 写入 dispatch_batches + node_dispatches（level_phase=0）
  → 若失败则终止，不执行第二次
  → F005 第二次调用（层级 L1→L2，仅在 demo_mode=true 或模拟送达完成后可执行）
  → 写入 node_dispatches（level_phase=1）
  → F006 为每辆车规划路径（Haversine + 2-opt）
  → 写入 routes（route_segments JSON）
  → 返回 batch_code
```

关键约束：
- F005 第一次失败则整个批次失败，不执行第二次。
- `demo_mode=true` 跳过 L1 实际送达等待，允许连续执行两次 F005（课堂演示用）。
- 模拟送达 API `POST /api/simulation/deliver` 驱动状态流转：L0→L1 送达后货物变"待打包"；L1→L2 送达后货物变"已送达"。
- 司机分配策略：从车辆归属节点选取 `status=idle` 的第一个司机，不做复杂排班。

### 实体状态流转

- **订单**：`pending` → `delivering`（F007 调度完成）→ `completed`（全部货物送达 L2）/ `exception`
- **货物**：`pending_pack` → `packed`（节点打包）→ `in_transit`（F005 分配车辆）→ `pending_pack`（到达 L1 需重新打包）/ `delivered`（到达 L2）
- **包裹**：`pending_pack` → `packed` → `in_transit`（F005 分配）→ `delivered`
- **车辆**：`idle` → `delivering` → `idle`（模拟送达后回写）
- **司机**：`idle` ↔ `busy`

### 异常处理与重规划

异常分为三类，处理方式不同：
- **道路异常 / 包裹异常**：触发 `reroute`，仅重新执行 F006 路径规划。
- **节点异常**（容量/存储时长/维修）：触发 `redispatch`，重新执行 F007 + F005 + F006。

重规划通过 `POST /api/exceptions/{event_code}/replan` 触发，生成新版本记录（version+1，parent_id 指向前一版本，is_replan=true），原方案完整保留可对比。

### DeepSeek 降级策略（Q12 已确认）

`POST /api/ai/parse` 接收自然语言 → DeepSeek 解析为算法参数 JSON → 自动调用调度链路。若 DeepSeek API 调用失败（网络/配额/密钥问题），在统一响应中设置 `meta.degraded=true` 和 `meta.degraded_reason`，使用默认算法参数完成调度。**绝不伪造 AI 成功结果**。

### 统一响应格式

```json
// 成功
{ "code": 0, "message": "success", "data": {...}, "meta": { "degraded": false, "degraded_reason": null } }

// 业务失败 (HTTP 200)
{ "code": 40001, "message": "约束不满足的描述", "data": null }

// 参数错误 (HTTP 400)
{ "code": 40000, "message": "参数校验失败", "data": { "fields": {...} } }

// 认证/授权
40100 未登录, 40101 Token过期, 40300 无权限
```

### 角色权限（RBAC）

| 角色 | 用户名/密码 | GET | POST/PUT/DELETE | P2 运营统计 |
| --- | --- | --- | --- | --- |
| 调度员 | `dispatcher` / `123456` | ✅ | ✅ | ❌ |
| 物流管理者 | `manager` / `123456` | ✅ | ❌ (403) | P2 不实现 |

### 开发阶段推进（8 阶段）

阶段 0→1→2→3→4→5→6→7→8 严格顺序依赖。阶段 3-4-5 是核心主链路，优先保障。每个阶段开始前：后端先定 API 契约，前端 Mock 并行；阶段结束时前后端联调通过再进入下一阶段。

### P1/P2 扩展点（不进入 MVP 实现）

- P1：DQN/MLP+LSTM 模型（`algorithms/ai/` 目录）、高德地图 API（`amap_service.py` 占位）、F015-F017 AI 解释/审查、F009 方案对比、Canvas 轨迹动画
- P2：F018-F020 运营统计看板与报告

P1 相关路由已规划占位，MVP 阶段返回 HTTP 501。

### 演示数据规模

初始化生成：5 个存储中心(L0)、2 个 1 级分拣中心(L1)、50 个 0 级分拣中心(L2)、70 辆车（每节点 10 辆）、70 名司机、15 种货物、50 个订单（每单 2-7 个货物）。虚拟坐标以 (30.500000, 114.300000) 为中心，节点在 ±0.1° 范围内分布。

### 关键约束与非功能需求

- F007/F005/F006 单次调度 ≤ 10 秒返回（算法设迭代上限，超时返回明确错误）
- 前端接口超时提示 10 秒
- 调度结果必须同输入可复现（用于验收）
- 算法权重统一在 `algorithm_config.json` 中配置
- 密码 bcrypt 哈希存储，API Key 仅存后端 `.env`
- `log_events` 保留 30 天自动清理
- 同一输入参数下调度结果可复现（确定性算法，不使用随机种子）

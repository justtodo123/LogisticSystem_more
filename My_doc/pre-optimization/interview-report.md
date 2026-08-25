# DeepSeek 路径优化 - 智能物流平台：面试总说明报告

> 用途：项目答辩、技术面试、代码评审时的统一说明材料。结合 `test-results.md` 使用。

---

**项目名称**：DeepSeek 路径优化 - 智能物流平台  
**类型**：教学实训项目（华中科技大学软件学院 2026 年 6 月）  
**团队**：2 人（1 前端 + 1 后端），4 周开发周期  
**当前状态**：MVP 阶段 0~8 + P1 必做项 + F015（方案解释）已交付  
**报告日期**：2026-08-06  

---

## 目录

1. [系统总览](#1-系统总览)
2. [架构与技术栈](#2-架构与技术栈)
3. [核心业务闭环](#3-核心业务闭环)
4. [数据模型设计](#4-数据模型设计)
5. [技术亮点](#5-技术亮点)
6. [安全设计](#6-安全设计)
7. [测试与质量保障](#7-测试与质量保障)
8. [部署与运行](#8-部署与运行)
9. [系统边界与已知限制](#9-系统边界与已知限制)
10. [高频面试问题](#10-高频面试问题)

---

## 1. 系统总览

本系统是一个**三级物流网络智能调度演示平台**，核心目标为——给定一批订单，自动规划从存储中心(L0) → 一级分拣中心(L1) → 配送节点(L2) 的全链路调度方案，并结合 DeepSeek AI 实现自然语言驱动的智能调参。

**业务价值**：
- 将「人工制定物流排班」升级为「算法自动规划 + AI 辅助调优」
- 支持异常场景（道路阻断、节点容量超限、包裹滞留）的**版本化重规划**，且可回溯对比

---

## 2. 架构与技术栈

### 2.1 总体架构

```
Vue 3 SPA (Element Plus)
  → Axios (baseURL=/api)
    → Vite Proxy
      → FastAPI (:8000)
        → Service Layer (编排)
          → Algorithm Layer (纯函数)
          → SQLAlchemy ORM
            → SQLite
```

**单体优先**：一个 FastAPI 进程承载 API + 算法 + AI 代理，不拆分微服务。

### 2.2 技术栈（全栈自研，无第三方调度平台）

| 层 | 技术 | 说明 |
|---|------|------|
| 前端 | Vue 3.4 + TypeScript 5.x + Vite 5.x | Element Plus 2.x, Pinia, Axios |
| 后端 | Python 3.11 + FastAPI 0.110+ | Uvicorn ASGI 服务器 |
| ORM | SQLAlchemy 2.0 + Alembic | Pydantic v2 数据校验 |
| 数据库 | SQLite（开发） / MySQL 8.0（可选） | 零配置，即开即用 |
| 算法 | NumPy + 自研 Haversine + 自研 2-opt | 确定性算法，可复现 |
| AI | DeepSeek API（OpenAI 兼容） | httpx 异步调用 |
| 认证 | PyJWT + passlib[bcrypt] | JWT 24h + RBAC 角色权限 |

### 2.3 分层设计

- **路由层 `api/`**：参数校验、权限依赖、统一响应 → 调用服务层
- **服务层 `services/`**：业务编排、事务管理、状态机驱动 → 调用算法层 / ORM
- **算法层 `algorithms/`**：纯函数、无副作用、可单测 → 命令式调用，不主动读写 DB
- **模型层 `models/`**：14 张表，双标识策略（库内 `id`，API 暴露 `*_code`）

---

## 3. 核心业务闭环

### 3.1 主链路（串行依赖）

```
订单(pending)
  → F007 全局调度（贪心+评分，为每票货物规划 L0→L1→L2 路径）
    → 写入 global_schedules (status=draft)
  → F021 打包确认（确认方案 → status=active，生成 L0→L1 包裹）
    → 写入 packages
    → 订单状态 pending→delivering
  → F005 节点调度（两次串行：L0→L1，L1→L2）
    → 贪心分配车辆+司机
    → 写入 dispatch_batches + node_dispatches
  → F006 路径规划（为每辆车生成 route_segments）
    → 写入 routes
  → 模拟送达 / 到货确认
    → 状态流转：包裹→delivered，货物/订单→completed
```

> **关键约束**：F005 第一次失败 → 批次直接 failed，不执行第二次。  
> **demo_mode=true**：单次 API 调用完成 L0→L1→L2 全链路（课堂演示用）。

### 3.2 异常处理闭环

```
异常事件创建（道路/包裹/节点）
  → 关联实体自动置 exception
  → 触发重规划：
    ├── reroute（道路/包裹异常）：仅重算 F006
    └── redispatch（节点异常）：完整重算 F007→F021→F005→F006
  → 新版本记录（version+1, parent_id, is_replan=true）
  → 原方案完整保留可对比
```

### 3.3 AI 辅助调度（F014）

自然语言 → DeepSeek 解析为算法参数 JSON → 自动执行调度链路：
- 参数来源：纯 AI / 纯人工 / AI+权重覆盖 / 默认
- 目标：新建调度 / 对已有方案版本化重规划
- 执行模式：dry-run（仅返回参数）/ 真执行
- **降级保证**：API Key 缺失 / 超时 / 解析失败 → 默认算法参数 + `meta.degraded=true`，不伪造 AI 结果

---

## 4. 数据模型设计

### 4.1 核心设计模式

| 设计模式 | 应用场景 |
|----------|----------|
| **双标识策略** | 库内自增 `id` 做外键，API 层暴露 `*_code` 业务编号 |
| **版本链** | 调度类表通过 `version + parent_id + is_replan` 构成自关联链 |
| **JSON 聚合** | `goods_schedules`, `tasks`, `route_segments`, `goods_items` 用 JSON 字段减少关联查询 |
| **节点统一建模** | `nodes` 存公共属性，`storage_centers` / `sorting_centers` 只存扩展字段 |

### 4.2 14 张 MVP 表

| 分类 | 表 |
|------|-----|
| 系统 | `users`, `log_events` |
| 基础数据 | `nodes`, `storage_centers`, `sorting_centers`, `orders`, `goods`, `packages`, `vehicles`, `drivers` |
| 调度结果 | `global_schedules`, `dispatch_batches`, `node_dispatches`, `routes` |
| 异常 | `exception_events` |

---

## 5. 技术亮点

### 5.1 严格的状态机管理

所有状态变更必须通过 `state_machine.py` 的 `transition_*_status()` 函数：
- 非法状态转换 → 立即抛 `ValueError`
- 服务层捕获 → 返回统一错误响应
- `force=True` 保留给数据修复 / 异常重规划场景

**覆盖实体**：Order(4 态), Goods(5 态), Package(5 态), Vehicle(4 态), Driver(2 态), Batch(3 态), Schedule(2 态)

### 5.2 确定性算法 + 可复现验收

- 三大调度算法（F007/F005/F006）不使用随机种子
- Haversine 距离计算、贪心分配、评分公式 = 确定输出
- 同一输入 → 同一输出 → 同一验收结果
- 算法权重集中在 `config/algorithm_config.json`，支持运行时覆盖

### 5.3 DeepSeek AI 降级策略

```
AI 调用失败（网络/配额/密钥/JSON 解析）
  → 返回默认算法参数
  → 设置 meta.degraded = true
  → 前端展示降级提示
  → 绝不伪造 AI 成功结果
```

### 5.4 版本化重规划

- 异常触发重规划时，旧方案完整保留
- 新方案 `version = 旧版本+1, parent_id = 旧id, is_replan = true`
- 方案 A/B 可对比：距离、耗时、包裹数、评分

### 5.5 统一响应格式

所有 API 遵循 `{ code: int, message: str, data: any, meta: {degraded: bool, degraded_reason: str|null} }`：

- `code=0` → 成功
- `code≠0` + HTTP 200 → 业务失败
- HTTP 400/401/403 → 参数/认证/权限错误
- `meta.degraded=true` → AI 降级提示

### 5.6 API 契约先行 + 双标识策略

- 每个阶段开始前先出 OpenAPI 契约 → 前后端平行开发
- 库内自增 `id` 做外键 → 灵活关联
- API 只暴露 `*_code` 业务编号 → 防止 ID 泄漏和顺序猜测

---

## 6. 安全设计

| 安全措施 | 实现方式 |
|----------|----------|
| 密码存储 | bcrypt 哈希，不存储明文 |
| JWT 认证 | HS256 + 24h 过期 |
| RBAC 权限 | dispatcher(读写) / manager(只读)，路由层 `require_role` 依赖 |
| API Key 保护 | 仅存后端 `.env`，不提交 Git（`.gitignore` 规则） |
| 日志脱敏 | 不记录密码、Token 到日志 |
| CORS 配置 | FastAPI CORS middleware，开发期宽松 |
| JWT 弱密钥警告 | `init_db()` 检测到默认 `JWT_SECRET` 时输出 RuntimeWarning |
| 演示账号 | `dispatcher` / `manager` + `123456` —— 仅本地演示，见 README 安全提醒 |

---

## 7. 测试与质量保障

> 详细数据见 `My_doc/test-results.md`。

| 指标 | 数值 |
|------|------|
| 总用例 | 423 |
| 通过 | 421 (99.53%) |
| 测试耗时 | ~76 秒 |
| 测试类型 | unit(算法+服务) / api(接口) / integration(流水线) |

### 测试分布

| 层 | 文件数 | 说明 |
|----|--------|------|
| Unit - Algorithms | 4 | F007 / F005 / F006 / F021 算法独立测试 |
| Unit - Services | 15 | 全部服务层，含 112 项状态机用例 |
| API | 13 | 所有路由端点 + 权限控制 |
| Integration | 6 | 调度流水线 + 重规划回归 + 到货确认全链路 |

### 测试覆盖

- **状态机**：112 项用例全部通过，覆盖所有合法/非法转换
- **调度链路**：F007→F021→F005→F006 端到端验证通过
- **异常重规划**：redispatch / reroute 全链路通过
- **AI 降级**：DeepSeek 各种失败场景的降级行为验证

---

## 8. 部署与运行

### 8.1 一键启动（推荐）

**Windows**：双击 `scripts\start-demo.bat`

自动完成：环境检查 → 依赖安装 → 演示数据初始化 → 后端启动(:8000) → 健康检查 → 前端启动(:5173) → 打开浏览器。

日志输出到 `out-start-demo.md`。

### 8.2 手动启动

```bash
# 后端
cd src/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（另开终端）
cd src/frontend
npm install
npm run dev
```

### 8.3 首次初始化演示数据

```bash
cd src/backend
.venv\Scripts\activate
python -m scripts.init_demo_data
```

生成：5 个存储中心(L0) + 2 个一级分拣中心(L1) + 50 个 0 级分拣中心(L2)、70 辆车、70 名司机、15 种货物、50 个订单。

---

## 9. 系统边界与已知限制

### 9.1 明确不追求的目标（有意识的工程取舍）

| 不追求 | 原因 | 演进方案 |
|--------|------|----------|
| 生产级高并发 | 教学演示系统，SQLite 单写入连接 | 换 MySQL + 连接池 + 多 Uvicorn worker |
| 地图 API 集成 | 离线可演示，依赖虚拟坐标 | P1 预留高德 API 接口占位 |
| 微服务拆分 | 单体优先，阶段 0 即明确 | 按服务边界拆分（当前服务层已解耦） |
| 实时调度引擎 | 演示系统，单次调度 ≤10s 足够 | Celery 任务队列 + WebSocket 推送 |
| P1 深度学习模型 | MVP 纯传统算法 | `algorithms/ai/` 目录已预留 |

### 9.2 已知技术债

| 项 | 影响 | 优先级 |
|----|------|--------|
| Pydantic `config` → `ConfigDict` 迁移 | 警告不阻塞 | P2 |
| FastAPI `on_event` → `lifespan` 迁移 | 警告不阻塞 | P2 |
| `datetime.utcnow()` → `datetime.now(UTC)` | 警告不阻塞 | P2 |
| `model.dict()` → `model_dump()` | 警告不阻塞 | P2 |
| P1-12 权限细化（manager AI限制） | 功能缺失 | P1 |
| P1-13 模拟送达批量增强 | 功能缺失 | P1 |
| F006 2-opt 启用 | 路径可优化 | P1 |
| F016/F017 前端占位按钮 | 用户体验 | P1 |

---

## 10. 高频面试问题

### Q1：为什么选择单体架构而不是微服务？

A：项目定位是教学演示系统，2 人 4 周开发周期。单体架构在此场景下：
- 部署简单（一个进程，一条命令启动）
- 调试方便（单步断点即可追踪全链路）
- 开发效率高（无需 RPC/消息队列协议）

但架构已做良好分层：算法层纯函数、服务层编排、路由层薄接口。未来拆分微服务时，算法可直接独立部署为 Worker，服务层拆分后只要统一响应格式即可。

### Q2：如何保证调度结果的可复现性？

A：三个层面：
1. **确定性算法**：F007/F005/F006 不使用随机种子，贪心策略 + Haversine 距离 = 同输入必同输出
2. **权重可配**：所有算法权重集中在 `algorithm_config.json`，变更可追溯
3. **版本链**：每次重规划生成新版本（version+1, parent_id），原方案完整保留，可逐版本对比

### Q3：DeepSeek AI 是如何集成的？如何防止 AI 瞎编？

A：三重保证：
1. **参数映射**：AI 只输出算法参数（权重、排除节点），不直接输出调度方案
2. **安全过滤**：AI 输出的参数经过 schema 校验 + 取值范围限制 + 业务约束检查
3. **降级兜底**：任何 AI 失败场景自动 fallback 到默认参数 + `meta.degraded=true`，前端必须展示「AI 降级」提示

### Q4：系统的并发处理能力如何？

A：本项目是教学演示系统，明确不做高并发设计。具体来说：
- 数据库使用 SQLite（单写入连接），够 1 人演示
- FastAPI 默认单 Uvicorn worker
- 未配置连接池、任务队列

如果需要面向生产演进：
- 数据库：SQLite → MySQL/PostgreSQL + 连接池
- 应用层：增加 Uvicorn workers 数量
- 调度瓶颈（F007 CPU 密集型）：拆为独立 Worker + Celery 异步任务
- 并发安全：调度写入加乐观锁/版本检查

这是有意识地做范围控制，而非技术遗漏。

### Q5：如何处理异常和重规划？

A：异常分为两类：
- **reroute**（道路/包裹异常）：仅重算 F006 路径规划，不改调度方案
- **redispatch**（节点异常）：完整重算 F007→F021→F005→F006

重规划通过版本链保留历史：`version+1`、`parent_id` 指向前版、`is_replan=true`、`replan_reason` 记录原因。方案 A/B 可完整对比。

### Q6：安全方面做了哪些设计？

A：
- 密码 bcrypt 哈希存储
- JWT 24h 过期 + HS256 签名
- RBAC 双角色权限（前端 UI + 后端双重控制）
- API Key 仅存后端 `.env`（`.gitignore` 排除）
- 日志不记录密码/Token
- 统一响应 format，避免信息泄露
- `init_db()` 对默认 JWT_SECRET 发出 RuntimeWarning

### Q7：项目中有哪些你觉得设计得好的地方？

A（按实际经验选取 3~4 个）：
1. **状态机集中管理**：所有状态流转必须经过 `state_machine.py`，112 个测试用例全覆盖，杜绝非法状态
2. **双标识策略**：库内用 `id` 做高效外键，API 暴露 `*_code` 业务编号，兼顾性能和安全性
3. **DeepSeek 降级策略**：AI 失败不伪造、不报错，而是标记降级继续执行
4. **版本化重规划**：异常场景下能完整保留历史方案，支持方案 A/B 对比

### Q8：测试覆盖率如何？

A：423 个测试用例，421 通过（99.53%）。分层覆盖：
- 算法层：F007/F005/F006/F021 独立测试
- 服务层：全部服务 + 状态机 112 项
- API 层：全部端点 + 权限控制 + 分页
- 集成层：调度流水线、异常重规划、到货确认全链路

### Q9：如何处理 L1→L2 的包裹生成？

A：不在一开始的 F021 生成 L1→L2 包裹。流程是：
1. F021 只生成 L0→L1 包裹
2. F005 L0→L1 执行后 → 模拟送达把货物运到 L1
3. 到货确认（`confirm-arrival`）→ 触发 `_trigger_repacking` 按 `order_code` 动态生成 L1→L2 包裹（保证同订单货物打成一个包裹）
4. F005 L1→L2 执行 → F006 路径规划

这样设计更贴近真实物流：「货物先到 L1 才能知道怎么发往 L2」。

### Q10：如果让你重新设计这个项目，你会改什么？

A：
1. **测试先行**：状态机和核心算法先写测试再写实现（当前是先实现后补测试）
2. **前端状态管理**：当前 Pinia store 拆得不够细，复杂调度页面的组件间通信可优化
3. **demo_mode 简化**：当前 demo_mode 逻辑和正常流程耦合较深，可单独抽为 `DemoOrchestrator`
4. **API 版本化**：从一开始就加 `/api/v1/` 前缀，方便 P1/P2 阶段 API 演变

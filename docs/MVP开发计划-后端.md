# MVP 开发计划 · 后端

| 字段 | 值 |
| --- | --- |
| **角色** | 后端开发（同学 A） |
| **技术栈** | Python 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic · SQLite |
| **总计划** | [MVP开发计划.md](./MVP开发计划.md) |
| **架构文档** | [系统架构设计说明书](./architecture/系统架构设计说明书.md) |
| **需求文档** | [PRD V2.7](./prds/03产品需求文档(PRD)-V2.7.md) |
| **Git 协作** | [Git协作规范.md](./Git协作规范.md) |

---

## 1. 你的职责范围

| 负责 | 不负责 |
| --- | --- |
| FastAPI 接口、JWT 认证、RBAC | 页面 UI、SVG 绘制 |
| 数据库模型、Alembic 迁移、种子数据 | 前端路由与组件 |
| F007 / F021 / F005 / F006 算法 | DQN / MLP+LSTM（P1） |
| DeepSeek API 代理（F014） | 运营统计（P2） |
| 异常重规划、模拟送达 API | Docker / K8s（可选） |

**核心原则**：

- 对外 API 统一使用 `*_code` 业务编号，内部用自增 `id` 做外键。
- 每个阶段完成后，先在 **Swagger / Postman** 自测通过，再通知前端联调。
- 接口契约以架构文档 §6 为准；有变更及时同步。

---

## 2. 推荐目录结构

```text
backend/
├── main.py
├── api/                    # 路由
│   ├── auth.py
│   ├── orders.py
│   ├── schedule.py
│   └── ...
├── services/               # 业务逻辑
│   ├── schedule_service.py
│   ├── deepseek_service.py
│   └── simulation_service.py
├── algorithms/             # 纯算法
│   ├── global_schedule.py  # F007
│   ├── packaging.py        # F021
│   ├── node_dispatch.py    # F005
│   └── route_planning.py   # F006
├── models/                 # SQLAlchemy 模型
├── schemas/                # Pydantic
├── config/
│   ├── database.py
│   └── algorithm_config.json
├── scripts/
│   └── init_demo_data.py
└── data/
    └── logistics.db
```

---

## 3. 分阶段任务

### 阶段 0：工程初始化

**目标**：后端可启动，Swagger 可访问。

| 任务 | 说明 |
| --- | --- |
| 初始化 FastAPI 项目 | `main.py` 注册路由、CORS |
| 配置 SQLite + SQLAlchemy | `backend/data/logistics.db` |
| 初始化 Alembic | 后续迁移统一管理 |
| 健康检查 | `GET /api/health` → `{ "status": "ok" }` |
| `.env.example` | `JWT_SECRET`、`DEEPSEEK_API_KEY` 等占位 |

**交付物**：可启动工程 + README 启动命令。

**自测**：

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 访问 http://localhost:8000/docs
```

**通知前端**：health 接口可用，端口 8000。

---

### 阶段 1：认证与权限

**目标**：登录发 Token，受保护接口需认证，manager 写操作 403。

| 任务 | 说明 |
| --- | --- |
| `users` 表迁移 | username、password_hash、role |
| 种子账号 | dispatcher / manager，密码 bcrypt(`123456`) |
| `POST /api/auth/login` | 返回 access_token、role、expires_in(86400) |
| `GET /api/auth/me` | 返回当前用户信息 |
| JWT 工具 | 签发、解码、过期校验 |
| 认证依赖 | `get_current_user` |
| RBAC 依赖 | `require_dispatcher`，manager 写接口 403 |
| 统一响应 | `{ code, message, data }` |

**自测**：

- [ ] 登录成功拿到 token
- [ ] 带 token 访问 `/auth/me` 成功
- [ ] manager token 调 POST 写接口返回 403
- [ ] 错误密码返回明确错误

**通知前端**：Swagger 链接 + 登录接口示例 JSON。

---

### 阶段 2：基础数据管理

**目标**：全部基础实体 CRUD + 演示数据脚本。

| 任务 | 说明 |
| --- | --- |
| 建表迁移 | nodes、storage_centers、sorting_centers、orders、goods、packages、vehicles、drivers |
| CRUD API | 见架构 §6.5.2；分页 `page` / `page_size` |
| 订单导入 | `POST /api/orders/import`（xlsx/csv） |
| 删除规则 | 配送中订单不可删；配送中车辆不可删 |
| 演示数据 | `init_demo_data.py`：5 存储中心、2 一级分拣、50 零级分拣、70 车、70 司机、50 订单 |
| 虚拟坐标 | 中心 (30.5, 114.3)，节点 ±0.1° 分布 |

**推荐顺序**：

```text
nodes → storage/sorting_centers → orders → goods
    → vehicles → drivers → packages（只读+repack）
    → init_demo_data.py
```

**自测**：

- [ ] seed 后数据量符合 PRD
- [ ] 订单按 status 筛选
- [ ] 删除配送中订单返回业务错误（code 非 0）
- [ ] 响应字段用 order_code，不暴露 id

**通知前端**：每完成一组 API 更新 Swagger；优先保证 orders / nodes / vehicles。

**过关说明**：全部 API Postman 测通即可进阶段 3；前端 CRUD 页可边做边补。

---

### 阶段 3：全局调度（F007 + F021）

**目标**：`POST /schedule/global` 10 秒内返回，写入 global_schedules 和 packages。

| 任务 | 说明 |
| --- | --- |
| `global_schedules` 表 | 含 version、parent_id、replan_reason、is_replan |
| F007 算法 | 规则评分 + 启发式；读 algorithm_config.json |
| 硬约束 | 一级分拣容量、同订单汇聚、最大存储时长 |
| F021 打包 | L0→L1 按节点对；L1→L2 按订单 |
| 编排服务 | F007 → 写库 → F021 → 写 packages |
| 状态更新 | 订单 → delivering |
| API | POST /schedule/global；GET 列表；GET /{schedule_code} |

**推荐顺序**：

```text
F007 最小可行 → 写 global_schedules → F021 → 写 packages → POST 接口 → GET 查询
```

**自测**：

- [ ] 有待分配订单时能生成方案
- [ ] packages 含 L0→L1 和 L1→L2
- [ ] 无解返回 code=40001，message 明确
- [ ] 10 秒内返回

**通知前端**：POST/GET 接口 + 响应 JSON 样例。

**必须与前端联调通过后**再进阶段 4。

---

### 阶段 4：节点间调度（F005）

**目标**：两次串行 F005，形成 dispatch_batches。

| 任务 | 说明 |
| --- | --- |
| 建表 | dispatch_batches、node_dispatches |
| F005 算法 | 载重、包裹不重复、距离优先 |
| L0→L1 第一次 | 查 from∈L0、to∈L1、status=packed 的包裹 |
| L1→L2 第二次 | 第一次成功后才执行；demo_mode 可跳过等待 |
| 司机分配 | 车辆 node 下 status=idle 司机，取第一个 |
| tasks JSON | from_node_code、to_node_code、package_codes、is_return |
| 批次状态机 | pending → l0_l1_done → completed / failed |
| API | POST /schedule/node-dispatch；GET /batches、/{batch_code} |

**自测**：

- [ ] demo_mode=true 下一次调用产生两次 level_phase 记录
- [ ] 第一次失败不执行第二次
- [ ] 每辆车有 driver_code

**必须与前端联调通过后**再进阶段 5。

---

### 阶段 5：路径规划（F006）

**目标**：节点间调度后自动生成 routes，提供坐标查询 API。

| 任务 | 说明 |
| --- | --- |
| `routes` 表 | route_segments JSON、total_emission |
| F006 算法 | Haversine + 2-opt |
| 触发时机 | node-dispatch 成功后对每辆车自动执行 |
| 路段数据 | MVP 可用节点间直线，road_name 填「虚拟路段」 |
| 碳排放 | 燃油：里程×0.2；电动：0 |
| API | GET /routes/by-vehicle/{vehicle_code}/coordinates |

**coordinates 响应结构**（与前端对齐）：

```json
{
  "vehicle_code": "鄂A12345",
  "route_code": "RT001",
  "nodes": [{ "node_code": "SC001", "latitude": 30.52, "longitude": 114.28, "role": "depot" }],
  "packages": [{ "package_code": "PKG001", "latitude": 30.51, "longitude": 114.29 }],
  "segments": [{ "road_name": "虚拟大道", "start_lng": 114.28, "start_lat": 30.52, "end_lng": 114.29, "end_lat": 30.51 }],
  "total_distance": 15.5,
  "total_time": 45.0
}
```

**自测**：

- [ ] 调度完成后 routes 表有记录
- [ ] coordinates 接口三类数据齐全

**必须与前端联调通过后**，核心主链路打通。

---

### 阶段 6：模拟送达（F013-1）

**目标**：`POST /simulation/deliver` 驱动状态流转。

| 任务 | 说明 |
| --- | --- |
| deliver 服务 | vehicle_code、package_code 均可选 |
| 无参数 | 处理所有 in_transit 包裹 |
| 状态规则 | L0→L1：货物 pending_pack；L1→L2：货物 delivered |
| 车辆 | delivering → idle |

**自测**：

- [ ] Postman 调用后 goods/packages/vehicles 状态正确

**过关说明**：Postman 测通即可进阶段 7；前端按钮可后补。

---

### 阶段 7：异常与重规划（F013）

**目标**：异常持久化 + 版本化重规划。

| 任务 | 说明 |
| --- | --- |
| `exception_events` 表 | 见架构 §5.4.4 |
| CRUD | GET/POST /api/exceptions |
| 推荐动作 | 节点 → redispatch；道路 → reroute |
| replan 服务 | parent_id、version+1、replan_reason |
| redispatch | 重跑 F007→F021→F005→F006 |
| reroute | 仅重跑 F006 |
| API | POST /exceptions/{event_code}/replan |

**自测**：

- [ ] 重规划后新 schedule version=2，parent 指向旧方案

**必须与前端联调通过**。

---

### 阶段 8：AI 助手与收尾

**目标**：DeepSeek 接入、埋点、回归测试。

| 任务 | 说明 |
| --- | --- |
| deepseek_service | httpx 调用；Key 从 .env 读取 |
| POST /api/ai/parse | 解析 → 调调度编排 |
| 降级 | 失败时 meta.degraded=true + 默认 traditional 参数 |
| log_events | login、global_schedule、node_dispatch、replan、deepseek_call |
| P1 占位 | explain/review/compare 返回 501 |
| 回归 | 完整跑一遍主链路 + 重规划 |

**自测**：

- [ ] DeepSeek 不可用时不崩溃，返回降级信息
- [ ] log_events 有记录

---

## 4. 阶段过关（后端视角）

| 阶段 | 你可独立进入下一阶段的条件 |
| --- | --- |
| 0 | health 200 |
| 1 | login/me + RBAC Postman 通过 |
| 2 | 全部 CRUD Swagger 可查 + seed 成功 |
| 3 | POST global 成功写库 |
| 4 | POST node-dispatch 产生 batch |
| 5 | coordinates API 有数据 |
| 6 | deliver API 状态正确 |
| 7 | replan 版本链正确 |
| 8 | ai/parse + 回归通过 |

> 阶段 1、3、4、5、7 还需与前端联调打勾后，团队才算整体过关。

---

## 5. 与前端协作要点

1. **每个阶段开始**：你先更新 Swagger，丢链接给前端。
2. **响应格式统一**：`{ code, message, data, meta? }`；业务失败可用 HTTP 200 + code≠0。
3. **字段命名**：API 层只用 `order_code`、`node_code`，不要漏出 `id`。
4. **长耗时接口**：调度类接口可能接近 10 秒，不要提前断开。
5. **demo_mode**：`POST /schedule/node-dispatch` 支持 `demo_mode: true`，课堂演示用。

---

## 6. 答辩前自检清单

- [ ] `uvicorn` 一条命令可启动
- [ ] `init_demo_data.py` 可重复执行或幂等
- [ ] dispatcher / manager 账号可登录
- [ ] 全局调度 → 节点间调度 → 路线坐标 全链路 Postman 通过
- [ ] 异常重规划产生新版本
- [ ] DeepSeek 失败时有降级，不 500 崩溃
- [ ] `.env` 未提交 Git

---

## 版本历史

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| V1.0 | 2026-06-09 | 后端分角色 MVP 开发计划 |

# DeepSeek 路径优化 - 智能物流平台

华中科技大学软件学院 2026 实训项目 · MVP 智能物流调度演示系统。

基于 DeepSeek 大模型的物流路径优化与调度平台，覆盖订单管理、全局调度（F007）、节点间调度（F005）、模拟送达（F013）、异常重规划（F013-2）、AI 助手（F014/F015）等能力。

## 当前进度

**MVP（阶段 0～8）**：已完成  
**P1（答辩增强）**：必做项已完成；选做项已实现 AI 方案解释（F015）

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| MVP | 主链路：订单 → 全局调度 → 节点调度 → 模拟送达 → 异常重规划 | ✅ |
| P1-1 | 方案评分、货物路径/节点调度搜索、实体详情 | ✅ |
| P1-2 | 订单筛选 + 预览确认全局方案 | ✅ |
| P1-3 | 节点到货确认（C/D 异常语义） | ✅ |
| P1-4 | 登录页与全站界面美化 | ✅ |
| P1-5 | AI 方案解释（F015，选做） | ✅ |

详细验收与演示脚本见 [P1 开发计划 §4](docs/P1开发计划.md#4-阶段验收检查表)。

## 功能概览

| 模块 | 说明 |
| --- | --- |
| 订单管理 | CRUD、Excel/CSV 批量导入（`POST /api/orders/import`） |
| 调度工作台 | 全局方案生成/预览/确认、节点间调度、路线可视化 |
| 模拟送达 | 按车/包裹驱动状态流转，支持 F021 重打包 |
| 节点到货确认 | 单包裹正常/异常确认与下游状态级联 |
| AI 助手 | 自然语言调度（F014）、方案解释（F015） |
| 异常管理 | 异常录入与 F013 重规划 |

## 快速启动

### 1. 后端

```bash
cd src/backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
# 编辑 .env，配置 DEEPSEEK_API_KEY（AI 功能需要；无 key 时 explain 会降级）

python -m scripts.init_demo_data   # 重建演示数据（初始状态）
uvicorn main:app --reload --port 8000
```

### 2. 前端

```bash
cd src/frontend
npm install
copy .env.example .env.local    # macOS/Linux: cp .env.example .env.local
# 联调时将 VITE_USE_MOCK_* 全部设为 false
npm run dev
```

- 前端：<http://localhost:5173>
- 后端 API：<http://localhost:8000/api>
- Swagger：<http://localhost:8000/docs>

### 3. 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `dispatcher` | `123456` | 调度员 |
| `manager` | `123456` | 管理员 |

`init_demo_data` 会创建节点、车辆、司机与 **100 条 pending 订单**，**不含**已确认的全局调度方案；演示调度前需先「预览 → 确认」生成方案，或通过 AI 助手生成 draft。

### 4. 演示用订单导入

仓库根目录 [`orderdata.xlsx`](orderdata.xlsx) 可用于答辩演示订单导入：

1. 登录 → **订单管理** → **导入**
2. 选择 `orderdata.xlsx`

必填列：`destination_node_code`、`time_window`、`goods_name`、`goods_type`、`weight`、`volume`；可选 `storage_center_code`。

## 答辩演示建议（约 6～8 分钟）

1. **登录页** → 展示界面美化
2. **订单管理** → 导入 `orderdata.xlsx`（可选）
3. **调度工作台** → 筛选订单 → 预览全局方案 → 确认采用
4. 查看方案评分、货物路径（搜索/详情）、节点间调度
5. **节点到货确认** → n_2 对 C 正常、D 异常 → 验证 F 为 exception
6. 再次节点调度 / 模拟送达 → 验证异常包裹不可 in_transit
7. （选做）AI 助手 → 选中方案 → **方案解释**

完整脚本见 [P1 开发计划 §4.2](docs/P1开发计划.md#42-答辩演示脚本建议约-68-分钟)。

## 项目结构

```text
LogisticsSystem/
├── orderdata.xlsx                    # 演示用订单导入表格（xlsx）
├── README.md
├── docs/                             # 项目文档
│   ├── MVP开发计划.md / P1开发计划.md   # 阶段计划与答辩验收
│   ├── P1功能概览.md
│   ├── 环境配置说明.md / 开发规范.md / Git协作规范.md
│   ├── 前后端联调规范.md
│   ├── 联调反馈-*.md                  # 各阶段联调记录
│   ├── api-contract/                 # API 契约（phase1～8、p1-*）
│   ├── architecture/                 # 系统架构（V1.0 基线 + V1.1 P1 交付版）
│   └── prds/                         # 产品需求文档 PRD
│
└── src/
    ├── backend/                      # Python FastAPI 后端
    │   ├── main.py                   # 应用入口
    │   ├── requirements.txt
    │   ├── .env.example              # 环境变量模板（含 DEEPSEEK_API_KEY）
    │   ├── pytest.ini
    │   │
    │   ├── api/                      # REST 路由层
    │   │   ├── auth.py               # 登录 / JWT
    │   │   ├── orders.py             # 订单 CRUD + 导入
    │   │   ├── schedule.py           # 全局调度 / 节点调度 / 批次
    │   │   ├── simulation.py         # 模拟送达
    │   │   ├── arrival_confirm.py    # 节点到货确认（P1-08）
    │   │   ├── exception_events.py   # 异常与重规划
    │   │   ├── ai.py                 # AI 解析 / 方案解释 / 审查 / 异常分析
    │   │   ├── nodes.py / goods.py / packages.py / vehicles.py / drivers.py
    │   │   └── routes.py             # 路线坐标
    │   │
    │   ├── services/                 # 业务逻辑层
    │   │   ├── schedule_service.py / dispatch_service.py
    │   │   ├── simulation_service.py / arrival_confirm_service.py
    │   │   ├── order_service.py / exception_service.py / replan_service.py
    │   │   ├── deepseek_service.py   # DeepSeek 调用
    │   │   └── state_machine.py      # 状态机
    │   │
    │   ├── algorithms/               # 调度算法（F007/F005/F006/F021）
    │   │   ├── global_schedule.py / node_dispatch.py
    │   │   ├── route_planning.py / packaging.py
    │   │
    │   ├── models/                   # SQLAlchemy 数据模型
    │   ├── schemas/                  # Pydantic 请求/响应模型
    │   ├── config/                   # 数据库配置、algorithm_config.json
    │   ├── core/                     # 统一响应、错误码
    │   ├── utils/                    # 工具函数
    │   ├── alembic/                  # 数据库迁移
    │   ├── data/                     # SQLite 数据库（logistics.db，不提交或本地生成）
    │   │
    │   ├── scripts/                  # 运维与联调脚本
    │   │   ├── init_demo_data.py     # 重建演示数据（答辩前常用）
    │   │   └── test_p1_1_integration.py  # 联调冒烟示例
    │   │
    │   └── tests/                    # 单元 / 集成 / API 测试
    │       ├── api/                  # 接口测试
    │       ├── integration/          # 流水线集成测试
    │       └── unit/                 # 服务层、算法单测
    │
    └── frontend/                     # Vue 3 + TypeScript + Vite
        ├── package.json
        ├── vite.config.ts            # 开发代理 /api → localhost:8000
        ├── .env.example              # Mock 开关模板
        │
        └── src/
            ├── main.ts / App.vue
            ├── router/index.ts       # 路由（Dashboard、订单、到货确认等）
            ├── layouts/
            │   └── MainLayout.vue    # 侧栏 + 顶栏布局
            │
            ├── views/                # 页面
            │   ├── Login.vue
            │   ├── Dashboard.vue     # 调度工作台（核心演示页）
            │   ├── orders/OrderList.vue
            │   ├── arrival/ArrivalConfirm.vue
            │   ├── exceptions/ExceptionList.vue
            │   ├── goods/ / packages/ / nodes/ / vehicles/ / drivers/
            │   └── HealthCheck.vue
            │
            ├── components/
            │   ├── schedule/         # 调度相关（路径表、地图、批次面板等）
            │   ├── ai/               # AI 助手面板、方案解释抽屉
            │   ├── detail/           # 实体详情抽屉（订单/货物/包裹等）
            │   ├── crud/             # 通用表格、分页、工具栏
            │   └── login/Owl.vue     # 登录页动画
            │
            ├── composables/          # 组合式逻辑
            │   ├── useGlobalSchedule.ts / useNodeDispatch.ts
            │   ├── useAiParse.ts / useAiExplain.ts
            │   ├── useArrivalConfirm.ts / useSimulationDelivery.ts
            │   └── useDashboardDetail.ts
            │
            ├── api/                  # Axios 封装与接口调用
            │   ├── request.ts        # 拦截器、postWithMeta / postWithBusinessCode
            │   ├── orders.ts / schedule.ts / simulation.ts / ai.ts
            │   └── ...
            │
            ├── stores/auth.ts        # 登录态
            ├── types/                # TypeScript 类型定义
            ├── utils/                # Mock 数据、格式化、env 开关
            ├── constants/            # 状态枚举、到货常量
            ├── styles/               # 全局 CSS 变量与样式
            └── assets/               # 登录背景、Owl 图片等静态资源
```

> 本地配置文件（不提交 Git）：`src/backend/.env`、`src/frontend/.env.local`

## 文档

| 文档 | 说明 |
| --- | --- |
| [环境配置说明](docs/环境配置说明.md) | 安装、环境变量、联调检查 |
| [MVP 开发计划](docs/MVP开发计划.md) | MVP 阶段总览与验收 |
| [P1 开发计划](docs/P1开发计划.md) | P1 任务、验收与答辩脚本 |
| [P1 功能概览](docs/P1功能概览.md) | P1 功能清单与范围 |
| [开发规范](docs/开发规范.md) | 依赖与环境变量记录规范 |
| [Git 协作规范](docs/Git协作规范.md) | 分支与 PR |
| [系统架构设计说明书 V1.0（基线）](docs/architecture/系统架构设计说明书.md) | MVP 架构、ER、接口、评审 |
| [系统架构设计说明书 V1.1（P1 交付版）](docs/architecture/系统架构设计说明书-V1.1-P1交付版.md) | **P1 完成后实际架构与模块映射** |
| [PRD V2.7（需求基线）](docs/prds/03产品需求文档(PRD)-V2.7.md) | 原始产品需求与澄清历史 |
| [PRD V2.8（P1 交付版）](docs/prds/04产品需求文档(PRD)-V2.8-P1交付版.md) | **P1 完成后实际交付范围与验收** |
| [API 契约](docs/api-contract/) | 各阶段接口契约 |

## 已知限制（答辩说明）

- P1-12 权限细化未做（如 manager 调 `/ai/parse` 限制）
- P1-13 模拟送达批量增强未做
- AI 方案审查 / 异常分析后端已实现，前端仍为占位按钮
- `init_demo_data` 不预置全局方案，演示前需手动造方案

---

详细安装与排错见 [docs/环境配置说明.md](docs/环境配置说明.md)。

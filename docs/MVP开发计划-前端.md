# MVP 开发计划 · 前端

| 字段 | 值 |
| --- | --- |
| **角色** | 前端开发（同学 B） |
| **技术栈** | Vue 3 · TypeScript · Vite · Element Plus · Pinia · Axios |
| **总计划** | [MVP开发计划.md](./MVP开发计划.md) |
| **架构文档** | [系统架构设计说明书](./architecture/系统架构设计说明书.md) |
| **需求文档** | [PRD V2.7](./prds/03产品需求文档(PRD)-V2.7.md) |
| **Git 协作** | [Git协作规范.md](./Git协作规范.md) |

---

## 1. 你的职责范围

| 负责 | 不负责 |
| --- | --- |
| 页面、路由、组件、交互 | 调度算法实现 |
| Axios 封装、Token 管理 | 数据库与迁移 |
| 调度工作台、SVG 路线图 | DeepSeek API 直连（走后端代理） |
| 角色权限 UI（按钮显隐） | 后端 RBAC 实现 |
| Mock 数据并行开发 | 运营统计看板（P2） |

**核心原则**：

- 所有 API 通过后端代理，**不存 API Key**。
- 后端接口未就绪时，用 Mock JSON 先搭页面，接口好了再切换。
- 业务展示统一用 `*_code`（如 `order_code`），不要用数据库 `id`。
- manager 账号：**隐藏**所有写操作按钮（后端仍会 403 兜底）。

---

## 2. 推荐目录结构

```text
frontend/
├── src/
│   ├── api/                # 按模块封装请求
│   │   ├── request.ts      # Axios 实例、拦截器
│   │   ├── auth.ts
│   │   ├── orders.ts
│   │   └── schedule.ts
│   ├── stores/
│   │   └── auth.ts         # Pinia：token、role
│   ├── router/
│   │   └── index.ts        # 路由守卫
│   ├── layouts/
│   │   └── MainLayout.vue  # 顶栏+侧栏
│   ├── views/
│   │   ├── Login.vue
│   │   ├── Dashboard.vue   # 调度工作台
│   │   ├── orders/
│   │   └── ...
│   ├── components/
│   │   └── RouteMap.vue    # SVG 路线图
│   └── types/              # TS 接口类型
├── vite.config.ts          # /api 代理 → :8000
└── package.json
```

---

## 3. 分阶段任务

### 阶段 0：工程初始化

**目标**：前端可启动，能请求后端 health 接口。

| 任务 | 说明 |
| --- | --- |
| 创建 Vite + Vue3 + TS 项目 | `npm create vite@latest` |
| 安装依赖 | element-plus、pinia、vue-router、axios |
| Vite 代理 | `/api` → `http://localhost:8000` |
| Axios 封装 | baseURL、timeout(建议 15s)、响应拦截骨架 |
| 基础 Layout | 顶栏 + 侧栏 + router-view |
| 联通测试页 | 按钮调 `/api/health` 显示结果 |

**交付物**：可启动工程 + Layout 骨架。

**自测**：

```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
```

**依赖后端**：health 接口（阶段 0 联调）。

---

### 阶段 1：认证与权限

**目标**：登录、登出、路由守卫、角色区分。

| 任务 | 说明 |
| --- | --- |
| 登录页 | 用户名、密码、错误提示 |
| auth store | login / logout；存 token、role、display_name |
| localStorage | 刷新页面保持登录 |
| 请求拦截 | 自动加 `Authorization: Bearer {token}` |
| 响应拦截 | 401 → 清 token → 跳转 /login |
| 路由守卫 | 未登录 → /login |
| 角色跳转 | dispatcher、manager 均进 /dashboard（manager 只读） |
| Layout | 顶栏显示用户名、退出按钮 |

**Mock 策略**：登录接口未好时，可临时写死 token 开发 Layout，阶段结束前必须切真实接口。

**自测**：

- [ ] dispatcher 登录进工作台
- [ ] 刷新后仍登录
- [ ] 改坏 token 跳登录页
- [ ] manager 看不到「新增」「删除」等按钮

**必须与后端联调通过**。

---

### 阶段 2：基础数据管理

**目标**：基础数据模块页面，至少订单/节点/车辆对接真实 API。

| 任务 | 说明 |
| --- | --- |
| 侧栏菜单 | 订单、货物、包裹、车辆、司机、存储中心、分拣中心 |
| 通用列表模板 | el-table + 分页 + 筛选 + loading + 空状态 |
| 通用表单 | Dialog 新增/编辑；表单校验 |
| **优先：订单页** | 列表、status 筛选、CRUD、Excel 导入 |
| **优先：节点页** | 存储中心 / 分拣中心筛选或 Tab |
| **优先：车辆页** | 按节点筛选、状态展示 |
| 货物/司机/包裹 | 列表查看；CRUD 可第二批 |
| manager 只读 | `v-if="role==='dispatcher'"` 控制按钮 |
| TS 类型 | 与 Swagger 字段对齐 |

**推荐顺序**：

```text
列表模板 → 订单页 → 节点页 → 车辆页 → 其余页面
```

**Mock 策略**：`public/mock/orders.json` 等，接口就绪后逐个替换。

**自测**：

- [ ] 能看到演示订单数据
- [ ] 新增订单成功
- [ ] manager 无编辑入口

**过关说明**：订单/节点/车辆三页对接完成即可配合后端进阶段 3；其余页可后续补。

---

### 阶段 3：全局调度（F007 + F021）

**目标**：调度工作台 v1，能触发全局调度并查看方案。

| 任务 | 说明 |
| --- | --- |
| Dashboard 页面 | 登录后默认页 /dashboard |
| 生成全局调度按钮 | 调 POST /api/schedule/global |
| loading | 按钮 disabled + 最长 10 秒提示 |
| 方案下拉 | GET /schedule/global → el-select |
| 摘要卡片 | distance、time、goods、score |
| 查看详情 | 异步 GET /schedule/global/{code} |
| 侧边栏 | 货物路径表：goods_code、path |
| 错误提示 | code≠0 时 ElMessage.error(message) |

**Mock 策略**：先用静态 schedule JSON 搭布局。

**自测**：

- [ ] 点击按钮后摘要与详情一致
- [ ] 切换历史方案数据变化
- [ ] 无解时有明确提示

**必须与后端联调通过**。

---

### 阶段 4：节点间调度（F005）

**目标**：工作台扩展，展示批次与车辆任务。

| 任务 | 说明 |
| --- | --- |
| 生成节点间调度按钮 | POST /schedule/node-dispatch |
| 传参 | schedule_code（当前选中方案）、demo_mode |
| demo_mode 开关 | el-switch，默认 false |
| 批次信息 | batch_code、status、车辆数 |
| 车辆任务表 | vehicle_code、driver_code、distance、tasks |
| tasks 展开 | from → to、package_codes |
| 失败提示 | 无包裹/无车辆/第一次失败 |

**自测**：

- [ ] demo_mode=true 可一次看到 L0→L1 和 L1→L2 任务

**必须与后端联调通过**。

---

### 阶段 5：路径可视化（F010）

**目标**：SVG 静态路线图，核心主链路在前端闭环。

| 任务 | 说明 |
| --- | --- |
| RouteMap.vue | SVG 组件，viewBox 自适应 |
| 车辆卡片 | 点击加载 coordinates API |
| 坐标映射 | 经纬度 → SVG 像素（线性变换） |
| 绘制 | 红=节点、蓝=包裹、线=路线 |
| 多车 | 最多 10 辆，不同 stroke 颜色 |
| 交互 | 点击包裹点 → 侧边栏详情 |
| loading | 切换车辆时显示 |

**推荐顺序**：

```text
画静态点 → 画线 → 接 API → 多车颜色 → 点击交互
```

**自测**：

- [ ] 选车辆能看到路线
- [ ] 切换车辆路线变化
- [ ] 10 辆车以内不卡

**必须与后端联调通过**——MVP 核心验收点。

---

### 阶段 6：模拟送达（F013-1）

**目标**：提供演示用操作入口。

| 任务 | 说明 |
| --- | --- |
| 模拟送达按钮 | 工作台或包裹列表 |
| 调 POST /simulation/deliver | body 可空（全部送达） |
| 刷新列表 | 成功后 re-fetch 包裹/货物状态 |
| tooltip | 说明与 demo_mode 配合使用 |

**自测**：

- [ ] 点击后列表状态更新

**过关说明**：答辩前必须有入口；开发期可等后端 API 好了再接。

---

### 阶段 7：异常与重规划（F013）

**目标**：异常录入、触发重规划、版本展示。

| 任务 | 说明 |
| --- | --- |
| 异常列表页 | /exceptions |
| 录入表单 | type、target_code、description |
| 推荐动作展示 | 显示 redispatch / reroute |
| 触发重规划按钮 | POST replan，长 loading |
| 版本标识 | 方案下拉标注「重规划 v2」、is_replan 标签 |
| 刷新 | 重规划后刷新 Dashboard、路线图 |

**自测**：

- [ ] 录入异常 → 重规划 → 下拉出现新版本
- [ ] 旧版本仍可查看

**必须与后端联调通过**。

---

### 阶段 8：AI 助手与收尾

**目标**：AI 对话框、降级 UI、体验打磨、答辩彩排。

| 任务 | 说明 |
| --- | --- |
| AI 对话框 | 工作台右侧或浮层 |
| POST /api/ai/parse | 输入自然语言发送 |
| 降级 UI | meta.degraded=true → ElAlert 警告 |
| P1 置灰 | 方案对比、AI 解释等「即将推出」 |
| manager 复查 | 全站写按钮隐藏 |
| 体验 | 统一 ElMessage、loading、空状态 |
| 彩排 | 按总计划 §5.2 演示脚本走一遍 |

**自测**：

- [ ] AI 成功或降级两种路径都可演示
- [ ] 5 分钟答辩脚本流畅

---

## 4. 阶段过关（前端视角）

| 阶段 | 你完成即可推进的条件 |
| --- | --- |
| 0 | dev server 启动 + health 显示 |
| 1 | 登录/守卫/角色跳转正确 |
| 2 | 订单+节点+车辆页对接完成 |
| 3 | 工作台全局调度 happy path |
| 4 | 节点间调度+批次展示 |
| 5 | SVG 路线图可展示 |
| 6 | 模拟送达有按钮（答辩前） |
| 7 | 异常页+重规划版本标识 |
| 8 | AI 对话框+降级 UI+彩排通过 |

> 阶段 1、3、4、5、7 需与后端联调后，团队才算整体过关。

---

## 5. 与后端协作要点

1. **等 Swagger，不猜字段**：每个阶段向后端要 OpenAPI 链接。
2. **响应解包**：统一从 `response.data.data` 取业务数据；注意 `code !== 0` 的业务错误。
3. **调度接口慢**：Axios timeout 建议 ≥15s；按钮防重复点击。
4. **降级展示**：`meta.degraded === true` 时必须提示用户，不要显示「AI 成功」。
5. **不要直连 DeepSeek**：所有 AI 请求走 `/api/ai/*`。

---

## 6. 页面路由规划（建议）

| 路径 | 页面 | 阶段 |
| --- | --- | --- |
| /login | 登录 | 1 |
| /dashboard | 调度工作台 | 3 |
| /orders | 订单管理 | 2 |
| /goods | 货物管理 | 2 |
| /packages | 包裹管理 | 2 |
| /vehicles | 车辆管理 | 2 |
| /drivers | 司机管理 | 2 |
| /nodes/storage | 存储中心 | 2 |
| /nodes/sorting | 分拣中心 | 2 |
| /exceptions | 异常管理 | 7 |

---

## 7. 答辩前自检清单

- [ ] `npm run dev` 可启动，代理正确
- [ ] dispatcher 完整演示路径无报错
- [ ] manager 登录后无任何写入口
- [ ] 全局调度 → 节点间调度 → SVG 路线图 流畅
- [ ] 重规划后能看到版本标识
- [ ] DeepSeek 失败时降级提示可见
- [ ] 移动端不强制适配（实训演示用 PC 即可）

---

## 版本历史

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| V1.0 | 2026-06-09 | 前端分角色 MVP 开发计划 |

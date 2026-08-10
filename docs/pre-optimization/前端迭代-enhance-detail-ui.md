# 前端迭代：详情与信息增强（enhance-detail-ui）

> 在阶段 0～8 主流程不变的前提下，增量补全「查看详情」与 Dashboard 信息展示能力。

---

## 迭代摘要

| 项 | 说明 |
|----|------|
| 分支 | `frontend/enhance-detail-ui`（基于 `main` @ `eef767f`） |
| 目标 | **只增不改**：详情抽屉、富字段展示、跨页跳转、Dashboard 追加信息区 |
| 构建 | `npm run build` 通过（vue-tsc + vite） |
| PR | 待创建：`frontend/enhance-detail-ui` → `main` |

---

## 功能清单

### 详情基础设施

| 新增 | 路径 | 说明 |
|------|------|------|
| 通用详情抽屉 | `src/frontend/src/components/detail/EntityDetailDrawer.vue` | `el-drawer` + loading，宽度 `480px` |
| 描述列表块 | `src/frontend/src/components/detail/DetailDescriptions.vue` | 统一 `el-descriptions` border 样式 |
| 详情状态 | `src/frontend/src/composables/useEntityDetail.ts` | `open` / `close` / loading 管理 |
| 跨页跳转 | `src/frontend/src/utils/detail-navigation.ts` | 方案 / 包裹 / 订单 query 跳转 |
| 样式变量 | `src/frontend/src/styles/variables.css` | 间距、抽屉宽度等（仅新组件引用） |

### 业务详情 API（纯新增）

| API | 路径 |
|-----|------|
| `getOrder(code)` | `api/orders.ts` |
| `getPackage(code)` | `api/packages.ts` |
| `getGoods(code)` | `api/goods.ts` |
| `getDriver(code)` | `api/drivers.ts` |
| `getVehicle(code)` | `api/vehicles.ts` |
| `getNode(code)` | `api/nodes.ts` |
| `getException(code)` | `api/exceptions.ts`（已有，本次接入 UI） |

### 列表页「查看」入口（操作列追加，保留原有 CRUD / replan）

| 页面 | 详情内容 |
|------|----------|
| `OrderList.vue` | 货物子表、状态、`updated_at` |
| `PackageList.vue` | 起终点名称、`goods_items`、批次号 |
| `ExceptionList.vue` | 全字段 + 描述；表格追加「描述」列 |
| `GoodsList.vue` | 货物完整字段 + 订单跳转 |
| `DriverList.vue` | 司机完整字段 |
| `VehicleList.vue` | 车辆完整字段（与编辑 Dialog 并存） |
| `NodeList.vue` | 节点完整字段（与编辑 Dialog 并存） |

### Dashboard 追加区块（不重组 Tabs / 不移动 AI 面板）

| 组件 | 数据 | 展示 |
|------|------|------|
| `SchedulePackagesPanel.vue` | `detail.packages[]` | 折叠面板「方案包裹一览」 |
| `UnallocatedAlert.vue` | `batchDetail.unallocated_packages` | 有数据时 warning 告警 |
| `ScheduleSummaryCards` | `summary.package_count` | 追加第 5 张「包裹数」卡片 |
| `RouteDetailMeta.vue` | `getRouteDetail.total_emission` | 路线区距离/时间/碳排放 |

### 详情 Body 组件

`components/detail/`：`OrderDetailBody`、`PackageDetailBody`、`ExceptionDetailBody`、`GoodsDetailBody`、`DriverDetailBody`、`VehicleDetailBody`、`NodeDetailBody`

---

## 与阶段 0～8 关系

### 明确未改动

- `MainLayout.vue` 侧栏/顶栏结构
- Dashboard 整体信息架构（未改为 Tabs）
- `ExceptionList` 录入 / replan / 解决表单逻辑
- `useAiParse.ts` / `AiAssistantPanel` 交互
- `PageToolbar` / `DataTable` 契约
- 异常分页事件不一致问题（另开 bugfix PR）

### 新增文件索引

```
src/frontend/src/
├── components/detail/
│   ├── EntityDetailDrawer.vue
│   ├── DetailDescriptions.vue
│   ├── OrderDetailBody.vue
│   ├── PackageDetailBody.vue
│   ├── ExceptionDetailBody.vue
│   ├── GoodsDetailBody.vue
│   ├── DriverDetailBody.vue
│   ├── VehicleDetailBody.vue
│   └── NodeDetailBody.vue
├── components/schedule/
│   ├── SchedulePackagesPanel.vue
│   ├── UnallocatedAlert.vue
│   └── RouteDetailMeta.vue
├── composables/useEntityDetail.ts
├── styles/
│   ├── variables.css
│   └── detail-shared.css
└── utils/detail-navigation.ts
```

---

## 自测与验收

| 检查项 | 结果 |
|--------|------|
| `npm run build` | 通过 |
| 订单 / 包裹 / 异常「查看」抽屉 | 手测路径可用 |
| 基础数据四页「查看」 | 手测路径可用 |
| Dashboard 包裹一览 / unallocated 告警 | 联调时有数据即展示 |
| 回归：全局调度、node 异常 replan、AI 新建/重规划 | 主路径逻辑未改，需合并前再跑一遍 |

### 手测路径示例

1. **订单**：订单管理 → 任意行「查看」→ 抽屉展示货物子表
2. **包裹**：包裹管理 →「查看」→ 货物明细中订单编号可跳转
3. **异常**：异常管理 →「查看」→ 关联方案可跳转 Dashboard `?schedule=`
4. **Dashboard**：选择方案 → 摘要卡含包裹数 → 展开「方案包裹一览」；有未分配包裹时出现告警
5. **路线**：路径规划后 → 地图上方显示距离/时间/碳排放（API 有 `total_emission` 时）

---

### 阶段 5：增量美化

| 项 | 说明 |
|----|------|
| `styles/variables.css` | 间距、圆角、文字色、meta 背景等 CSS 变量 |
| `styles/detail-shared.css` | 详情副文本、区块标题、空态、Dashboard 信息条共用 class |
| `EntityDetailDrawer` | 固定 `480px`、loading 文案「加载详情中…」 |
| `DetailDescriptions` | 统一 border + 标签列宽变量 |
| 新组件 | 均使用变量 / 共用 class；**旧列表页 `.page-card` 未改** |

---

## 已知限制与后续

| 项 | 说明 |
|----|------|
| Mock `schedule-details.json` | 无 `packages[]` 字段，Mock 模式下包裹一览为空态；联调真实 API 有数据 |
| 异常分页 | `ExceptionList` 仍用 `@page-change`（与 `TablePagination` 事件名不一致），本次不修 |
| P2 美化 | MainLayout 重构、Dashboard Tabs 分区等不在本迭代 |
| 司机 CRUD | 仅「查看」，完整 CRUD 后续迭代 |
| 独立详情路由 | 如 `/orders/:id` 未做，统一用抽屉 |

---

## PR 建议

- **标题**：`feat(frontend): 详情查看与信息展示增强（enhance-detail-ui）`
- **说明**：引用本文档；强调「只增不改」与阶段 8 主路径回归要求

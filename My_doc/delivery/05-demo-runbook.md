# 5～10 分钟无 Docker 演示 Runbook

> 目标：用前端 Mock 稳定展示业务产品形态，再用仓库中的可审计证据说明后端一致性、故障韧性和安全发布。Mock UI 不冒充真实后端 E2E。

## 演示模式

### 权威启动命令

```bash
cd src/frontend
cp .env.example .env.local
# 确认所有 VITE_USE_MOCK_*=true
npm install
npm run dev
```

访问 `http://localhost:5173`。Mock 登录使用已定义的 demo 用户名（推荐 `admin`）和密码 `123456`；这是 disposable/non-production 演示凭据。完整说明见 [docs/06-启动说明.md](../../docs/06-启动说明.md#方式三仅前端mock-演示)。

### 环境确认

- `.env.local` 不提交 Git；
- `VITE_USE_MOCK_AUTH/BASIC_DATA/SCHEDULE/NODE_DISPATCH/ROUTES/SIMULATION/EXCEPTIONS/AI` 均为 `true`；
- 不启动后端、不安装 Docker、不执行 Compose；
- 浏览器缩放建议 90%～100%；关闭个人通知和无关标签页；
- 预先打开两个证据页：
  - [项目一页卡](01-project-one-pager.md)
  - [Claim-to-evidence 台账](02-claim-evidence-ledger.md)

## 10 分钟标准流程

| 时间 | 页面 / 操作 | 讲解重点 | 预期结果 | Fallback |
|---:|---|---|---|---|
| 0:00–0:45 | `/login`，以 `admin / 123456` 登录 | 平台覆盖订单、调度、异常、报表、通知和权限；本次是纯前端 Mock 产品演示 | 登录后进入第一个有权限页面 | 刷新后重登；不要切换真实 auth |
| 0:45–1:45 | `/dashboard` | 调度工作台是业务主入口；方案先生成候选，再经人工确认闸门生效 | 显示调度概览、候选或路线相关内容 | 若图表尚未渲染，先讲业务链路再进入订单页 |
| 1:45–2:45 | `/orders` | 展示订单筛选、创建/导入入口和订单到调度的上游关系 | 列表和操作入口可见 | 不现场导入未知文件，使用现有 mock 数据 |
| 2:45–4:15 | 返回 `/dashboard`，选择/查看调度与路线 | 可插拔调度策略、Top-K 候选、解释性和人工确认；地图无 Key 时可降级为 Canvas/SVG 路线 | 路线和方案信息可见 | 无地图 Key 属预期降级，直接说明三档地图降级 |
| 4:15–5:45 | `/exceptions`，选择异常并进入重规划 | 产品层展示 partial/full/hybrid 重规划和差异；工程层由持久化 Saga、lease/token 和 outbox 支撑 | 展示异常列表、策略和重规划结果/跳转 | 如果 mock 状态已改变，刷新页面恢复初始数据或只讲现有记录 |
| 5:45–6:45 | `/arrival-confirm` 或 `/notifications` | 到货/调度确认使用 CAS，通知不放在数据库锁内而由 outbox 恢复 | 可看到确认任务或通知配置 | 无可确认行时展示页面结构，并切到证据台账 CAS-01 |
| 6:45–7:45 | `/reports` | 报表覆盖 SLA、成本、异常和运力；这里展示业务闭环，不声称实时生产数据 | Dashboard 图表可见 | 若动画慢，等待一次渲染，不刷新多次 |
| 7:45–8:30 | 切换到受限 demo 账号（可选 `viewer`） | 前端按 `/me` 权限集合和 `can()` 控制路由/按钮；真正授权仍在后端 `require_permission()` | 菜单或操作能力收缩 | 如果当前 Mock 角色映射与页面表现不稳定，跳过切换，展示路由权限说明 |
| 8:30–10:00 | 打开项目一页卡和证据台账 | 收束到三个工程点：CAS/幂等、Saga/outbox、先扫描后发布；主动交代生产部署边界 | 面试官能看到数字、环境、PR/CI/CD 和限制 | 用下方 60 秒工程证据话术完成 |

## 60 秒工程证据话术

> 刚才 UI 使用 Mock，主要展示产品流程；后端正确性不是由这段演示证明，而是由分层证据证明。P0 用独立 Session 测试验证 CAS 在 20/100 个竞争者下最多一个成功，并用数据库状态机解决跨 worker 幂等。P1 在 GitHub Actions 的 PostgreSQL 16、Redis 7、两个 HTTP worker 和独立 outbox worker 上复跑协议，覆盖 Redis pause、worker restart、数据库断连和 lease reclaim。独立写场景完成 600/600 replay 且无重复副作用；两小时 soak 在该窗口内 0 errors，预热后 RSS 约 1.002x。发布先生成 SBOM 和执行 Trivy policy，阻断基础镜像漏洞后通过切换发行版解决，最终零 exception 发布固定 SHA 镜像。这些是工程验收结果，不等于生产部署或生产 SLA。

## 5 分钟压缩版

1. **0:00–0:30**：登录 + 30 秒项目介绍；
2. **0:30–1:30**：Dashboard 调度候选、路线、确认闸门；
3. **1:30–2:15**：订单页说明业务输入；
4. **2:15–3:15**：异常页说明 Saga/outbox 恢复；
5. **3:15–4:00**：报表或权限页面说明业务闭环；
6. **4:00–5:00**：证据台账收束 CAS、100k 编号、600 replay 和安全门禁。

## 8 分钟推荐版

- 标准流程删除“切换受限账号”和通知页；
- Dashboard 与异常重规划各保留 90 秒；
- 最后保留 90 秒工程证据和边界。

## 页面与可讲能力

| 路由 | 页面 | 可讲内容 | 不应据此声称 |
|---|---|---|---|
| `/dashboard` | 调度工作台 | 候选方案、确认闸门、路线与状态概览 | Mock 方案即真实算法或真实数据库结果 |
| `/orders` | 订单管理 | CRUD/筛选/导入入口、业务上游 | 现场展示即已完成生产 ERP 联调 |
| `/goods`、`/packages` | 货物/包裹 | 订单拆分与物流对象 | UI 列表证明原子编号并发能力 |
| `/vehicles`、`/drivers` | 运力资源 | 调度约束输入 | 当前数据代表真实运力 |
| `/nodes/storage`、`/nodes/sorting` | 节点 | 分层物流网络 | 地图折线代表真实道路导航 |
| `/exceptions` | 异常管理 | 重规划策略、差异和恢复业务 | Mock 操作证明 Saga 故障矩阵 |
| `/arrival-confirm` | 到货确认 | 确认状态转换 | 单次点击证明 100 并发性能 |
| `/notifications` | 通知设置 | 渠道配置与 outbox 背景 | 外部投递 exactly-once |
| `/reports` | 报表分析 | SLA/成本/异常/运力闭环 | Mock 图表是生产实时统计 |
| `/health` | 前端联通测试页面（调用后端 `GET /api/health`） | 前后端联调辅助 | 未启动后端时健康检查真实通过 |

## 权限演示说明

当前后端正式角色体系包含 `admin`、`dispatcher`、`viewer`、`warehouse_operator` 和兼容角色 `manager`；路由分别要求诸如 `schedule:read`、`orders:read`、`exceptions:read`、`arrivals:confirm`。现场最稳妥的是：

- 用 `admin` 完整走业务；
- 若切换只读账号，先在彩排中确认当前 Mock 映射与菜单表现；
- 明确“前端路由和按钮显隐不是安全边界，后端 dependency 才是强制权限检查”；
- 不用历史指南中的旧两角色体系解释当前 RBAC。

## 彩排检查清单

### 演示前一天

- [ ] 从干净依赖安装执行 `npm install` 或 `npm ci`，确认 `npm run dev` 可启动；
- [ ] 确认 `.env.local` 所有 Mock 开关为 true；
- [ ] 逐个打开标准流程路由；
- [ ] 记录哪些交互会改变内存 mock 状态，决定是否刷新恢复；
- [ ] 验证 admin 登录、退出和可选 viewer 登录；
- [ ] 确认 Mermaid/Markdown 证据页能离线显示；
- [ ] 准备浏览器书签和 5/8/10 分钟计时版本。

### 演示前 5 分钟

- [ ] 启动前端并打开 `/login`；
- [ ] 清理浏览器 console 中与演示无关的旧日志；
- [ ] 打开项目一页卡和证据台账到对应锚点；
- [ ] 关闭敏感窗口、终端历史和私人消息；
- [ ] 禁用系统通知；
- [ ] 不在现场临时升级 npm 包或切换真实 API。

## 失败处理

| 故障 | 处理 |
|---|---|
| npm 安装失败 | 使用彩排时已安装且锁文件一致的环境；不要现场改依赖 |
| 页面刷新后回登录 | 重新用 disposable Mock 账号登录，跳到下一段 |
| 图表/地图没有显示 | 说明无地图 Key 的降级设计，切换到订单或异常页 |
| 某个 Mock 操作无数据 | 不现场造数据，展示页面结构并切到 evidence ledger |
| 演示超时 | 立即跳到“60 秒工程证据话术”收束 |
| 被追问生产部署 | 明确 R2 工程交付已完成，但 Compose/02B/生产拉起属于独立 P3-PROD follow-up |

## 现场禁区

- 不展示 `.env*`、JWT、API key、cookie、CI 原始日志或数据库文件；
- 不临时拉取 `latest` 镜像做审计；固定批次才是 `f9e08a4...`；
- 不把 Mock 页面点击说成 PostgreSQL/Redis E2E；
- 不说“exactly-once”“永久无泄漏”“系统 P95 9.81 ms”或“生产级”；
- 不引用旧 PPT 中的 2-opt 已实现、旧角色/状态、旧测试/API 数或未经佐证的效率百分比。

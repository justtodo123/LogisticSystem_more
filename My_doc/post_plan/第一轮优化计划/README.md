# 第一轮优化计划历史归档

> **历史资料声明**：本文件保留第一轮优化阶段的路线图、任务状态、测试数字和当时结论，事实截止日期为 2026-08-20。它不再是当前任务状态入口，也不代表当前生产就绪度。
>
> 当前工程状态请以 [My_doc 当前入口](../../README.md)、[R2 计划与收口](../../plan_todo/README.md) 和 [项目交付材料](../../delivery/README.md) 为准。R2-00～R2-06 已于 2026-09-04 完成并冻结；本文件中的 02B、旧测试快照和“下一步”仅保留作历史追溯。
>
> **维护规则（历史语境）**：以下状态变化、owner、updated、依赖、命令/环境/结果均是当时记录；不要将本文件的历史 `mitigated`、`pending` 或任务顺序当作当前待办。


## 阅读顺序与文档分类

本目录索引见 [上级 README](../../README.md)。

1. **实时状态**：先读本 README，再进入对应的 00、00A、01～05 计划卡；本文件之外不维护第二份实时完成率。
2. **当前规范**：已完成 [00A](./00A-documentation-baseline-and-source-governance.md) 校准的 `docs/` 文档才可作为当前契约说明；发生冲突时仍须以当前代码、实际验证和批准决策为准。
3. **历史快照**：已归档至 [post_plan](../)（`TASK_TRACKER.md`、`优化方案.md`、`优化实施计划.md`、`开发执行计划.md`）；本文件下方 T-01～T-13 同为历史收尾证据，不代表当前生产就绪度。
4. **决策记录**：用于保存业务选项和结论，不承担实时进度统计；未决事项使用 `needs_decision`。

## 下一步动作（2026-08-20）

- **02A 已完成**：`smoke_local.py --self-host` 得到 `ALL_02A_SMOKE_CHECKS_PASS`。
- **下一步做 02B-VM**：本机 Ubuntu Server 虚拟机 + Docker Engine（不是 Desktop）。推荐 2～4 vCPU / 4GB / 40GB。
- **02B-Cloud 可选**：虚拟机被飞连拦截或资源不够时再上云。两条 Docker 路径完成其一即可把 02 标 `done`。
- 细节见 [02 计划卡](./02-docker-seed-e2e.md)。

## 当前活动计划

| ID | 优先级 | 状态 | 负责人 | 计划 | 进入条件/说明 |
|----|--------|------|--------|------|---------------|
| 00 | P0 | done | 待认领 | [执行治理与路线图维护](./00-execution-governance.md) | 已采用；对后续任务持续生效 |
| 00A | P0 | done | 待认领 | [文档基线校准与状态源治理](./00A-documentation-baseline-and-source-governance.md) | 2026-08-19 校准完成；事实矩阵 v2026-08-19-00A |
| 01 | P0 | done | 待认领 | [已送达货物重规划完整性](./01-delivered-goods-replan-integrity.md) | 2026-08-19 完成；645 passed |
| 03 | P1 | done | 待认领 | [前后端订单六态契约统一](./03-order-status-contract.md) | 2026-08-19 完成；656 passed |
| 02 | P0 | mitigated | 待认领 | [全新种子库端到端验收（本地 smoke + 虚拟机/云服务器 Docker）](./02-docker-seed-e2e.md) | 02A 已通过；02B-VM 与 02B-Cloud 完成其一即可 done |
| 04 | P1 | done | 待认领 | [`time_window` 数据契约决策](./04-time-window-contract-decision.md) | 2026-08-19 方案 A；678 passed |
| 05 | P1 | done | 待认领 | [路线分页契约与查询效率](./05-route-pagination-and-query-efficiency.md) | 2026-08-19 完成；664 passed |

**依赖主链**：`00`(已采用) `→ 00A`(已校准) `→ 01 → 03 → {02, 04, 05}`。02A 已完成。02B 在本地虚拟机或云服务器跑同一套 Compose smoke，完成其一即可；个人秋招项目，无公司许可门禁。04 / 05 已完成。本表仍保留原依赖编号。

## 当前事实摘要（事实矩阵 v2026-08-19-00A）

| 事实域 | 当前证据 | 状态/限制 |
|--------|----------|-----------|
| 后端测试 | 2026-08-19，`src/backend`，`python -m pytest -q -p no:cacheprovider`：678 passed、209 warnings | 04 本轮实测；05 为 664，03 为 656，01 为 645，此前既有 635，T0-T6 历史 626 |
| 前端构建 | 2026-08-19，类型检查与生产构建通过 | 既有验证；仅有第三方 pure-annotation 警告 |
| 本地无容器 smoke（02A） | 2026-08-20 `python scripts/smoke_local.py --self-host --port 18000 --temp-dir tmp/logistics-02a` → `ALL_02A_SMOKE_CHECKS_PASS`；开发库 LastWriteTime 未变 | done；仅证明本机进程主链路 |
| Docker E2E（02B-VM / 02B-Cloud） | 本机无 Docker Desktop；改走本地 Ubuntu VM 或可选云主机的 Docker Engine | pending；完成其一即可；配置/镜像文件存在不等于验收通过 |
| 到货确认权限 | `arrival_confirm.py` 三端点 `require_dispatcher`（dispatcher/admin） | 当前规范已与代码一致 |
| 状态契约 | 前后端/Mock/种子共用 `unassigned/assigned/in_transit/signed/exception/closed`；本地库 100 条 `pending` 已回填为 `unassigned`；goods `delivered` 终态不被重规划回退 | 03 已收口；未知状态不静默映射 |
| 算法能力 | L1、2-opt stub、load_rate 恒定 0.5、DeepSeek 策略 mitigated | 未完成项不得被历史 T-07“收尾”措辞覆盖 |

---

## 历史运行评估摘要（2026-08-11～12）

> 本节记录当时的 626 测试与 83 端点盘点，不是当前基线；当前数字见上方事实摘要。

| 当时结论 | 当时说明 |
|----------|----------|
| 后端可运行 | venv 安装 49 包成功；uvicorn 正常启动；health/login/orders/vehicles/nodes API 实测 OK |
| 测试全绿 | `pytest` 626/626 通过（~2min） |
| 前端可构建 | vue-tsc + vite build 成功，lockfile 与 package.json 一致 |
| API 端点盘点 | 当时记录为 83 个（与当时 README 声称一致） |
| **Docker 未验证** | 本机未安装 Docker，镜像构建/`docker compose up` 无法本地验证 |

---

## T-01～T-13 历史收尾快照（2026-08-14）

> 下述编号属于上一轮问题收尾，不等同于上方当前活动计划 00、00A、01～05；其中 ✅ 只表示当时任务按当时口径完成，不能推出当前生产就绪。

### 当时进度说明

> 上轮会话（2026-08-13）因权限分类器限流中断的**验证与提交**，本轮已全部完成。

**已完成并提交（5 个 commit，main 分支）**：

| Commit | 内容 |
|--------|------|
| `8a00c9f` | fix: init 脚本补建 admin 种子账号（init_users + init_demo_data + proced_problem/001 真实验证数据） |
| `846ba3f` | fix: arrival_confirm 与 ERP webhook 补鉴权及角色校验（含 9 个新测试） |
| `2e0c6e8` | fix: AI 建议上下文按 unassigned 查询待调度订单（ai.py） |
| `0e9e089` | fix: 审计中间件记录操作者 current_user（dependencies.py） |
| `f289b68` | chore: requirements.txt 转 UTF-8（原 UTF-16LE） |

**验证结果**：

- `requirements.txt`：UTF-16LE → UTF-8（`file` 确认 `UTF-8 text`），`pip install --dry-run -r` 解析通过
- T-01：临时库重跑双 init 脚本 → `users` 表 admin count=1 → `admin/123456` 登录 JWT payload `role=admin` ✅
- T-02/T-07：定向测试 15 passed；全量 `pytest` **635 passed**（原 626 + 新增 9）
- T-06：`.env` 已替换为随机 `JWT_SECRET`；`DEEPSEEK_API_KEY` 前导空格已删（gitignored 本地文件）

**仍 🚫 阻塞**：T-04 Docker 镜像构建验证（本机无 Docker，需装有 Docker 的机器执行）；T-07 剩余 4 项算法级边界（L1 容量检查、2-opt stub、load_rate 恒定、`algorithm="deepseek"` 未实现）留待后续排期。

---

## 历史任务清单（按当时优先级）

### P0 — 必须先修（阻碍真实部署/演示）

| # | 状态 | 事项 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| [T-01](#t-01-补建-admin-种子账号) | ✅ | **补建 admin 种子账号** | `src/backend/scripts/init_users.py`、`init_demo_data.py` | 双脚本补建 admin；临时库验证 admin count=1 + `admin/123456` 登录 JWT role=admin；[proced_problem/001](../../../proced_problem/001-seed-users-missing-admin.md) 已补真实验证数据并置 fixed；commit `8a00c9f` |
| [T-02](#t-02-修复鉴权中风险) | ✅ | **修复鉴权中风险**（arrival_confirm 无鉴权 + ERP webhook JWT 回退无角色检查） | `api/arrival_confirm.py`、`api/erp_webhook.py`、`core/permissions.py` | 3 端点 `require_dispatcher`；webhook 回退校验 role∈{dispatcher,admin}；新增 9 个鉴权测试；定向 15 passed + 全量 635 passed；commit `846ba3f` |
| [T-03](#t-03-修复-envlocal-拼写错误) | ✅ | **修复 `.env.local` 拼写错误** | `src/frontend/.env.local:8` | `VITE_USE_MOCK_AUTH=fasle` → `false`（本地文件，gitignored 不提交） |
| [T-08](#t-08-种子订单状态枚举漂移pending--unassigned) | ✅ | **种子订单状态枚举漂移**（pending → unassigned） | `src/backend/scripts/init_demo_data.py:340` | 100 条种子**订单**写 `status="pending"`，订单状态机/业务代码统一 `unassigned` → 调度/打包/派单/路径全链路阻塞；货物 `pending_pack` 为合法状态不改（ISSUE-002）；[proced_problem/005](../../../proced_problem/005-seed-order-status-enum-drift.md) |
| [T-09](#t-09-manager-角色无权限映射) | ✅ | **manager 角色无权限映射** | `src/backend/core/permissions.py` | `ROLE_PERMISSIONS` 无 `manager` 键 → `get_user_permissions` 返回空列表，仓库写端点全 403（ISSUE-001）；[proced_problem/004](../../../proced_problem/004-manager-role-missing-permission-map.md) |

### P1 — 应修（可复现性/安全加固）

| # | 状态 | 事项 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| [T-04](#t-04-docker-镜像构建验证) | 🚫 | **Docker 镜像构建验证** | `Dockerfile.backend`、`Dockerfile.frontend`、`docker-compose.yml` | 本机未安装 Docker，无法本地执行；需在装有 Docker 的机器上跑 `docker compose up -d` + 初始化脚本 + 冒烟 |
| [T-05](#t-05-requirementstxt-编码规范化) | ✅ | **requirements.txt 编码规范化** | `src/backend/requirements.txt` | 已 UTF-16LE → UTF-8（`file` 确认 `UTF-8 text`），`pip install --dry-run -r` 解析通过；commit `f289b68` |
| [T-06](#t-06-生产密钥检查) | ✅ | **生产密钥检查**（JWT_SECRET 占位符 + DeepSeek key 前导空格） | `src/backend/.env` | `.env` 已替换随机 `JWT_SECRET`；`DEEPSEEK_API_KEY` 前导空格已删（gitignored 本地文件）。注意：dev 实际加载 `.env.dev`（key 空属预期降级），`.env` 为防御性修复 |
| [T-10](#t-10-auth-expiresin-硬编码) | ✅ | **auth expires_in 硬编码** | `src/backend/api/auth.py:59` | 返回 `86400` ≠ `settings.JWT_EXPIRE_SECONDS`(172800)，前端过期倒计时错位 2 倍（ISSUE-003）；[proced_problem/006](../../../proced_problem/006-auth-expires-in-hardcoded.md) |
| [T-11](#t-11-algorithmdeepseek-未实现) | ⚠️ | **algorithm="deepseek" 未实现** | `src/backend/algorithms/factory.py`、`global_schedule.py:342` | 策略工厂仅注册 greedy/dummy，入口只接受 traditional，与 docs 功能清单不符（ISSUE-005）；[proced_problem/008](../../../proced_problem/008-deepseek-algorithm-not-implemented.md) |

### P2 — 已自记录的遗留边界（docs/08，低/中）

| # | 状态 | 事项 | 来源 |
|---|------|------|------|
| [T-07](#t-07-已文档化遗留边界docs08非阻塞) | 🔄 | 8 项遗留边界（见下节），本次完成 4 项 quick wins | docs/08 | 已完成的 4 项：arrival_confirm / ERP 角色（T-02）、审计 current_user + AI 上下文 unassigned（commit `0e9e089` / `2e0c6e8`）；剩余 4 项算法级边界（L1 容量检查、2-opt stub、load_rate 恒定、`algorithm="deepseek"` 未实现）留待后续排期 |
| [T-12](#t-12-ordercreate-timewindow-未校验) | ✅ | **OrderCreate time_window 未校验** | `src/backend/schemas/order.py:18` | 2026-08-19 方案 A：自由文本时效要求，strip/非空/无控制字符/≤32；不启用 `HH:MM-HH:MM`；[proced_problem/007](../../../proced_problem/007-ordercreate-time-window-unvalidated.md) |
| [T-13](#t-13-残留-debug-print) | ✅ | **schedule_service 残留 DEBUG print** | `src/backend/services/schedule_service.py:318,319,425` | 裸 `print` 泄漏内部状态到 stdout，`[ERROR]` 分支未走 `logger.error`（ISSUE-006）；[proced_problem/009](../../../proced_problem/009-residual-debug-print.md) |

---

## 历史任务详情

### T-01 补建 admin 种子账号

**现象**：按 docs/06 初始化后，`admin/123456` 登录 401；README/docs/06 演示账号表与实现不符。

**修复**：在 `init_users.py` 增加 admin 分支（`role="admin"`，`display_name="管理员"`），与 dispatcher/manager 并列；同步核对 init_demo_data.py。可复用现成 `get_password_hash`。

**验证**：重跑 init 脚本 → `SELECT count(*) FROM users WHERE role='admin'` = 1 → `admin/123456` 登录返回 JWT（payload 含 `role=admin`）→ 调仅 admin 端点过权限校验。

**收尾**：修复后更新 [proced_problem/001](../../../proced_problem/001-seed-users-missing-admin.md) 状态 `open → fixed`，补验证数据。

---

### T-02 修复鉴权中风险

**2a. `arrival_confirm` 3 个端点无鉴权**（[api/arrival_confirm.py](../../../src/backend/api/arrival_confirm.py)）
- 现状：`confirm-arrival`、`confirm-arrival-batch`、`arrival-packages` 仅 `Depends(get_db)`，任何人可确认送达/领取包裹。
- 修复：加 `Depends(require_permission(...))` 或 `require_role("dispatcher")`，与开通权责匹配；补 403 测试。

**2b. ERP webhook JWT 回退无角色检查**（[api/erp_webhook.py:39-59](../../../src/backend/api/erp_webhook.py)）
- 现状：`ERP_API_KEY` 为空时，回退 JWT 只验 `sub` 存在，不验角色 → 任意有效 JWT 即可创建订单。
- 修复：回退分支校验 `payload["role"]` 为 dispatcher（或引入 `require_permission` 语义）；补测试。

---

### T-03 修复 `.env.local` 拼写错误

`src/frontend/.env.local:8` → `VITE_USE_MOCK_AUTH=fasle` 改为 `false`。当前值不是 `"true"` 等效关闭 Mock（行为恰好正确），但它与注释意图（默认 Mock）相反，且今后任何人按注释期待行为会踩坑。

验证：`npm run dev` 确认登录走真实后端（或按注释意图改为 true 验证 Mock 登录）。

---

### T-04 Docker 镜像构建验证

需 Docker 环境：
1. `docker compose up -d --build`
2. `docker exec -it logistics-backend python scripts/init_demo_data.py`
3. 访问 `http://localhost:8080` 冒烟前端
4. `http://localhost:8000/api/health` 冒烟后端
5. 确认 init 后 admin 登录可用（依赖 T-01）

**风险点**：requirements.txt 为 UTF-16LE，Linux 下 `pip install -r` 依赖 pip 的 BOM 自动探测；转 UTF-8（T-05）后可消除。

---

### T-05 requirements.txt 编码规范化

`src/backend/requirements.txt` 当前为 UTF-16LE（`file` 命令确认）。pip 能靠 BOM 探测解析，但：任何按 UTF-8 读取该文件的工具/Git 冲突合并会坏。转 UTF-8（LF）+ 确认无乱码后提交。转换后重新 `pip install -r` 验证可解析。

---

### T-06 生产密钥检查

- `JWT_SECRET`：`.env` 中为占位符 `请替换为随机长字符串`，生产必须更换（docs/05 已要求）。
- **`DEEPSEEK_API_KEY` 前导空格**：`.env:15` 为 `DEEPSEEK_API_KEY= ark-...`（`=` 后有空格）。pydantic-settings 会不会 trim 需实测——若不平，key 会带空格 → DeepSeek 401 → health 显示 `ai_service: degraded`（当前实测正是 degraded，需排查是否为空格所致）。
  - 快速验证：`from config.settings import settings; print(repr(settings.DEEPSEEK_API_KEY))`

---

### T-07 已文档化遗留边界（docs/08，非阻塞）

| 严重度 | 边界 | 说明 |
|--------|------|------|
| 低 | L1 容量检查维度 | 读 DB 全局 packed 量而非本次调度分配量；`max_storage_time` 体积×小时 等价死代码 |
| 低 | 2-opt stub | `route_planning.py` 2-opt 不执行实际交换，路线优化仅靠贪心初始解 |
| 低 | load_rate 恒定 0.5 | 分母用车辆 capacity（包裹数）而非实际体积，跨候选不变 |
| 低 | 审计中间件 user 未设置 | ✅ fixed（commit `0e9e089`）：`get_current_user` 写入 `request.state.current_user` |
| 中 | AI 建议上下文 Bug | ✅ fixed（commit `2e0c6e8`）：`_build_context` 改为查 `status="unassigned"` |
| 低 | `algorithm="deepseek"` 未实现 | 策略工厂只注册 greedy/dummy |
| 中 | ERP webhook 角色检查 | ✅ fixed（commit `846ba3f`）：JWT 回退校验 role∈{dispatcher,admin}，见上 T-02b |

---

### T-08 种子订单状态枚举漂移（pending → unassigned）

**现象**：`init_demo_data.py` 生成 100 条**订单** `status="pending"`（第 340 行），而订单状态机（`ORDER_TRANSITIONS` 起点 `unassigned`）、`order_service.create_order`、`ai._build_context` 统一用 `unassigned`。导致 `GET /api/orders` 列表 status 全为 `pending`、AI 待调度计数错误（100→0）、`POST /api/schedule/global`(traditional) 返回 `40001 未找到未打包订单`——调度/打包/派单/路径全链路阻塞。注意：种子货物 `status="pending_pack"`（第 358 行）是货物状态机的**合法起点**，无需改动。

**修复**：`init_demo_data.py` 订单 `status="pending"` → `"unassigned"`（货物 `pending_pack` 保持不变）；若历史库已有 `pending`，补回填 `UPDATE orders SET status='unassigned' WHERE status='pending';`。

**验证**：全量 `pytest` 635 passed，0 failed。✅

**记录**：[proced_problem/005](../../../proced_problem/005-seed-order-status-enum-drift.md)（status: fixed）

---

### T-09 manager 角色无权限映射

**现象**：`init_users.py` 创建 `role="manager"` 账号，但 `core/permissions.py` 的 `ROLE_PERMISSIONS` 键为 `{admin, dispatcher, viewer, warehouse_operator}`，无 `manager` → `get_user_permissions` 走 `.get(user.role, [])` 返回空列表，manager 调仓库写端点全 403。

**修复**：方案 A——`permissions.py` 增加 `WAREHOUSE_OPERATOR_PERMISSIONS` 常量，`warehouse_operator` 和 `manager` 均引用该常量，避免两处漂移。

**验证**：`manager perms == warehouse_operator perms == 7`；全量 `pytest` 635 passed。✅

**记录**：[proced_problem/004](../../../proced_problem/004-manager-role-missing-permission-map.md)（status: fixed）

---

### T-10 auth expires_in 硬编码

**现象**：`api/auth.py:59` 登录返回 `"expires_in": 86400`（硬编码），而 JWT 实际 exp 由 `settings.JWT_EXPIRE_SECONDS` 计算（dev 下 172800），前端过期倒计时错位 2 倍。

**修复**：`api/auth.py:59` 改为 `"expires_in": settings.JWT_EXPIRE_SECONDS`。

**验证**：`settings.JWT_EXPIRE_SECONDS` → `172800`；全量 `pytest` 635 passed。✅

**记录**：[proced_problem/006](../../../proced_problem/006-auth-expires-in-hardcoded.md)（status: fixed）

---

### T-11 algorithm="deepseek" 未实现

**现象**：`POST /api/schedule/global` 传 `{"algorithm":"deepseek"}` 返回 `40001 阶段3仅支持 traditional`；`algorithms/factory.py` 的 `_GLOBAL_STRATEGIES` 只注册 `greedy`/`dummy`，与 docs 功能清单不符。

**修复（短期缓解）**：`schedule_service.py` 新增 `SUPPORTED_ALGORITHMS = ("traditional",)`，`create_global_schedule` 在调用策略前校验，未知算法返回 `code=40000`（参数错误）+ 支持列表；`api/schedule.py` schema 描述更新。`DeepSeekScheduleStrategy` 完整实现留待后续排期。

**验证**：`{"algorithm":"deepseek"}` → `code=40000`；`{"algorithm":"traditional"}` → 正常 draft；全量 `pytest` 635 passed。✅

**记录**：[proced_problem/008](../../../proced_problem/008-deepseek-algorithm-not-implemented.md)（status: mitigated）

---

### T-12 OrderCreate time_window 未校验

**现象**：`schemas/order.py:18` `OrderCreate.time_window: str` 无 validator。但 ISSUE-004 建议的严格 `HH:MM-HH:MM` 正则与代码库实际契约冲突——`time_window` 是自由文本"时效要求"，合法值含 `"全天"`、`"2026-06-15 全天"`、`"2026-06-20 9:00-18:00"` 等（见 `tests/conftest.py`、`test_orders.py`、`init_demo_data.py:339`）；全链路无解析起止时间做 ETA/SLA 计算；`core/validators.py:validate_time_window` 为死代码。

**结论**：2026-08-19 选定方案 A 并落地——保留自由文本「时效要求」，只做 strip / 非空 / 控制字符 / 长度≤32；不启用 `HH:MM-HH:MM`，不拆 start/end。

**记录**：[proced_problem/007](../../../proced_problem/007-ordercreate-time-window-unvalidated.md)（status: fixed）

---

### T-13 残留 DEBUG print

**现象**：`services/schedule_service.py:318-319` 两条 `[DEBUG]` print、`:425` 一条 `[ERROR]` print，绕过统一 logging 向 stdout 泄漏内部状态。

**修复**：删除 318-319 行 DEBUG print；`:425` 改 `logger.error("get_global_schedule failed: %s", e)`（模块顶部 `import logging; logger = logging.getLogger(__name__)`）。

**验证**：触发调度请求，stdout 无 DEBUG 行。

**记录**：[proced_problem/009](../../../proced_problem/009-residual-debug-print.md)（status: fixed）

---

## 状态图例

| 图标 | 含义 |
|------|------|
| ⬜ | pending |
| 🔄 | in_progress |
| ✅ | done |
| 🚫 | blocked（备注写原因） |
| ⚠️ | mitigated（短期缓解，完整方案待排期） |
| 🔍 | needs_decision（需业务/契约决策，不计为完成） |

## 当前执行顺序

1. **00 — 执行治理**：采用状态、证据、分支和回滚规则。
2. **00A — 文档基线校准**：先治理过时记录、内容冲突和证据缺漏；完成前不关闭后续业务计划。
3. **01 — delivered 重规划完整性**：保护终态数据与失败回滚。
4. **03 — 订单六态契约**：统一后端、前端、Mock、种子和迁移语义。
5. **02A 已完成**。下一步 **02B-VM 本地虚拟机 Docker**（首选）；**02B-Cloud** 可选。二者完成其一即可把 02 标 `done`。

每次状态变化均更新本表和对应计划卡；完成必须填写日期、owner、Commit/PR、验证命令/环境/结果和残留问题。非平凡故障按 `proced_problem` 模板记录，已有问题优先更新原记录。

### 历史执行顺序（T-01～T-13）

以下仅保留 2026-08-14 当时的推进语境，不再作为当前排期：
1. **T-08（种子状态）** 最先——单点阻塞调度/打包/派单/路径全链路，且改动最小（改两处状态枚举）。
2. **T-09（manager 权限）** 其次——演示/部署角色权限失效，与 T-08 同属 P0。
3. **T-10（expires_in）**、**T-11（deepseek）** P1 回归完善。
4. **T-12（time_window）**、**T-13（print）** P2 顺手清。
5. **回归**：修复后在**全新库**上重跑 `init_users.py` + `init_demo_data.py`，重点回归 TC-040 调度端到端，并补一条「针对真实种子数据的冒烟测试」堵住"测试全绿但演示失败"的假象。

**历史（T-01~T-07）**：P0（T-01 → T-02 → T-03）已完成；P1（T-04 → T-05 → T-06）中 T-04（Docker）仍阻塞；P2（T-07）剩余 4 项算法级边界留待后续排期。

当时每完成一项：更新历史表 + `proced_problem` 相应记录（`open → fixed`）+ 按 Git 协作规范提交。当前任务改按上方活动计划及证据门禁维护。

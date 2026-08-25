---
plan_id: "02"
title: 全新种子库端到端验收（本地 smoke + 虚拟机/云服务器 Docker）
status: mitigated
priority: P0
owner: 待认领
created: 2026-08-18
updated: 2026-08-20
depends_on: ["00", "01", "03"]
---

# 02 — 全新种子库端到端验收（本地 smoke + 虚拟机/云服务器 Docker）

> **项目性质**：个人秋招作品，与公司无关。仓库可放进自用 Linux 环境。
> **02A**：已于 2026-08-20 本机进程 smoke 通过，状态见下方完成记录。
> **02B Docker**：本机 Windows 不装 Docker Desktop（飞连仍可能把 Desktop 标违规）。改在 **本地 Linux 虚拟机** 装 Docker Engine 部署；**云服务器作为可选备选**。
> **验收硬约束**：`02` 标 `done` 只需 **02A +（02B-VM 或 02B-Cloud 二者完成其一）**。两条 Docker 路径业务标准相同，不必两条都做。
> **当前状态**：`mitigated`（仅 02A 完成）。任一 Docker 路径填好完成记录后即可改 `done`。

## 当前下一步

1. 在本机创建 Ubuntu Server 虚拟机，安装 Docker Engine + Compose（不是 Docker Desktop）。
2. 在虚拟机里克隆仓库，用 `docker compose -p logistics-smoke` 全新 volume 起栈。
3. 跑与 02A 相同的 `smoke_local.py --base-url`，再 `compose restart` 复查持久化。
4. 云服务器只作备选：虚拟机若因飞连拦截 Hypervisor / 本机资源不够再启用，不作为必做项。

## 来源证据与当前行为

- 历史 T-04 一直记录为 Docker 未验证，见 [README 历史快照](./README.md#t-01t-13-历史收尾快照2026-08-14)。
- [启动说明](../../docs/06-启动说明.md) 已有本机进程启动和 Compose 配置说明；容器启动后仍需手动初始化演示数据。
- [CI](../../.github/workflows/ci.yml) 只运行 pytest 与前端 build；[CD](../../.github/workflows/cd.yml) 构建镜像，但没有全新数据库业务 smoke。
- 2026-08-20：本机 Windows `docker --version` 为 command not found。飞连将 Docker Desktop（`Docker Desktop.exe` / `com.docker.desktop.exe` / `docker.exe`）标为违规。本机 **Windows 宿主仍不装 Desktop**；Docker 放到 Linux 客户机或云主机的 Engine。
- 2026-08-19 PR #1 已合入 `main`（`4d1fd64`）。01 / 03 / 04 / 05 已完成。
- 2026-08-20：`src/backend/scripts/smoke_local.py` 已落地；`--self-host` 在临时库上通过双初始化、HTTP 主链路与进程重启校验。
- 现有 `src/backend/scripts/test_p1_1_integration.py` 打的是默认开发库，且缺少确认打包 / 到货确认，不能当作验收脚本。

## 问题与目标

pytest 全绿不等于全新种子库上的真实 HTTP 主链路可跑。目标分两层：

1. **02A**（已完成）：本机进程方式证明业务主链路可重复通过。
2. **02B**：把同一套 HTTP smoke 迁到 Compose / 镜像栈，补上构建、网络、volume 与重启持久化。部署环境二选一：
   - **02B-VM（首选）**：本地 Linux 虚拟机 + Docker Engine
   - **02B-Cloud（可选）**：自用云服务器 + Docker Engine

## 路径对照

| 项 | 02A 本机无容器 smoke | 02B-VM 本地虚拟机 Docker | 02B-Cloud 云服务器 Docker |
|----|----------------------|--------------------------|---------------------------|
| 状态 | 已完成 | **下一步首选** | 可选备选 |
| 是否必须 | 已满足 | 与 Cloud **完成其一** | 与 VM **完成其一** |
| 环境 | Windows + Python | Ubuntu Server VM + Docker Engine | Linux 云主机 + Docker Engine |
| 数据 | 临时 SQLite；不碰开发库 | compose project `logistics-smoke` + 全新 volume | 同左 |
| 覆盖 | 双初始化、权限、主链路、进程重启 | 02A 业务项 + 镜像构建、Compose、Nginx、volume、重启 | 同 VM，另加安全组与公网密钥 |
| 不覆盖 | 镜像 / 容器网络 | Windows 宿主 Docker Desktop | 不在本机装 Desktop |
| 脚本 | `smoke_local.py --self-host` | 同一脚本 `--base-url` | 同一脚本 `--base-url` |

## 本地虚拟机配置

栈很轻（FastAPI + SQLite + Redis + Nginx），但 **前端镜像构建**（`node:22` + `npm ci` + `npm run build`）吃内存。按构建期估算，不要只按运行期给 1GB。

| 项 | 最低能跑 | **推荐（按此准备）** | 说明 |
|----|----------|----------------------|------|
| 宿主机 | Win11；内存 ≥ 8GB 才比较从容 | 16GB 更稳 | 宿主还要留 Windows / 飞连 / 浏览器 |
| 虚拟化 | VirtualBox 7 / VMware Workstation / Hyper-V | 已开通的那个用那个 | 先看飞连是否拦截虚拟化软件本身 |
| 客户机 OS | Ubuntu 22.04/24.04 **Server** | **Ubuntu 24.04 LTS Server** | 不要装桌面，省 1～2GB |
| vCPU | 2 | **2～4** | 构建前后端镜像时 2 核即可 |
| 内存 | 2GB（只跑已构建镜像，构建易 OOM） | **4GB** | 前端 build 建议 ≥ 4GB；桌面版则 6～8GB |
| 磁盘 | 20GB 动态盘 | **40GB 动态盘** | 系统 + 镜像 + volume；动态分配不一次占满 |
| 网卡 | NAT + 端口转发 | NAT 转发 **22 / 8000 / 8080**，或桥接 | **不要**转发 Redis `6379` |
| 共享目录 | 可选 | **不推荐当代码源** | VirtualBox 共享盘对 Docker 不稳；在 VM 内 `git clone` |
| 软件 | Docker Engine + Compose 插件 | 官方 `docker-ce` + `docker compose` | **不要**装 Docker Desktop |

飞连提示：若 VirtualBox / VMware / Hyper-V 也被标违规，不要硬装，改走 02B-Cloud。WSL2 里只装 Docker Engine 也可，但本卡默认完整 Linux VM，验收口径更接近云主机。

## 共用 HTTP 契约（所有 02B 环境同一套）

| 步骤 | 方法 / 路径 | 通过口径 |
|------|-------------|----------|
| 健康 | `GET /api/health` | 非 5xx，服务已就绪 |
| 三角色登录 | `POST /api/auth/login` | `admin` / `dispatcher` / `manager` |
| 身份 | `GET /api/auth/me` | JWT 角色匹配 |
| 种子巡检 | orders / goods / packages / vehicles / nodes | 关键实体存在；订单无非法 `pending` |
| F007 draft | `POST /api/schedule/global` | 返回 `schedule_code` |
| F021 确认打包 | `POST /api/schedule/confirm/{schedule_code}` | draft → active |
| F005 节点调度 | `POST /api/schedule/node-dispatch` | 产生批次 / 车辆任务 |
| F006 路线 | `POST /api/routes/plan` 或查询路线 | 路线可查 |
| 模拟配送 | `POST /api/simulation/deliver` | 可进入到货确认 |
| 到货确认 | `POST /api/simulation/confirm-arrival` | dispatcher/admin 可写；manager 403 |
| 重启后再查 | 复用业务编码 | 容器重启后数据仍在 |
| 前端入口 | `GET http://<vm或云>:8080` | Nginx 静态页可打开（Docker 路径加验） |

允许降级（DeepSeek / 地图 / Redis）须在 `meta` 或日志可见，不得当核心失败。

## 范围与非目标

- 范围：02B-VM 或 02B-Cloud 其一 + 已完成的 02A。
- Windows 宿主不装 Docker Desktop。
- 不在开发机现有 SQLite 或未知 volume 上清库。
- 不改 `.env.dev` 里的 `DATABASE_URL`。
- 02A 通过不得写成「Docker E2E 已完成」。
- 演示账号不要长期挂公网；云路径必须换强 `JWT_SECRET`，且不暴露 `6379`。

## 有序实施步骤

### 02A — 本机无容器 smoke

已完成，见文末完成记录。不要重跑去改开发库。

### 02B-VM — 本地虚拟机 Docker（首选）

1. 宿主机开启虚拟化（BIOS VT-x/AMD-V）。安装 VirtualBox / VMware / Hyper-V 之一。
2. 新建虚拟机：Ubuntu 24.04 Server，2～4 vCPU，**4GB 内存**，40GB 动态盘，NAT。
3. 端口转发（NAT 时）：主机 `2222→22`、`8000→8000`、`8080→8080`。不要转发 `6379`。
4. 客户机安装 Docker Engine（非 Desktop）：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-pip
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
# 重新登录后再检查
docker --version
docker compose version
```

5. 在 VM 内克隆仓库（不要用宿主共享文件夹当 build context）：

```bash
git clone <你的仓库 URL> ~/LogisticSystem
cd ~/LogisticSystem
```

6. 准备独立密钥后起专用项目（全新 volume）：

```bash
export JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose config
docker compose -p logistics-smoke up -d --build
docker compose -p logistics-smoke ps
```

7. 双初始化并确认幂等：

```bash
docker exec logistics-backend python scripts/init_users.py
docker exec logistics-backend python scripts/init_demo_data.py
docker exec logistics-backend python scripts/init_users.py
docker exec logistics-backend python scripts/init_demo_data.py
```

8. 跑与 02A 相同的 HTTP smoke。VM 内：

```bash
cd ~/LogisticSystem/src/backend
python3 -m pip install --user requests
python3 scripts/smoke_local.py --base-url http://127.0.0.1:8000
```

再访问 `http://127.0.0.1:8080`（或宿主 `http://127.0.0.1:8080`）确认 Nginx 前端。

9. `docker compose -p logistics-smoke restart` 后复查登录与已完成业务编码仍可查。
10. 记录 `docker version`、`compose ps`、镜像 ID、smoke 退出码、关键响应。失败记 `proced_problem`。
11. 清理前确认 project name；仅专用测试数据且明确确认后才 `down -v`。

### 02B-Cloud — 云服务器 Docker（可选）

虚拟机路径已通过就不必做。仅当 VM 不可用或想多一份公网演示时：

1. 选用 ≥ 2 vCPU / 4GB / 40GB 的 Linux 云主机（与 VM 推荐规格对齐；2GB 云主机可能构建 OOM）。
2. 安全组只放行 `22`、`8080`（按需 `8000`），不放行 `6379`。
3. 安装 Docker Engine + Compose，克隆仓库，后续命令与 02B-VM 第 6～11 步相同。
4. `JWT_SECRET` 不用仓库占位值；演示账号不长期挂公网。
5. smoke 可用 `http://127.0.0.1:8000`（SSH 登录后）或经 Nginx 的 `http://<公网IP>:8080`。

## 验收标准

`02` 标 `done` 当且仅当：**02A 已完成**，并且 **02B-VM、02B-Cloud 至少一条**满足下列 Docker 标准。另一条可保持 `pending` / 不做。

### 02A（已满足）

- 临时库上一键完成双初始化与核心 HTTP 链路。
- 无 5xx；非法 `pending` 为 0；开发库未被改写。

### 02B-VM 或 02B-Cloud（完成其一）

- 满足 02A 全部业务断言（同一 `smoke_local.py`）。
- 全新 volume 上构建、启动、双初始化、smoke、`compose restart` 后数据仍在。
- `8080` 前端可打开；容器日志无未处理异常、密钥泄漏或残留 DEBUG。
- Redis 未对宿主机局域网 / 公网暴露；`JWT_SECRET` 非占位值。
- 有带日期的环境说明（VM 规格或云厂商 / OS / Docker 版本）和镜像摘要。

## 验证命令

### 02A（已跑过，不必为 02B 重做）

```powershell
src\backend\.venv\Scripts\python.exe src\backend\scripts\smoke_local.py --self-host --port 18000 --temp-dir tmp\logistics-02a
```

### 02B-VM / 02B-Cloud（在 Linux 上）

```bash
docker --version
docker compose version
docker compose config
docker compose -p logistics-smoke up -d --build
docker compose -p logistics-smoke ps
docker exec logistics-backend python scripts/init_users.py
docker exec logistics-backend python scripts/init_demo_data.py
python3 src/backend/scripts/smoke_local.py --base-url http://127.0.0.1:8000
curl -I http://127.0.0.1:8080
docker compose -p logistics-smoke restart
python3 src/backend/scripts/smoke_local.py --base-url http://127.0.0.1:8000
docker compose -p logistics-smoke logs --no-color
docker compose -p logistics-smoke down
# 仅专用测试数据且明确确认后：docker compose -p logistics-smoke down -v
```

## 文档与问题记录同步

- 02B-VM / 02B-Cloud 谁先通过谁填完成记录；另一条注明「未做，因另一条已验收」。
- [README](./README.md) 在任一 Docker 路径通过后把 02 从 `mitigated` 改为 `done`。
- 历史 T-04 保留「当时本机未验证 Docker」；后继状态指向本卡。
- 启动说明区分：本机进程 / 本地 VM Compose / 云主机 Compose。

## 回滚与恢复

- 02B 失败：保留 `compose logs` 与镜像 ID，不删未知 volume。
- 虚拟机装失败或飞连拦截 Hypervisor：改走 02B-Cloud，不在 Windows 宿主安装 Docker Desktop。
- 严禁对未知或生产 volume 执行 `down -v`。

## 完成记录

### 02A 本地无容器 smoke

- 完成日期：2026-08-20
- 执行环境：Windows 11 10.0.26200；Python 3.13.3（`src/backend/.venv`）；端口 `18000`；临时库 `tmp/logistics-02a/logistics.db`
- Commit / PR：`c1c248e` / https://github.com/justtodo123/LogisticSystem_more/pull/2
- 命令 / 结果：`src/backend/.venv/Scripts/python.exe src/backend/scripts/smoke_local.py --self-host --port 18000 --temp-dir tmp/logistics-02a` → `ALL_02A_SMOKE_CHECKS_PASS`。覆盖双初始化（users=3 / orders=100 / pending=0）、三角色登录、种子巡检、F007 draft → F021 confirm → F005（`demo_mode=false`）→ F006 分页、`/simulation/deliver`、manager 到货确认 403、dispatcher 到货确认、停进程再拉起后调度/包裹仍可查。健康检查记录 `ai_service=degraded`。
- 开发库 `data/logistics.db` 是否被改写：否。跑前跑后均为 LastWriteTime `2026-08-19 22:52:10`、size `593920`
- 残留问题：DeepSeek 无 Key，健康检查降级（允许）。`GET /api/schedule/global/{code}` 详情不含 `status`，重启校验改查 `schedule_code` + packages + `status=active` 列表。

### 02B-VM 本地虚拟机 Docker

- 完成日期：待填写
- 执行环境：待填写（Hypervisor / 客户机 OS / vCPU / 内存 / 磁盘 / Docker / Compose）
- 镜像 SHA：待填写
- Commit / PR：待填写
- E2E 结果与证据：待填写

### 02B-Cloud 云服务器 Docker（可选）

- 完成日期：待填写 / 或注明「未做，02B-VM 已验收」
- 执行环境：待填写（云厂商 / OS / Docker / Compose）
- 镜像 SHA：待填写
- Commit / PR：待填写
- E2E 结果与证据：待填写
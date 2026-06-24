# DeepSeek 路径优化 - 智能物流平台

华中科技大学软件学院 2026 实训项目 · MVP 智能物流调度演示系统。

## 当前进度

- **阶段 6（模拟送达 F013-1）**：✅ 已完成（2026-06-17）
  - 实现 `POST /api/simulation/deliver` API，驱动货物/包裹/车辆/司机/订单状态流转
  - 支持自动触发L1重新打包（F021）
  - 支持自动触发第二次F005（L1→L2调度，异步执行）
  - 单元测试全部通过（56个测试）
  - 详见 [阶段 6 开发文档](My_doc/阶段6-模拟送达-开发文档.md)

- **阶段 4（节点间调度）**：已完成 F005 节点调度功能，支持包裹按重量拆分、部分分配、未分配包裹返回。详见 [阶段 4 开发文档](docs/MVP开发计划-后端.md#阶段-4节点间调度f005)。

## 文档

| 文档 | 说明 |
| --- | --- |
| [MVP 开发计划](docs/MVP开发计划.md) | 阶段总览与验收 |
| [P1 功能概览](docs/P1功能概览.md) | P1 功能清单与范围确认 |
| [P1 开发计划](docs/P1开发计划.md) | P1 分阶段任务与验收 |
| [P1 后端计划](docs/P1开发计划-后端.md) | P1 后端任务与联调 |
| [P1 前端计划](docs/P1开发计划-前端.md) | P1 前端任务与联调 |
| [后端开发计划](docs/MVP开发计划-后端.md) | 后端分阶段任务 |
| [前端开发计划](docs/MVP开发计划-前端.md) | 前端分阶段任务 |
| [开发规范](docs/开发规范.md) | 依赖与环境变量记录规范 |
| [环境配置说明](docs/环境配置说明.md) | 安装与启动 |
| [Git 协作规范](docs/Git协作规范.md) | 分支与 PR |
| [系统架构设计说明书](docs/architecture/系统架构设计说明书.md) | 架构与 API |
| [PRD](docs/prds/03产品需求文档(PRD)-V2.7.md) | 产品需求 |

## 快速启动（阶段 0 完成后）

```bash
# 后端
cd src/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000

# 前端
cd src/frontend
npm install
npm run dev
```

详细步骤见 [docs/环境配置说明.md](docs/环境配置说明.md)。

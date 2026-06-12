# DeepSeek 路径优化 - 智能物流平台

华中科技大学软件学院 2026 实训项目 · MVP 智能物流调度演示系统。

## 文档

| 文档 | 说明 |
| --- | --- |
| [MVP 开发计划](docs/MVP开发计划.md) | 阶段总览与验收 |
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

# 智能物流平台 · 前端

Vue 3 + TypeScript + Vite + Element Plus 单页应用。

## 项目状态

**MVP + P1 必做 + F015 方案解释** 已交付（2026-06-25）。详见 [根目录 README](../../README.md)。

## 快速启动

```bash
npm install
copy .env.example .env.local   # 联调/答辩：VITE_USE_MOCK_* 全 false
npm run dev                    # http://localhost:5173
npm run build                  # 生产构建校验
```

后端需先在 `src/backend` 启动 `uvicorn main:app --port 8000`（Vite 代理 `/api`）。

## 核心页面

| 路径 | 说明 |
| --- | --- |
| `/login` | 登录（P1-4 美化） |
| `/dashboard` | 调度工作台 + AI 助手 |
| `/arrival-confirm` | 节点到货确认（P1-08） |
| `/orders` | 订单管理（含 Excel 导入） |

## 目录结构

```text
src/
├── views/          # 页面
├── components/     # schedule / ai / detail / crud
├── composables/    # useGlobalSchedule、useAiExplain 等
├── api/            # Axios 封装与接口
├── stores/         # Pinia（auth）
├── utils/          # Mock 开关、格式化
└── layouts/        # MainLayout 侧栏布局
```

## 文档

- [P1 开发计划-前端](../../docs/P1开发计划-前端.md)
- [环境配置说明](../../docs/环境配置说明.md)
- [PRD V2.8 交付版](../../docs/prds/04产品需求文档(PRD)-V2.8-P1交付版.md)

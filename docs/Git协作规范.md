# Git 协作规范

| 字段 | 值 |
| --- | --- |
| **文档版本** | V1.0 |
| **创建日期** | 2026-06-09 |
| **适用团队** | 2 人（1 前端 + 1 后端） |
| **远程仓库** | https://github.com/vegetablebasket/LogisticSystem.git |
| **关联文档** | [MVP开发计划](./MVP开发计划.md) · [开发规范](./开发规范.md) · [环境配置说明](./环境配置说明.md) |

---

## 1. 目标

本规范用于约定两人在 GitHub 上的协作方式，做到：

- 代码不丢、可回溯
- 前后端并行开发少冲突
- 每个 MVP 阶段验收通过后再合入稳定分支
- 密钥与本地环境不进入版本库

---

## 2. 分支策略

### 2.1 分支说明

```text
main                          ← 稳定分支：阶段联调通过后的代码
├── backend/phase-0           ← 后端：阶段 0
├── backend/phase-1           ← 后端：阶段 1
├── ...
├── frontend/phase-0          ← 前端：阶段 0
├── frontend/phase-1          ← 前端：阶段 1
└── ...
```

| 分支 | 维护人 | 用途 |
| --- | --- | --- |
| `main` | 两人共同 | 可演示、可联调、可答辩的稳定版本 |
| `backend/phase-N` | 后端同学 | 第 N 阶段后端开发（**Git 分支名**，非目录路径） |
| `frontend/phase-N` | 前端同学 | 第 N 阶段前端开发（**Git 分支名**，非目录路径） |

> 代码目录为 `src/backend/`、`src/frontend/`，与分支命名 `backend/phase-N` 无关。

### 2.2 基本原则

1. **禁止**两人直接在 `main` 上长期并行开发。
2. **阶段内**：在各自分支上频繁 `commit` + `push`（不必等整个阶段结束）。
3. **阶段末**：联调通过后，通过 **Pull Request（PR）** 合并到 `main`。
4. 新阶段从**最新 `main`** 拉出分支，不要从过期分支继续叠代。

### 2.3 不推荐的做法

| 做法 | 原因 |
| --- | --- |
| 整个阶段只 commit 一次 | 难回溯、冲突集中爆发、易丢代码 |
| 本地合并 main 不上传 | 对方看不到进度 |
| 在 `main` 上 force push | 会覆盖对方历史 |
| 提交 `.env`、`*.db` | 泄露密钥或污染仓库 |

---

## 3. 目录与修改范围

为减少冲突，默认**只改自己负责目录**：

| 同学 | 主要目录 | 慎改目录 |
| --- | --- | --- |
| 后端 | `src/backend/` | `src/frontend/`、`docs/`（改前沟通） |
| 前端 | `src/frontend/` | `src/backend/`、`docs/`（改前沟通） |
| 两人 | `docs/`、`README.md`、`.gitignore` | 改前在群里说一声 |

**接口契约**以 [系统架构设计说明书 §6](./architecture/系统架构设计说明书.md) 与 Swagger 为准；后端改接口字段须通知前端。

---

## 4. 日常开发流程

### 4.1 开始工作前（两人相同）

```bash
git checkout main
git pull origin main
```

### 4.2 后端同学

```bash
# 首次进入某阶段
git checkout -b backend/phase-2

# 已在该阶段分支
git checkout backend/phase-2
git merge main          # 把 main 最新改动合进来（建议每次开发前做）

# 开发、自测（Swagger / Postman）...

git add .
git commit -m "feat(backend): 阶段2 订单 CRUD API"
git push -u origin backend/phase-2   # 首次 push 加 -u，之后可省略
```

### 4.3 前端同学

```bash
git checkout -b frontend/phase-2
# 或 git checkout frontend/phase-2 && git merge main

# 开发、自测...

git add .
git commit -m "feat(frontend): 阶段2 订单列表页"
git push -u origin frontend/phase-2
```

### 4.4 提交频率建议

| 时机 | 是否提交 |
| --- | --- |
| 完成一个小功能（如一个 API、一个页面） | ✅ 建议 commit |
| 当天收工前 | ✅ 必须 push 到远程 |
| 代码跑不通、半成品 | ⚠️ 可 commit 到分支，但注明 WIP；阶段末前须修到可联调 |
| 仅本地试玩、未保存 | ❌ 不要长期只放本地 |

---

## 5. 阶段结束：合并到 main

### 5.1 合并前置条件

满足 [MVP开发计划](./MVP开发计划.md) 中该阶段的**阶段产出检查项**，且：

- [ ] 本侧功能自测通过
- [ ] 与对方联调通过（该阶段若要求联调）
- [ ] 未提交 `.env`、`*.db`、`node_modules/` 等（见 §7）
- [ ] 新增依赖已更新 `requirements.txt` 或 `package.json` + `package-lock.json`（见 [开发规范](./开发规范.md)）

### 5.2 合并顺序（默认）

| 阶段类型 | 合并顺序 |
| --- | --- |
| 一般阶段 | **先后端 PR → 再前端 PR** |
| 阶段 3～5（核心链路） | 联调通过后，约定时间一起提 PR |
| 阶段 8 | 谁改谁先合，最后两人回归测试 main |

### 5.3 Pull Request 步骤

**后端（示例：阶段 2）**

1. 确认 `backend/phase-2` 已 push 到 GitHub。
2. 打开仓库 → **Pull requests** → **New pull request**。
3. Base：`main` ← Compare：`backend/phase-2`。
4. 标题示例：`阶段2：基础数据 API（后端）`。
5. 描述中写明：完成了什么、如何自测、是否影响前端。
6. 指派对方 **Review** → 通过后 **Merge pull request**。
7. 实训项目可用 **Merge commit**（保留合并记录）。

**前端（后端 PR 合并后）**

```bash
git checkout main
git pull origin main
git checkout frontend/phase-2
git merge main              # 同步刚合入的后端接口
# 本地再联调一次，解决冲突（若有）
git push origin frontend/phase-2
```

再提 PR：`main` ← `frontend/phase-2`，Review 后合并。

**两人同步**

```bash
git checkout main
git pull origin main
```

### 5.4 开启下一阶段

```bash
# 后端
git checkout main && git pull origin main
git checkout -b backend/phase-3

# 前端
git checkout main && git pull origin main
git checkout -b frontend/phase-3
```

---

## 6. Commit 信息规范

### 6.1 格式

```text
<type>(<scope>): <简短说明>

[可选正文]
```

| type | 含义 | 示例 |
| --- | --- | --- |
| `feat` | 新功能 | `feat(backend): 阶段3 全局调度 API` |
| `fix` | 修复 bug | `fix(frontend): 修复登录 401 未跳转` |
| `docs` | 文档 | `docs: 补充 Git 协作规范` |
| `refactor` | 重构 | `refactor(backend): 抽取 schedule_service` |
| `chore` | 构建/工具 | `chore: 更新 .gitignore` |

| scope | 说明 |
| --- | --- |
| `backend` | 后端改动 |
| `frontend` | 前端改动 |
| 可省略 | 仅改 docs、根目录配置时 |

### 6.2 示例

```text
feat(backend): 阶段4 F005 节点间调度与 dispatch_batches
feat(frontend): 阶段5 SVG 路线可视化组件
fix(backend): 修复 demo_mode 下第二次 F005 未执行
docs: 更新 MVP 阶段验收说明
```

---

## 7. 禁止提交的内容

以下已由 `.gitignore` 忽略，提交前请确认 `git status` 中**不要出现**：

| 类别 | 示例 |
| --- | --- |
| 环境变量与密钥 | `.env`、`src/backend/.env` |
| 数据库文件 | `*.db`、`*.sqlite`、`src/backend/data/logistics.db` |
| 依赖目录 | `node_modules/`、`.venv/`、`venv/` |
| 构建产物 | `src/frontend/dist/`、`__pycache__/` |
| IDE 本地配置 | `.cursor/`、`.idea/`（团队约定） |

若误提交密钥：**立即轮换密钥**，并用新 commit 从仓库移除（必要时联系老师处理历史记录）。

---

## 8. 冲突处理

### 8.1 预防

1. 开发前先 `git pull origin main` 并 `merge main` 到当前分支。
2. 不修改对方主责目录下的文件。
3. 改 `docs/` 或公共配置前先沟通。

### 8.2 已发生冲突时

```bash
git checkout backend/phase-2   # 或 frontend/phase-2
git merge main
# 打开冲突文件，搜索 <<<<<<< 标记，人工合并
git add .
git commit -m "merge: 解决与 main 的冲突"
git push
```

**原则**：

- `main` 上**已验收通过**的逻辑优先保留。
- 拿不准时两人语音/屏幕共享一起改，改完再联调一次。
- **禁止**未经对方同意对 `main` 执行 `git push --force`。

---

## 9. 阶段与 Git 对照表

| MVP 阶段 | 后端分支 | 前端分支 | 合并建议 |
| --- | --- | --- | --- |
| 0 工程初始化 | `backend/phase-0` | `frontend/phase-0` | 先后端，再前端 |
| 1 认证权限 | `backend/phase-1` | `frontend/phase-1` | 先后端，再前端 |
| 2 基础数据 | `backend/phase-2` | `frontend/phase-2` | 先后端，再前端 |
| 3 全局调度 | `backend/phase-3` | `frontend/phase-3` | 联调后合并 |
| 4 节点间调度 | `backend/phase-4` | `frontend/phase-4` | 联调后合并 |
| 5 路径与可视化 | `backend/phase-5` | `frontend/phase-5` | 联调后合并 |
| 6 模拟送达 | `backend/phase-6` | `frontend/phase-6` | 后端可先合 |
| 7 异常重规划 | `backend/phase-7` | `frontend/phase-7` | 联调后合并 |
| 8 AI 与收尾 | `backend/phase-8` | `frontend/phase-8` | 按改动先后合 |

---

## 10. 协作节奏建议

| 时机 | 动作 |
| --- | --- |
| 阶段开始 | 确认本阶段接口清单；后端更新 Swagger 并告知链接 |
| 阶段进行中 | 每 2～3 天短联调；各自 push 分支 |
| 阶段结束 | 打勾验收项 → 提 PR → 合并 main → 两人 `pull main` |
| 答辩前 | 确认 `main` 可一键启动；标签可选 `v0.1.0-mvp` |

---

## 11. 常用命令速查

```bash
# 查看状态
git status
git branch -a
git log --oneline -10

# 同步远程
git fetch origin
git pull origin main

# 撤销未暂存修改（慎用）
git checkout -- <file>

# 查看远程
git remote -v

# 首次关联远程分支
git push -u origin <分支名>
```

---

## 12. 首次协作检查清单

仓库克隆后，两人各执行一次：

- [ ] `git clone https://github.com/vegetablebasket/LogisticSystem.git`
- [ ] 配置 Git 用户名邮箱（本机 `git config`，勿改仓库级配置）
- [ ] 确认能 `git pull origin main`
- [ ] 从 `main` 拉出 `backend/phase-0` 或 `frontend/phase-0`
- [ ] 首次 push 成功
- [ ] 复制 `src/backend/.env.example` → `src/backend/.env`（不提交）

---

## 版本历史

| 版本 | 日期 | 修改内容 |
| --- | --- | --- |
| V1.0 | 2026-06-09 | 初版：分支策略、日常流程、PR 合并、冲突与禁止提交 |
| V1.1 | 2026-06-12 | 代码目录调整为 `src/backend`、`src/frontend` |

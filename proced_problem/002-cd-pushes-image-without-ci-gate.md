---
problem_id: "002"
slug: cd-pushes-image-without-ci-gate
date: 2026-08-14
tags: [ci-cd, github-actions, workflow, supply-chain, silent-gate]
severity: major
status: fixed
related_files:
  - .github/workflows/ci.yml
  - .github/workflows/cd.yml
related_pr: ""
---

# CD 工作流绕过 CI 直接推送镜像，未通过测试的代码也会发布

## 1. 症状（表现形式）

`.github/workflows/cd.yml` 用 `on: push: branches: [main]` 直接触发 `docker-build-push` job，与 CI 工作流（`.github/workflows/ci.yml`，包含 `backend-test` + `frontend-check` 两个 job）**没有任何依赖关系**。可观测后果：

- 每次 push 到 `main`，CD 立即构建并推送 `ghcr.io/<repo>-backend/frontend:latest` 与 `:<sha>` 镜像。
- 即使 CI 全红（pytest 失败 / vue-tsc 报错），镜像照推不误。
- cd.yml 第 1 行注释声称"CI 为分支保护必检项"，但那是 GitHub 仓库设置，**不在代码库内、无法由工作流本身保证**——只要仓库没配 branch protection，注释就是空话。

即"未通过 CI 的代码也能进入镜像仓库"，是一次静默的发布门禁失效。

## 2. 复现条件

只要以下条件同时成立，就能稳定复现：

1. 仓库未启用 branch protection（或未把 `CI` 设为 main 必检项）；
2. 向 `main` 推一个会让测试失败的提交；
3. 观察 Actions：`CI` 变红，但 `CD` 仍绿、仍成功推镜像。

## 3. 定位过程

**Step 1 — 通读两个工作流触发配置**：ci.yml `on: push/pr`，cd.yml `on: push: branches: [main]`。两者触发条件互不相干，cd.yml 内没有任何 `needs` 引用。

**Step 2 — 确认 `needs` 能否直接跨工作流引用**：`needs` 只能引用**同一 workflow 文件内**的 job id；跨文件的 CI/CD 依赖无法用 `needs: ci` 表达（会报 `job 'ci' not found`）。起初以为加一行 `needs: ci` 即可，**后来确认不可行**。

**Step 3 — 排查 GitHub 是否在代码层有强制手段**：分支保护是仓库配置（`Settings → Branches → Protect`），不随代码入库；唯一能随代码强制"CI 通过才推送"的机制是 `workflow_run` 事件（监听 CI 完成）或把 CI 改成 `workflow_call` 可复用工作流。

**Step 4 — 确认 `workflow_run` 的关键陷阱**：该事件下 `github.sha` 是默认分支 HEAD，**不是**触发 CI 的那个 commit；若 checkout 不显式指定 `ref: github.event.workflow_run.head_sha`，会构建到"CI 验证的 commit 之后的更新代码"，导致镜像与测试覆盖的代码错位。

## 4. 根因

CD 用独立的 `push` 触发、与 CI 无任何代码层依赖，发布门禁靠的是仓库端的分支保护设置（代码外、易漏配），而非随代码强制的 workflow 依赖。

## 5. 解决方案

改 [cd.yml](../.github/workflows/cd.yml)，用 `workflow_run` 让 CD 严格依赖 CI 成功完成：

1. 触发改为 `on: workflow_run: { workflows: ["CI"], types: [completed] }`。
2. job 加 `if: ${{ github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.head_branch == 'main' }}`——只放行"push 到 main 的 CI run 成功"这一种情况，PR 触发的 CI 完成不推镜像。
3. `actions/checkout` 加 `ref: ${{ github.event.workflow_run.head_sha }}`，镜像 tag 的 sha 也改用 `head_sha`，保证"构建的代码 = CI 验证的代码"。

备选方案（未采用）：把 CI 重构为 `workflow_call` 可复用工作流再由 CD 调用——改动面更大（CI 需重写触发结构），不符合"最小修改"。

## 6. 验证

| 维度 | 修复前 | 修复后 |
| --- | --- | --- |
| 触发条件 | push main 即触发，无视 CI | 仅 `workflow_run`（CI completed）触发 |
| 门禁 | 依赖仓库分支保护设置（代码外） | `if: conclusion == 'success' && head_branch == 'main'`（代码内） |
| 构建代码 | 默认分支 HEAD | 显式 `checkout ref: head_sha` = CI 验证的 commit |
| CI 红时的 CD | 仍推送 | 不推送（conclusion != success 直接 skip） |

（工作流配置无本地可跑环境，改动通过语法走查 + GitHub Actions 文档语义核对确认；需在真实仓库 push 一次观察 `CD` 是否变为 `skipped`/仅在 CI 绿后触发。）

## 7. 通用经验

1. **发布门禁要随代码强制，不能只靠平台设置**：branch protection 是"代码外的开关"，会漏配；`workflow_run` / `workflow_call` / 同文件 `needs` 才是可入库、可 review 的依赖。
2. **`needs` 只能跨同文件 job，不能跨 workflow 文件**——想串起两个 `.yml`，用 `workflow_run` 事件或 `workflow_call` 可复用工作流。
3. **`workflow_run` 下 checkout 必须显式 `ref: head_sha`**：默认 checkout 的 `github.sha` 是默认分支 HEAD，会构建到 CI 验证之后的代码，造成"测的是一版、发的是另一版"的错位。
4. **镜像 tag 的 commit 标识要与实际构建的代码一致**：用 `github.event.workflow_run.head_sha`，而不是 `github.sha`。

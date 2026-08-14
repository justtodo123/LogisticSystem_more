# 问题记录库（proced_problem/）

> 记录项目开发中实际遇到的问题：症状、定位过程、根因与修复。目的是积累工程直觉，可复盘、可检索。

## 为什么叫"proced_problem"

"proced" = **Pro**blem **Rec**ord**ed** — 每一个被踩过、定位出来的问题，而不是未发生的理论风险。已经过一遍完整的问题解决闭环。

## 目录结构

```
proced_problem/
├── README.md              # 本导航文件
├── _template.md            # 记录模板
└── {序号}-{简短slug}.md    # 单条问题记录
```

## 记录列表

| 序号 | 标题 | 日期 | 标签 |
| --- | --- | --- | --- |
| 001 | [种子脚本缺失 admin 用户，文档声明的 admin/123456 登录失败](001-seed-users-missing-admin.md) | 2026-08-12 | seed-data, init-script, docs-drift, silent-failure, auth |
| 002 | [CD 工作流绕过 CI 直接推送镜像，未通过测试的代码也会发布](002-cd-pushes-image-without-ci-gate.md) | 2026-08-14 | ci-cd, github-actions, workflow, supply-chain, silent-gate |

## 如何新增记录

1. 复制 `_template.md`，按 `{序号}-{slug}.md` 命名
2. 填写各章节：症状 → 定位过程 → 根因 → 修复 → 验证 → 经验
3. 更新本 README 的记录列表
4. 触发方式：手动编写，或用 `problem-record` skill 辅助模板填写

## 关联

- 项目理解说明：[CLAUDE.md](../.claude/CLAUDE.md)
- 优化点与已知边界：[docs/08-优化点说明.md](../docs/08-优化点说明.md)

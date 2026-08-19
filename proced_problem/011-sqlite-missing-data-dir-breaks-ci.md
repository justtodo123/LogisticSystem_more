---
problem_id: "011"
slug: sqlite-missing-data-dir-breaks-ci
date: 2026-08-19
tags: [ci, sqlite, test-isolation, startup, silent-env-drift]
severity: major
status: fixed
related_files:
  - src/backend/config/database.py
  - src/backend/tests/api/conftest.py
  - src/backend/tests/api/test_health.py
related_pr: "https://github.com/justtodo123/LogisticSystem_more/pull/1"
---

# CI 空仓库下 SQLite 无法打开 data/logistics.db，API 测试 setup 成片失败

## 1. 症状（表现形式）

GitHub Actions 后端 pytest 失败。`TestClient` 进入 lifespan 时 `init_db()` 报 `sqlite3.OperationalError: unable to open database file`。本机 Windows 全量测试通过。

## 2. 复现条件

1. 干净目录，不存在 `src/backend/data/`
2. 默认 `DATABASE_URL=sqlite:///./data/logistics.db`
3. 运行依赖 `tests/api/conftest.py` 的 `client` fixture 的 API 测试

本机通常已有 `data/`（跑过演示库），所以本地全绿、CI 全红。

## 3. 定位过程

- CI 日志（2026-08-11，626 collected）在 `client` fixture 第 35 行 `TestClient(app)` 处失败
- 请求层已覆盖 `get_db` 为内存库，但 startup 仍使用模块级文件引擎
- SQLite 不会自动创建父目录；`*.db` 被 gitignore，CI 没有 `data/`

## 4. 根因

应用初始化依赖“父目录已经存在”。测试只替换了请求会话，没有隔离 startup 用的引擎。

## 5. 解决方案

- `ensure_sqlite_parent_dir`：打开文件库前创建父目录
- API `client` fixture：startup/`init_db` 改走独立内存库
- `test_health.py` 改为使用同一 fixture，避免模块级 `TestClient` 触发文件库启动

## 6. 验证

- 新增 `test_database_sqlite.py`
- 定向跑 API `client` 相关测试
- 全量 pytest 与 CI 复跑

## 7. 通用经验

覆盖 `get_db` 不等于隔离 startup。文件型 SQLite 必须自己创建父目录。本地残留数据目录会掩盖 CI 空仓库问题。

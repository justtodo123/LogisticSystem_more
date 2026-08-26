---
problem_id: "012"
slug: logger-exception-leaks-rollback-message
date: 2026-08-26
tags: [logging, security, sqlalchemy, rollback, error-contract]
severity: major
status: fixed
related_files:
  - src/backend/config/database.py
  - src/backend/tests/unit/core/test_database_session.py
related_pr: "feat/R2-04A-error-contract (uncommitted)"
---

# logger.exception 在 rollback 失败时把异常原文写入日志

## 1. 症状（表现形式）

R2-04A 聚焦测试首次运行收集 15 项，其中 14 项通过、1 项失败：`test_get_db_preserves_original_when_rollback_fails` 在 `caplog.text` 中发现哨兵字符串 `rollback secret`。业务原异常仍被正确重新抛出，但 rollback 异常的 traceback 和原文被完整写入日志。

## 2. 复现条件

只要 `get_db()` 收到依赖调用方抛出的异常，同时 `Session.rollback()` 再抛出带敏感内容的异常，就能稳定复现：

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/core/test_database_session.py
```

测试用 mock 令 `rollback()` 抛出 `RuntimeError("rollback secret")`，随后断言原异常身份、close 调用和日志脱敏。

## 3. 定位过程

1. 先实现 `rollback -> bare raise -> finally close`，并用 mock 测试原异常是否不被 rollback 异常覆盖；该部分行为正确。
2. 起初认为日志格式只显式传入 `type(rollback_error).__name__`，因此不会包含异常消息。
3. 聚焦测试失败后检查 `caplog`，发现 `logger.exception(...)` 会隐式附加当前异常的 traceback；即使格式参数只包含异常类型，traceback 最后一行仍包含 `RuntimeError: rollback secret`。
4. 排除“只修改测试断言”的做法，因为 R2-04A 明确要求 rollback 诊断脱敏，测试准确暴露了实现缺陷。

## 4. 根因

`logger.exception` 自动记录当前异常 traceback，绕过了显式日志字段只记录异常类型的脱敏设计。

## 5. 解决方案

将 `src/backend/config/database.py::get_db` 的 rollback 失败日志从 `logger.exception` 改为 `logger.error`，只记录固定文案和 `type(rollback_error).__name__`。继续使用 bare `raise` 保留业务原异常，并由 `finally` 保证 Session close。

未选择保留 traceback 后再做正则脱敏，因为异常消息可能包含任意 SQL、DSN 或驱动原文，事后黑名单无法可靠覆盖。

## 6. 验证

修复前：15 项聚焦测试中 1 项失败，`caplog.text` 含 `rollback secret`。

修复后执行：

```text
cd src/backend
python -m pytest -q -p no:cacheprovider tests/unit/core/test_error_codes.py tests/unit/core/test_domain_errors.py tests/unit/core/test_database_session.py tests/unit/test_response_contract.py
```

结果：15 passed，0 failed，0.33s；日志保留“数据库会话回滚失败”和异常类型，不含哨兵原文；原业务异常身份保持，close 仍调用一次。

## 7. 通用经验

- 对可能携带 SQL、DSN、请求正文或第三方响应的异常，禁止仅凭日志格式参数判断已脱敏；必须检查 `exc_info`/traceback 行为。
- 清理失败日志默认记录异常类别和安全上下文；只有明确证明异常文本安全时才附加 traceback。
- 数据库依赖测试必须同时验证顺序、原异常身份、close 和日志内容，不能只断言 rollback 被调用。
- 脱敏测试应注入唯一哨兵并同时检查 HTTP 响应与 `caplog`。

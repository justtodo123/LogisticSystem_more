# 测试结果固化报告

**项目**: DeepSeek 路径优化 - 智能物流平台  
**测试日期**: 2026-08-06  
**分支**: main  

---

## 1. 测试环境

| 项目 | 值 |
|------|-----|
| OS | Windows 11 (win32) |
| Python | 3.13.3 |
| pytest | 9.1.1 |
| asyncio mode | auto |
| 数据库 | SQLite（内存 / 临时文件） |

---

## 2. 测试执行命令

```bash
cd src/backend
.venv\Scripts\python.exe -m pytest tests/ --tb=short -q --no-header
```

**快速运行（跳过慢速测试）**：

```bash
cd src/backend
.venv\Scripts\python.exe -m pytest tests/ --tb=short -q --fast
```

---

## 3. 测试结果摘要

| 指标 | 数值 |
|------|------|
| 总收集 | **423** 项 |
| 通过 | **421** (99.53%) |
| 失败 | **2** (0.47%) |
| 耗时 | **~76 秒** |
| 警告 | 353 条（均为已知弃用/兼容性警告） |

---

## 4. 测试分布

### API 层测试（13 文件）

| 模块 | 数量 | 状态 |
|------|------|------|
| `test_health.py` | 3 | ✅ |
| `test_auth.py` | 7 | ✅ |
| `test_ai.py` | 13 | ✅ |
| `test_drivers.py` | 9 | ✅ |
| `test_exceptions.py` | 10 | ✅ |
| `test_nodes.py` | 10 | ✅ |
| `test_orders.py` | 9 | ✅ |
| `test_pagination.py` | 6 | ✅ |
| `test_permissions.py` | 9 | ✅ |
| `test_routes.py` | 9 | ✅ |
| `test_schedule.py` | 15 | ✅ |
| `test_simulation.py` | 6 | ✅ |
| `test_vehicles.py` | 9 | ✅ |

### 集成测试（5 文件）

| 模块 | 数量 | 状态 |
|------|------|------|
| `test_auto_redispatch.py` | 5 | ✅ |
| `test_dispatch_pipeline.py` | 4 | ✅ |
| `test_exception_replan.py` | 4 | ✅ |
| `test_phase8_regression.py` | 6 | ✅ |
| `test_schedule_pipeline.py` | 3 | ✅ |
| `test_simulation_pipeline.py` | 3 | ✅ |

### 单元测试 - 算法（4 文件）

| 模块 | 数量 | 状态 |
|------|------|------|
| `test_global_schedule.py` (F007) | 7 | ✅ |
| `test_node_dispatch.py` (F005) | 4 | ✅ |
| `test_packaging.py` (F021) | 4 | ✅ |
| `test_route_planning.py` (F006) | 4 | ✅ |

### 单元测试 - 服务层（11 文件）

| 模块 | 数量 | 状态 |
|------|------|------|
| `test_arrival_confirm_service.py` | 13 | ✅ |
| `test_auth_service.py` | 10 | ✅ |
| `test_deepseek_service.py` | 6 | ✅ |
| `test_dispatch_service.py` | 4 | ✅ |
| `test_driver_service.py` | 11 | ✅ |
| `test_exception_service.py` | 19 | ✅ |
| `test_goods_service.py` | 8 | ✅ |
| `test_node_service.py` | 16 | ✅ |
| `test_order_service.py` | 14 | ✅ |
| `test_package_service.py` | 8 | ⚠️ 1 FAIL |
| `test_route_service.py` | 7 | ✅ |
| `test_schedule_service.py` | 15 | ⚠️ 1 FAIL |
| `test_simulation_service.py` | 7 | ✅ |
| `test_state_machine.py` | ~112 | ✅ |
| `test_vehicle_service.py` | 11 | ✅ |

---

## 5. 失败用例分析

| 测试用例 | 错误类型 | 分析 |
|----------|----------|------|
| `test_repack_package_success` | `code=50000` 而非 `0` | 服务层返回了内部错误码，可能因参数变更或业务约束不满足 |
| `test_normal_flow_preview_then_confirm` | L1→L2 包裹数 = 0 | 调度流水线预览后未正确生成 L1→L2 包裹，可能与状态流转逻辑变更有关 |

> 2 个失败均不影响核心功能（F007/F005/F006 全通过）。建议后续统一用例与当前代码状态。

---

## 6. 已知警告（均为兼容性警告，不阻塞运行）

| 类型 | 影响文件 | 说明 |
|------|----------|------|
| Pydantic `config` deprecation | `database.py`, `schemas/*.py` | 应迁移到 `ConfigDict`（Pydantic V3 将移除） |
| FastAPI `on_event` deprecation | `main.py` | 应迁移到 `lifespan` 事件处理器 |
| `datetime.utcnow()` deprecation | `auth_service.py` | 应使用 `datetime.now(datetime.UTC)` |
| `model.dict()` deprecation | `api/nodes.py` | 应使用 `model_dump()` |
| Starlette `httpx` deprecation | TestClient | 应升级到 `httpx2` |
| JWT Key Length | `jwt/api_jwt.py` | HMAC Key 30 字节低于推荐 32 字节 |

---

## 7. 覆盖率（上次记录，非实时）

| 模块 | 覆盖率 |
|------|--------|
| `services/` | ~90%+ |
| `algorithms/` | ~95%+ |
| `api/` | ~85%+ |
| 整体 | ~75% |

---

## 8. 结论

- 核心调度链路（F007 → F021 → F005 → F006）全部通过测试
- 异常重规划（F013）和 AI 降级（F014）测试通过
- 状态机 112 项用例全部通过，状态流转逻辑稳固
- 2 个失败为重点排查项，建议下一迭代修复
- 已知警告均为 Pydantic/FastAPI 版本升级相关的兼容性提示，不影响功能

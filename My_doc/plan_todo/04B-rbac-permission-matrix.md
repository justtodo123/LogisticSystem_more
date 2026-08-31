# R2-04B 角色 × 权限矩阵

> 版本：v2026-08-31。后端 `ROLE_PERMISSIONS` 与 `/me.permissions` 是唯一运行时真相源；本文件是盘点记录。
> 未知角色 fail closed：权限集合为空。
> 前端 `can(permission)` 只影响菜单、路由和按钮，不构成安全边界。

## 公开路由

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| POST | `/api/auth/login` | 登录；进程内限流；失败不区分用户是否存在 |

OpenAPI / docs 若开启，同样不要求登录。

## 认证但无额外权限位

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/auth/me` | 返回规范化 `permissions` |
| POST | `/api/auth/logout` | 同事务递增 `token_version` |

## ERP 回退

| 方法 | 路径 | 认证 |
|---|---|---|
| POST | `/api/erp/orders` | 配置了 `ERP_API_KEY` 时校验 `X-ERP-API-Key`；否则回退 JWT，要求 active、`token_version` 匹配且拥有 `orders:write` |

## 最小权限路由盘点

| 权限 | 路由 |
|---|---|
| `orders:read` | `GET /api/orders`、`GET /api/orders/{order_code}` |
| `orders:write` | `POST /api/orders`、`PUT/DELETE /api/orders/{order_code}`、`POST /api/orders/{order_code}/close` |
| `orders:import` | `POST /api/orders/import` |
| `goods:read` | `GET /api/goods`、`GET /api/goods/{goods_code}` |
| `goods:write` | `PUT /api/goods/{goods_code}` |
| `packages:read` | `GET /api/packages`、`GET /api/packages/{package_code}` |
| `packages:write` | `POST /api/packages/{package_code}/repack` |
| `vehicles:read` | `GET /api/vehicles`、`GET /api/vehicles/{vehicle_code}` |
| `vehicles:write` | `POST /api/vehicles`、`PUT/DELETE /api/vehicles/{vehicle_code}` |
| `drivers:read` | `GET /api/drivers`、`GET /api/drivers/{driver_code}` |
| `drivers:write` | `POST /api/drivers`、`PUT/DELETE /api/drivers/{driver_code}` |
| `nodes:read` | `GET /api/nodes`、`GET /api/nodes/{node_code}` |
| `nodes:write` | 存储/分拣中心的 POST/PUT/DELETE |
| `schedule:read` | 调度方案、批次、明细、路线查询 |
| `schedule:execute` | 生成全局调度、节点调度、删 draft、人工干预、手动规划路线 |
| `schedule:confirm` | `POST /api/schedule/confirm/{schedule_code}`；AI 建议确认/拒绝 |
| `arrivals:confirm` | 到货确认读/写（仅 admin、dispatcher） |
| `simulation:write` | `POST /api/simulation/deliver` |
| `exceptions:read` | 异常列表/详情 |
| `exceptions:write` | 创建/更新/解决异常；单条与批量重规划 |
| `ai:use` | `/api/ai/parse|explain|review|analyze-exception`；建议列表 |
| `audit:read` | `GET /api/audit-logs` |
| `export:read` | `POST /api/export/orders`、`POST /api/export/schedule` |
| `reports:read` | `/api/reports/*` |
| `notifications:read` | `GET /api/notifications/config` |
| `notifications:write` | 更新通知配置、发送测试通知 |
| `admin:users` | `PATCH /api/users/{username}`（禁用/改角色，同事务撤权） |

强制幂等键的写接口（D-R2-IDEM）在鉴权通过后 claim，权限不足不得占用幂等键。

## 角色允许矩阵

`Y` = 允许，空 = 拒绝。`warehouse_operator` 与 `manager` 共用同一集合。

| 权限 | admin | dispatcher | viewer | manager | warehouse_operator |
|---|---|---|---|---|---|
| `orders:read` | Y | Y | Y | Y | Y |
| `orders:write` | Y | Y |  | Y | Y |
| `orders:import` | Y | Y |  | Y | Y |
| `goods:read` | Y | Y | Y | Y | Y |
| `goods:write` | Y | Y |  |  |  |
| `packages:read` | Y | Y | Y | Y | Y |
| `packages:write` | Y | Y |  |  |  |
| `vehicles:read` | Y | Y | Y | Y | Y |
| `vehicles:write` | Y | Y |  |  |  |
| `drivers:read` | Y | Y | Y | Y | Y |
| `drivers:write` | Y | Y |  |  |  |
| `nodes:read` | Y | Y | Y | Y | Y |
| `nodes:write` | Y | Y |  |  |  |
| `schedule:read` | Y | Y | Y |  |  |
| `schedule:execute` | Y | Y |  |  |  |
| `schedule:confirm` | Y | Y |  |  |  |
| `arrivals:confirm` | Y | Y |  |  |  |
| `simulation:write` | Y | Y |  |  |  |
| `exceptions:read` | Y | Y | Y |  |  |
| `exceptions:write` | Y | Y |  |  |  |
| `ai:use` | Y | Y |  |  |  |
| `audit:read` | Y | Y |  |  |  |
| `export:read` | Y | Y |  |  |  |
| `reports:read` | Y | Y | Y | Y | Y |
| `notifications:read` | Y | Y | Y | Y | Y |
| `notifications:write` | Y | Y |  |  |  |
| `admin:users` | Y |  |  |  |  |

Owner 摘要：AI=`ai:use`（确认/拒绝另需 `schedule:confirm`）；审计=`audit:read`；导出=`export:read`；重规划=`exceptions:write`；到货确认=`arrivals:confirm`（仅 dispatcher/admin）。

## Token 与限流边界

- JWT 携带 `tv`；与 `users.token_version` 不一致则 401，文案不泄露撤权细节。
- logout / 禁用 / 改角色在同一事务递增 `token_version`。
- 登录 `expires_in` 等于 `settings.JWT_EXPIRE_SECONDS`。
- 登录限流：进程内计数，默认 5 次 / 60 秒，键为 `ip + username`。P0 单进程有效，跨 worker 复跑归 R2-05。
- 演示账户 `admin` / `dispatcher` / `manager` 仅用于开发演示；限流对它们同样生效。

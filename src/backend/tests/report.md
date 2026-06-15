# Test Report

*Report generated on 15-Jun-2026 at 09:55:16 by [pytest-md]*

[pytest-md]: https://github.com/hackebrot/pytest-md

## Summary

56 tests ran in 4.97 seconds

- 27 failed
- 29 passed

## 27 failed

### tests\unit\algorithms\test_node_dispatch.py

`TestNodeDispatchNormal.test_node_dispatch_success` 0.02s

```
tests\unit\algorithms\test_node_dispatch.py:64: in test_node_dispatch_success
    result = run_node_dispatch(
algorithms\node_dispatch.py:384: in run_node_dispatch
    raise ValueError("L0→L1没有可调度的包裹")
E   ValueError: L0→L1没有可调度的包裹
```

`TestNodeDispatchNormal.test_node_dispatch_no_packages` 0.01s

```
tests\unit\algorithms\test_node_dispatch.py:112: in test_node_dispatch_no_packages
    result = run_node_dispatch(
algorithms\node_dispatch.py:384: in run_node_dispatch
    raise ValueError("L0→L1没有可调度的包裹")
E   ValueError: L0→L1没有可调度的包裹
```

`TestNodeDispatchEdgeCases.test_node_dispatch_no_available_vehicles` 0.08s

```
tests\unit\algorithms\test_node_dispatch.py:187: in test_node_dispatch_no_available_vehicles
    result = run_node_dispatch(
algorithms\node_dispatch.py:384: in run_node_dispatch
    raise ValueError("L0→L1没有可调度的包裹")
E   ValueError: L0→L1没有可调度的包裹
```

### tests\unit\services\test_auth_service.py

`TestCreateAccessToken.test_create_access_token` 0.18s

```
tests\unit\services\test_auth_service.py:80: in test_create_access_token
    token = create_access_token(
E   TypeError: create_access_token() got an unexpected keyword argument 'data'
```

`TestCreateAccessToken.test_create_access_token_expired` 0.18s

```
tests\unit\services\test_auth_service.py:110: in test_create_access_token_expired
    token = create_access_token(
E   TypeError: create_access_token() got an unexpected keyword argument 'data'
```

`TestAuthenticateUser.test_authenticate_user_success` 0.18s

```
tests\unit\services\test_auth_service.py:138: in test_authenticate_user_success
    authenticated_user = authenticate_user("testuser", "123456", db_session)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:39: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^
E   AttributeError: 'str' object has no attribute 'query'
```

`TestAuthenticateUser.test_authenticate_user_wrong_password` 0.17s

```
tests\unit\services\test_auth_service.py:160: in test_authenticate_user_wrong_password
    authenticated_user = authenticate_user("testuser", "wrong", db_session)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:39: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^
E   AttributeError: 'str' object has no attribute 'query'
```

`TestAuthenticateUser.test_authenticate_user_not_found` 0.00s

```
tests\unit\services\test_auth_service.py:169: in test_authenticate_user_not_found
    authenticated_user = authenticate_user("nonexist", "123456", db_session)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:39: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^
E   AttributeError: 'str' object has no attribute 'query'
```

`TestGetUserByUsername.test_get_user_by_username_success` 0.18s

```
tests\unit\services\test_auth_service.py:193: in test_get_user_by_username_success
    found_user = get_user_by_username("testuser", db_session)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:47: in get_user_by_username
    return db.query(User).filter(User.username == username).first()
           ^^^^^^^^
E   AttributeError: 'str' object has no attribute 'query'
```

`TestGetUserByUsername.test_get_user_by_username_not_found` 0.00s

```
tests\unit\services\test_auth_service.py:204: in test_get_user_by_username_not_found
    found_user = get_user_by_username("nonexist", db_session)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:47: in get_user_by_username
    return db.query(User).filter(User.username == username).first()
           ^^^^^^^^
E   AttributeError: 'str' object has no attribute 'query'
```

### tests\unit\services\test_dispatch_service.py

`TestCreateNodeDispatch.test_create_node_dispatch_success` 0.02s

```
tests\unit\services\test_dispatch_service.py:52: in test_create_node_dispatch_success
    assert result["code"] == 0
E   assert 40001 == 0
```

`TestGetDispatchBatches.test_get_batches_empty` 0.00s

```
tests\unit\services\test_dispatch_service.py:126: in test_get_batches_empty
    result = await DispatchService.get_dispatch_batches(
E   TypeError: DispatchService.get_dispatch_batches() got an unexpected keyword argument 'page'
```

`TestGetDispatchBatches.test_get_batches_with_data` 0.03s

```
tests\unit\services\test_dispatch_service.py:153: in test_get_batches_with_data
    assert batch_result["code"] == 0
E   assert 40001 == 0
```

`TestGetDispatchBatchDetail.test_get_batch_detail_success` 0.02s

```
tests\unit\services\test_dispatch_service.py:187: in test_get_batch_detail_success
    assert batch_result["code"] == 0
E   assert 40001 == 0
```

`TestGetDispatchBatchDetail.test_get_batch_detail_not_found` 0.00s

```
tests\unit\services\test_dispatch_service.py:203: in test_get_batch_detail_not_found
    result = await DispatchService.get_dispatch_batch(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: type object 'DispatchService' has no attribute 'get_dispatch_batch'. Did you mean: 'get_dispatch_batches'?
```

### tests\unit\services\test_route_service.py

`TestCreateRoute.test_create_route_success` 0.00s

```
tests\unit\services\test_route_service.py:36: in test_create_route_success
    node_dispatch = NodeDispatch(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'node_dispatch_code' is an invalid keyword argument for NodeDispatch
```

`TestCreateRoute.test_create_route_node_dispatch_not_found` 0.00s

```
tests\unit\services\test_route_service.py:73: in test_create_route_node_dispatch_not_found
    result = await RouteService.create_route(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: type object 'RouteService' has no attribute 'create_route'
```

`TestCreateRoute.test_create_route_algorithm_error` 0.00s

```
tests\unit\services\test_route_service.py:96: in test_create_route_algorithm_error
    node_dispatch = NodeDispatch(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'node_dispatch_code' is an invalid keyword argument for NodeDispatch
```

`TestGetRoutes.test_get_routes_empty` 0.00s

```
tests\unit\services\test_route_service.py:131: in test_get_routes_empty
    result = await RouteService.get_routes(
E   TypeError: RouteService.get_routes() missing 1 required positional argument: 'batch_code'
```

`TestGetRoutes.test_get_routes_with_data` 0.00s

```
tests\unit\services\test_route_service.py:147: in test_get_routes_with_data
    route = Route(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'node_dispatch_id' is an invalid keyword argument for Route
```

`TestGetRouteDetail.test_get_route_detail_success` 0.00s

```
tests\unit\services\test_route_service.py:181: in test_get_route_detail_success
    route = Route(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'node_dispatch_id' is an invalid keyword argument for Route
```

`TestGetRouteDetail.test_get_route_detail_not_found` 0.00s

```
tests\unit\services\test_route_service.py:206: in test_get_route_detail_not_found
    result = await RouteService.get_route(
                   ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: type object 'RouteService' has no attribute 'get_route'. Did you mean: 'get_routes'?
```

### tests\unit\services\test_simulation_service.py

`TestDeliverPackages.test_deliver_by_vehicle_success` 0.00s

```
tests\unit\services\test_simulation_service.py:37: in test_deliver_by_vehicle_success
    package = Package(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'vehicle_id' is an invalid keyword argument for Package
```

`TestDeliverPackages.test_deliver_by_package_success` 0.00s

```
tests\unit\services\test_simulation_service.py:88: in test_deliver_by_package_success
    package = Package(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'vehicle_id' is an invalid keyword argument for Package
```

`TestDeliverPackages.test_deliver_no_params` 0.00s

```
tests\unit\services\test_simulation_service.py:131: in test_deliver_no_params
    package1 = Package(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'vehicle_id' is an invalid keyword argument for Package
```

`TestDeliverPackages.test_deliver_package_not_in_transit` 0.00s

```
tests\unit\services\test_simulation_service.py:186: in test_deliver_package_not_in_transit
    package = Package(
<string>:4: in __init__
    ???
.venv\Lib\site-packages\sqlalchemy\orm\state.py:596: in _initialize_instance
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\state.py:594: in _initialize_instance
    manager.original_init(*mixed[1:], **kwargs)
.venv\Lib\site-packages\sqlalchemy\orm\decl_base.py:2179: in _declarative_constructor
    raise TypeError(
E   TypeError: 'vehicle_id' is an invalid keyword argument for Package
```

`TestDeliverPackages.test_deliver_vehicle_not_found` 0.00s

```
tests\unit\services\test_simulation_service.py:226: in test_deliver_vehicle_not_found
    assert "车辆" in result["message"] or "不存在" in result["message"]
E   AssertionError: assert ('\u8f66\u8f86' in '\u6ca1\u6709\u627e\u5230\u53ef\u9001\u8fbe\u7684\u5305\u88f9' or '\u4e0d\u5b58\u5728' in '\u6ca1\u6709\u627e\u5230\u53ef\u9001\u8fbe\u7684\u5305\u88f9')
```

## 29 passed

### tests\unit\algorithms\test_global_schedule.py

`TestGlobalScheduleNormal.test_normal_schedule_generates_paths` 0.01s

`TestGlobalScheduleHardConstraint.test_no_l1_available_raises_error` 0.01s

`TestGlobalScheduleHardConstraint.test_l1_capacity_exceeded_raises_error` 0.01s

`TestGlobalScheduleGreedySelection.test_greedy_selects_lowest_score_l1` 0.01s

`TestGlobalScheduleGreedySelection.test_same_order_same_l1_enforcement` 0.01s

`TestGlobalScheduleGreedySelection.test_invalid_algorithm_raises_error` 0.00s

`TestGlobalScheduleGreedySelection.test_no_pending_orders_raises_error` 0.00s

### tests\unit\algorithms\test_node_dispatch.py

`TestNodeDispatchEdgeCases.test_node_dispatch_schedule_not_found` 0.00s

### tests\unit\algorithms\test_packaging.py

`TestPackagingNormal.test_packaging_generates_packages` 0.00s

`TestPackagingNormal.test_packaging_l0_l1_merge` 0.00s

`TestPackagingNormal.test_packaging_l1_l2_by_order` 0.01s

`TestPackagingEdgeCases.test_packaging_empty_input` 0.00s

`TestPackagingEdgeCases.test_packaging_invalid_goods_code` 0.00s

### tests\unit\algorithms\test_route_planning.py

`TestRoutePlanningNormal.test_route_planning_success` 0.01s

`TestRoutePlanningNormal.test_route_planning_return_trip` 0.01s

`TestRoutePlanningEdgeCases.test_route_planning_node_dispatch_not_found` 0.00s

`TestRoutePlanningEdgeCases.test_route_planning_empty_tasks` 0.00s

### tests\unit\services\test_auth_service.py

`TestGetPasswordHash.test_get_password_hash` 0.52s

`TestVerifyPassword.test_verify_password_correct` 0.35s

`TestVerifyPassword.test_verify_password_wrong` 0.35s

### tests\unit\services\test_dispatch_service.py

`TestCreateNodeDispatch.test_create_node_dispatch_schedule_not_found` 0.00s

`TestCreateNodeDispatch.test_create_node_dispatch_no_available_vehicles` 0.02s

### tests\unit\services\test_schedule_service.py

`TestScheduleServiceNormalFlow.test_normal_flow_writes_all_data` 0.02s

`TestScheduleServiceNormalFlow.test_specific_orders_schedule` 0.02s

`TestScheduleServiceExceptionRollback.test_f021_exception_triggers_rollback` 0.01s

`TestScheduleServiceExceptionRollback.test_f007_exception_triggers_rollback` 0.00s

`TestScheduleServiceQuery.test_get_global_schedules_empty` 0.00s

`TestScheduleServiceQuery.test_get_global_schedule_not_found` 0.08s

### tests\unit\services\test_simulation_service.py

`TestDeliverPackages.test_deliver_package_not_found` 0.00s

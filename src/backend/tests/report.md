# Test Report

*Report generated on 15-Jun-2026 at 16:36:05 by [pytest-md]*

[pytest-md]: https://github.com/hackebrot/pytest-md

## Summary

56 tests ran in 8.23 seconds

- 1 failed
- 55 passed

## 1 failed

### tests\unit\services\test_simulation_service.py

`TestDeliverPackages.test_deliver_by_vehicle_success` 0.03s

```
tests\unit\services\test_simulation_service.py:118: in test_deliver_by_vehicle_success
    assert vehicle.status == "idle"
E   AssertionError: assert 'delivering' == 'idle'
E     
E     [0m[91m- idle[39;49;00m[90m[39;49;00m
E     [92m+ delivering[39;49;00m[90m[39;49;00m
```

## 55 passed

### tests\unit\algorithms\test_global_schedule.py

`TestGlobalScheduleNormal.test_normal_schedule_generates_paths` 0.04s

`TestGlobalScheduleHardConstraint.test_no_l1_available_raises_error` 0.11s

`TestGlobalScheduleHardConstraint.test_l1_capacity_exceeded_raises_error` 0.02s

`TestGlobalScheduleGreedySelection.test_greedy_selects_lowest_score_l1` 0.02s

`TestGlobalScheduleGreedySelection.test_same_order_same_l1_enforcement` 0.03s

`TestGlobalScheduleGreedySelection.test_invalid_algorithm_raises_error` 0.00s

`TestGlobalScheduleGreedySelection.test_no_pending_orders_raises_error` 0.00s

### tests\unit\algorithms\test_node_dispatch.py

`TestNodeDispatchNormal.test_node_dispatch_success` 0.07s

`TestNodeDispatchNormal.test_node_dispatch_no_packages` 0.01s

`TestNodeDispatchEdgeCases.test_node_dispatch_schedule_not_found` 0.00s

`TestNodeDispatchEdgeCases.test_node_dispatch_no_available_vehicles` 0.03s

### tests\unit\algorithms\test_packaging.py

`TestPackagingNormal.test_packaging_generates_packages` 0.01s

`TestPackagingNormal.test_packaging_l0_l1_merge` 0.01s

`TestPackagingNormal.test_packaging_l1_l2_by_order` 0.01s

`TestPackagingEdgeCases.test_packaging_empty_input` 0.00s

`TestPackagingEdgeCases.test_packaging_invalid_goods_code` 0.00s

### tests\unit\algorithms\test_route_planning.py

`TestRoutePlanningNormal.test_route_planning_success` 0.01s

`TestRoutePlanningNormal.test_route_planning_return_trip` 0.01s

`TestRoutePlanningEdgeCases.test_route_planning_node_dispatch_not_found` 0.00s

`TestRoutePlanningEdgeCases.test_route_planning_empty_tasks` 0.01s

### tests\unit\services\test_auth_service.py

`TestGetPasswordHash.test_get_password_hash` 0.63s

`TestVerifyPassword.test_verify_password_correct` 0.43s

`TestVerifyPassword.test_verify_password_wrong` 0.46s

`TestCreateAccessToken.test_create_access_token` 0.21s

`TestCreateAccessToken.test_create_access_token_expired` 0.22s

`TestAuthenticateUser.test_authenticate_user_success` 0.43s

`TestAuthenticateUser.test_authenticate_user_wrong_password` 0.44s

`TestAuthenticateUser.test_authenticate_user_not_found` 0.00s

`TestGetUserByUsername.test_get_user_by_username_success` 0.22s

`TestGetUserByUsername.test_get_user_by_username_not_found` 0.00s

### tests\unit\services\test_dispatch_service.py

`TestCreateNodeDispatch.test_create_node_dispatch_success` 0.09s

`TestCreateNodeDispatch.test_create_node_dispatch_schedule_not_found` 0.00s

`TestCreateNodeDispatch.test_create_node_dispatch_no_available_vehicles` 0.03s

`TestGetDispatchBatches.test_get_batches_empty` 0.00s

`TestGetDispatchBatches.test_get_batches_with_data` 0.08s

`TestGetDispatchBatchDetail.test_get_batch_detail_success` 0.09s

`TestGetDispatchBatchDetail.test_get_batch_detail_not_found` 0.00s

### tests\unit\services\test_route_service.py

`TestCreateRoutePlanning.test_create_route_planning_success` 0.02s

`TestCreateRoutePlanning.test_create_route_planning_batch_not_found` 0.00s

`TestCreateRoutePlanning.test_create_route_planning_algorithm_error` 0.01s

`TestGetRoutes.test_get_routes_empty` 0.01s

`TestGetRoutes.test_get_routes_with_data` 0.02s

`TestGetRouteDetail.test_get_route_detail_success` 0.02s

`TestGetRouteDetail.test_get_route_detail_not_found` 0.00s

### tests\unit\services\test_schedule_service.py

`TestScheduleServiceNormalFlow.test_normal_flow_writes_all_data` 0.03s

`TestScheduleServiceNormalFlow.test_specific_orders_schedule` 0.02s

`TestScheduleServiceExceptionRollback.test_f021_exception_triggers_rollback` 0.03s

`TestScheduleServiceExceptionRollback.test_f007_exception_triggers_rollback` 0.01s

`TestScheduleServiceQuery.test_get_global_schedules_empty` 0.01s

`TestScheduleServiceQuery.test_get_global_schedule_not_found` 0.00s

### tests\unit\services\test_simulation_service.py

`TestDeliverPackages.test_deliver_by_package_success` 0.03s

`TestDeliverPackages.test_deliver_no_params` 0.04s

`TestDeliverPackages.test_deliver_package_not_in_transit` 0.01s

`TestDeliverPackages.test_deliver_vehicle_not_found` 0.00s

`TestDeliverPackages.test_deliver_package_not_found` 0.00s

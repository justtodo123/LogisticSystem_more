# Test Report

*Report generated on 15-Jun-2026 at 17:10:26 by [pytest-md]*

[pytest-md]: https://github.com/hackebrot/pytest-md

## Summary

56 tests ran in 26.31 seconds

- 5 error
- 49 failed
- 2 passed

## 5 error

### tests\api\test_exceptions.py

`error at setup of TestExceptionAPI.test_get_exceptions_success` 0.19s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.IntegrityError: NOT NULL constraint failed: routes.total_emission

The above exception was the direct cause of the following exception:
tests\api\test_exceptions.py:53: in setup_exception_data
    db_session.flush()
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4352: in flush
    self._flush(objects)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4487: in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4448: in _flush
    flush_context.execute()
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:465: in execute
    rec.execute(self)
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:641: in execute
    util.preloaded.orm_persistence.save_obj(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:94: in save_obj
    _emit_insert_statements(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:1234: in _emit_insert_statements
    result = connection.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: routes.total_emission
E   [SQL: INSERT INTO routes (route_code, dispatch_id, vehicle_id, route_segments, total_distance, total_time, total_emission, version, parent_id, replan_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id, algorithm_type, is_replan, created_at]
E   [parameters: ('RT_TEST_001', 1, 1, '"[{\\"road_name\\":\\"\\u6d4b\\u8bd5\\u9053\\u8def\\"}]"', 100.0, 120.0, None, 1, None, None)]
E   (Background on this error at: https://sqlalche.me/e/20/gkpj)
```

`error at setup of TestExceptionAPI.test_get_exception_detail_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.IntegrityError: NOT NULL constraint failed: routes.total_emission

The above exception was the direct cause of the following exception:
tests\api\test_exceptions.py:53: in setup_exception_data
    db_session.flush()
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4352: in flush
    self._flush(objects)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4487: in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4448: in _flush
    flush_context.execute()
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:465: in execute
    rec.execute(self)
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:641: in execute
    util.preloaded.orm_persistence.save_obj(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:94: in save_obj
    _emit_insert_statements(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:1234: in _emit_insert_statements
    result = connection.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: routes.total_emission
E   [SQL: INSERT INTO routes (route_code, dispatch_id, vehicle_id, route_segments, total_distance, total_time, total_emission, version, parent_id, replan_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id, algorithm_type, is_replan, created_at]
E   [parameters: ('RT_TEST_001', 1, 1, '"[{\\"road_name\\":\\"\\u6d4b\\u8bd5\\u9053\\u8def\\"}]"', 100.0, 120.0, None, 1, None, None)]
E   (Background on this error at: https://sqlalche.me/e/20/gkpj)
```

`error at setup of TestExceptionAPI.test_update_exception_success` 0.19s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.IntegrityError: NOT NULL constraint failed: routes.total_emission

The above exception was the direct cause of the following exception:
tests\api\test_exceptions.py:53: in setup_exception_data
    db_session.flush()
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4352: in flush
    self._flush(objects)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4487: in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4448: in _flush
    flush_context.execute()
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:465: in execute
    rec.execute(self)
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:641: in execute
    util.preloaded.orm_persistence.save_obj(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:94: in save_obj
    _emit_insert_statements(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:1234: in _emit_insert_statements
    result = connection.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: routes.total_emission
E   [SQL: INSERT INTO routes (route_code, dispatch_id, vehicle_id, route_segments, total_distance, total_time, total_emission, version, parent_id, replan_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id, algorithm_type, is_replan, created_at]
E   [parameters: ('RT_TEST_001', 1, 1, '"[{\\"road_name\\":\\"\\u6d4b\\u8bd5\\u9053\\u8def\\"}]"', 100.0, 120.0, None, 1, None, None)]
E   (Background on this error at: https://sqlalche.me/e/20/gkpj)
```

`error at setup of TestExceptionAPI.test_replan_success` 0.19s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.IntegrityError: NOT NULL constraint failed: routes.total_emission

The above exception was the direct cause of the following exception:
tests\api\test_exceptions.py:53: in setup_exception_data
    db_session.flush()
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4352: in flush
    self._flush(objects)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4487: in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4448: in _flush
    flush_context.execute()
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:465: in execute
    rec.execute(self)
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:641: in execute
    util.preloaded.orm_persistence.save_obj(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:94: in save_obj
    _emit_insert_statements(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:1234: in _emit_insert_statements
    result = connection.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: routes.total_emission
E   [SQL: INSERT INTO routes (route_code, dispatch_id, vehicle_id, route_segments, total_distance, total_time, total_emission, version, parent_id, replan_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id, algorithm_type, is_replan, created_at]
E   [parameters: ('RT_TEST_001', 1, 1, '"[{\\"road_name\\":\\"\\u6d4b\\u8bd5\\u9053\\u8def\\"}]"', 100.0, 120.0, None, 1, None, None)]
E   (Background on this error at: https://sqlalche.me/e/20/gkpj)
```

`error at setup of TestExceptionAPI.test_replan_invalid_action` 0.19s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.IntegrityError: NOT NULL constraint failed: routes.total_emission

The above exception was the direct cause of the following exception:
tests\api\test_exceptions.py:53: in setup_exception_data
    db_session.flush()
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4352: in flush
    self._flush(objects)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4487: in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py:122: in __exit__
    raise exc_value.with_traceback(exc_tb)
.venv\Lib\site-packages\sqlalchemy\orm\session.py:4448: in _flush
    flush_context.execute()
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:465: in execute
    rec.execute(self)
.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py:641: in execute
    util.preloaded.orm_persistence.save_obj(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:94: in save_obj
    _emit_insert_statements(
.venv\Lib\site-packages\sqlalchemy\orm\persistence.py:1234: in _emit_insert_statements
    result = connection.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: routes.total_emission
E   [SQL: INSERT INTO routes (route_code, dispatch_id, vehicle_id, route_segments, total_distance, total_time, total_emission, version, parent_id, replan_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id, algorithm_type, is_replan, created_at]
E   [parameters: ('RT_TEST_001', 1, 1, '"[{\\"road_name\\":\\"\\u6d4b\\u8bd5\\u9053\\u8def\\"}]"', 100.0, 120.0, None, 1, None, None)]
E   (Background on this error at: https://sqlalche.me/e/20/gkpj)
```

## 49 failed

### tests\api\test_auth.py

`TestLogin.test_login_success` 0.28s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_auth.py:38: in test_login_success
    response = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestLogin.test_login_wrong_password` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_auth.py:70: in test_login_wrong_password
    response = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestLogin.test_login_user_not_found` 0.00s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_auth.py:84: in test_login_user_not_found
    response = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('nonexist', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetMe.test_get_me_success` 0.19s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_auth.py:127: in test_get_me_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetMe.test_get_me_no_token` 0.00s

```
tests\api\test_auth.py:153: in test_get_me_no_token
    assert response.status_code == 403
E   assert 401 == 403
E    +  where 401 = <Response [401 Unauthorized]>.status_code
```

`TestLogout.test_logout_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_auth.py:176: in test_logout_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_drivers.py

`TestGetDrivers.test_get_drivers_empty` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_drivers.py:42: in test_get_drivers_empty
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetDrivers.test_get_drivers_with_data` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_drivers.py:102: in test_get_drivers_with_data
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateDriver.test_create_driver_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_drivers.py:153: in test_create_driver_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateDriver.test_create_driver_duplicate_code` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_drivers.py:219: in test_create_driver_duplicate_code
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteDriver.test_delete_driver_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_drivers.py:288: in test_delete_driver_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteDriver.test_delete_driver_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_drivers.py:320: in test_delete_driver_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_exceptions.py

`TestExceptionAPI.test_get_exceptions_with_filters` 0.03s

```
tests\api\test_exceptions.py:107: in test_get_exceptions_with_filters
    assert response.status_code == 200
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
```

`TestExceptionAPI.test_create_exception_success` 0.00s

```
tests\api\test_exceptions.py:129: in test_create_exception_success
    assert response.status_code == 200
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
```

`TestExceptionAPI.test_create_exception_invalid_type` 0.00s

```
tests\api\test_exceptions.py:152: in test_create_exception_invalid_type
    assert response.status_code == 400
E   assert 404 == 400
E    +  where 404 = <Response [404 Not Found]>.status_code
```

`TestExceptionAPI.test_get_exception_detail_not_found` 0.00s

```
tests\api\test_exceptions.py:182: in test_get_exception_detail_not_found
    assert response.status_code == 200
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
```

`TestExceptionAPI.test_replan_exception_not_found` 0.00s

```
tests\api\test_exceptions.py:243: in test_replan_exception_not_found
    assert response.status_code == 200
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
```

### tests\api\test_nodes.py

`TestGetNodes.test_get_nodes_empty` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_nodes.py:46: in test_get_nodes_empty
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetNodes.test_get_nodes_with_data` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_nodes.py:96: in test_get_nodes_with_data
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateStorageCenter.test_create_storage_center_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_nodes.py:135: in test_create_storage_center_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateStorageCenter.test_create_storage_center_duplicate_code` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_nodes.py:191: in test_create_storage_center_duplicate_code
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteStorageCenter.test_delete_storage_center_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_nodes.py:250: in test_delete_storage_center_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteStorageCenter.test_delete_storage_center_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_nodes.py:282: in test_delete_storage_center_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_orders.py

`TestGetOrders.test_get_orders_empty` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_orders.py:57: in test_get_orders_empty
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetOrders.test_get_orders_with_data` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_orders.py:118: in test_get_orders_with_data
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateOrder.test_create_order_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_orders.py:171: in test_create_order_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateOrder.test_create_order_missing_goods` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_orders.py:232: in test_create_order_missing_goods
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteOrder.test_delete_order_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_orders.py:297: in test_delete_order_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteOrder.test_delete_order_delivering_status` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_orders.py:360: in test_delete_order_delivering_status
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_routes.py

`TestGetRoutes.test_get_routes_empty` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_routes.py:42: in test_get_routes_empty
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetRoutes.test_get_routes_with_data` 0.18s

```
tests\api\test_routes.py:90: in test_get_routes_with_data
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

`TestGetRouteDetail.test_get_route_detail_success` 0.17s

```
tests\api\test_routes.py:154: in test_get_route_detail_success
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

`TestGetRouteDetail.test_get_route_detail_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_routes.py:201: in test_get_route_detail_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetRouteCoordinates.test_get_route_coordinates_success` 0.18s

```
tests\api\test_routes.py:250: in test_get_route_coordinates_success
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

`TestGetRouteCoordinates.test_get_route_coordinates_vehicle_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_routes.py:298: in test_get_route_coordinates_vehicle_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_schedule.py

`TestCreateGlobalSchedule.test_create_global_schedule_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_schedule.py:160: in test_create_global_schedule_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateGlobalSchedule.test_create_global_schedule_no_pending_orders` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_schedule.py:198: in test_create_global_schedule_no_pending_orders
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateGlobalSchedule.test_create_global_schedule_manager_forbidden` 0.17s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_schedule.py:232: in test_create_global_schedule_manager_forbidden
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('manager', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetGlobalSchedules.test_get_global_schedules_empty` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_schedule.py:269: in test_get_global_schedules_empty
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetGlobalScheduleDetail.test_get_global_schedule_detail_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_schedule.py:316: in test_get_global_schedule_detail_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_simulation.py

`TestDeliverPackages.test_deliver_success` 0.17s

```
tests\api\test_simulation.py:69: in test_deliver_success
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

`TestDeliverPackages.test_deliver_no_params` 0.18s

```
tests\api\test_simulation.py:162: in test_deliver_no_params
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

`TestDeliverPackages.test_deliver_package_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_simulation.py:226: in test_deliver_package_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### tests\api\test_vehicles.py

`TestGetVehicles.test_get_vehicles_empty` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_vehicles.py:42: in test_get_vehicles_empty
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestGetVehicles.test_get_vehicles_with_data` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_vehicles.py:102: in test_get_vehicles_with_data
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateVehicle.test_create_vehicle_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_vehicles.py:153: in test_create_vehicle_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestCreateVehicle.test_create_vehicle_duplicate_code` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_vehicles.py:218: in test_create_vehicle_duplicate_code
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteVehicle.test_delete_vehicle_success` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_vehicles.py:286: in test_delete_vehicle_success
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

`TestDeleteVehicle.test_delete_vehicle_not_found` 0.18s

```
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.OperationalError: no such table: users

The above exception was the direct cause of the following exception:
tests\api\test_vehicles.py:318: in test_delete_vehicle_not_found
    login_resp = client.post(
.venv\Lib\site-packages\starlette\testclient.py:555: in post
    return super().post(
.venv\Lib\site-packages\httpx\_client.py:1144: in post
    return self.request(
.venv\Lib\site-packages\starlette\testclient.py:454: in request
    return super().request(
.venv\Lib\site-packages\httpx\_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:914: in send
    response = self._send_handling_auth(
.venv\Lib\site-packages\httpx\_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv\Lib\site-packages\httpx\_client.py:979: in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\httpx\_client.py:1014: in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\starlette\testclient.py:356: in handle_request
    raise exc
.venv\Lib\site-packages\starlette\testclient.py:353: in handle_request
    portal.call(self.app, scope, receive, send)
.venv\Lib\site-packages\anyio\from_thread.py:334: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
D:\Python\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
.venv\Lib\site-packages\anyio\from_thread.py:259: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\applications.py:1162: in __call__
    await super().__call__(scope, receive, send)
.venv\Lib\site-packages\starlette\applications.py:90: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\errors.py:186: in __call__
    raise exc
.venv\Lib\site-packages\starlette\middleware\errors.py:164: in __call__
    await self.app(scope, receive, _send)
.venv\Lib\site-packages\starlette\middleware\cors.py:88: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\middleware\exceptions.py:63: in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py:18: in __call__
    await self.app(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:660: in __call__
    await self.middleware_stack(scope, receive, send)
.venv\Lib\site-packages\starlette\routing.py:680: in app
    await route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1574: in handle
    await self.original_router.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:2012: in handle
    await included_router._handle_selected(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1594: in _handle_selected
    await original_route.handle(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:1183: in handle
    await app(scope, receive, send)
.venv\Lib\site-packages\fastapi\routing.py:143: in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
.venv\Lib\site-packages\starlette\_exception_handler.py:53: in wrapped_app
    raise exc
.venv\Lib\site-packages\starlette\_exception_handler.py:42: in wrapped_app
    await app(scope, receive, sender)
.venv\Lib\site-packages\fastapi\routing.py:129: in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\fastapi\routing.py:683: in app
    raw_response = await run_endpoint_function(
.venv\Lib\site-packages\fastapi\routing.py:337: in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
api\auth.py:22: in login
    user = authenticate_user(db, credentials.username, credentials.password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:43: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2766: in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2372: in execute
    return self._execute_internal(
.venv\Lib\site-packages\sqlalchemy\orm\session.py:2270: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
.venv\Lib\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
.venv\Lib\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
.venv\Lib\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
.venv\Lib\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
.venv\Lib\site-packages\sqlalchemy\engine\default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
E   [SQL: SELECT users.id AS users_id, users.username AS users_username, users.password_hash AS users_password_hash, users.role AS users_role, users.display_name AS users_display_name, users.is_active AS users_is_active, users.created_at AS users_created_at, users.updated_at AS users_updated_at 
E   FROM users 
E   WHERE users.username = ?
E    LIMIT ? OFFSET ?]
E   [parameters: ('testuser', 1, 0)]
E   (Background on this error at: https://sqlalche.me/e/20/e3q8)
```

## 2 passed

### tests\api\test_auth.py

`TestLogin.test_login_missing_params` 0.00s

### tests\api\test_schedule.py

`TestGetGlobalScheduleDetail.test_get_global_schedule_detail_success` 0.00s

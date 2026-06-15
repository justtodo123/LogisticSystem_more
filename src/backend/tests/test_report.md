# Test Report

*Report generated on 15-Jun-2026 at 09:53:11 by [pytest-md]*

[pytest-md]: https://github.com/hackebrot/pytest-md

## Summary

10 tests ran in 2.33 seconds

- 7 failed
- 3 passed

## 7 failed

### tests\unit\services\test_auth_service.py

`TestCreateAccessToken.test_create_access_token` 0.20s

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

`TestAuthenticateUser.test_authenticate_user_success` 0.17s

```
tests\unit\services\test_auth_service.py:138: in test_authenticate_user_success
    authenticated_user = authenticate_user("testuser", "123456", db_session)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services\auth_service.py:39: in authenticate_user
    user = db.query(User).filter(User.username == username).first()
           ^^^^^^^^
E   AttributeError: 'str' object has no attribute 'query'
```

`TestAuthenticateUser.test_authenticate_user_wrong_password` 0.18s

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

`TestGetUserByUsername.test_get_user_by_username_success` 0.17s

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

## 3 passed

### tests\unit\services\test_auth_service.py

`TestGetPasswordHash.test_get_password_hash` 0.52s

`TestVerifyPassword.test_verify_password_correct` 0.34s

`TestVerifyPassword.test_verify_password_wrong` 0.35s

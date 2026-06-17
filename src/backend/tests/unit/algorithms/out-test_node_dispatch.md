============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-9.1.0, pluggy-1.6.0 -- D:\Git Demo\LogisticSystem\src\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Git Demo\LogisticSystem\src\backend
plugins: anyio-4.13.0, asyncio-1.4.0, md-0.2.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 5 items

tests/test_algorithms/test_node_dispatch.py::TestDemoModeTrue::test_demo_mode_true_runs_both_levels PASSED [ 20%]
tests/test_algorithms/test_node_dispatch.py::TestDemoModeFalse::test_first_call_only_l0_to_l1 PASSED [ 40%]
tests/test_algorithms/test_node_dispatch.py::TestDemoModeFalse::test_second_call_only_l1_to_l2 PASSED [ 60%]
tests/test_algorithms/test_node_dispatch.py::TestNodeDispatchNoVehicle::test_no_vehicle_raises_error PASSED [ 80%]
tests/test_algorithms/test_node_dispatch.py::TestNodeDispatchWrongStatus::test_wrong_status_raises_error PASSED [100%]

============================== warnings summary ===============================
config\database.py:6
  D:\Git Demo\LogisticSystem\src\backend\config\database.py:6: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class Settings(BaseSettings):

tests\test_algorithms\test_node_dispatch.py:22
  D:\Git Demo\LogisticSystem\src\backend\tests\test_algorithms\test_node_dispatch.py:22: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.unit

tests\test_algorithms\test_node_dispatch.py:96
  D:\Git Demo\LogisticSystem\src\backend\tests\test_algorithms\test_node_dispatch.py:96: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.unit

tests\test_algorithms\test_node_dispatch.py:154
  D:\Git Demo\LogisticSystem\src\backend\tests\test_algorithms\test_node_dispatch.py:154: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.unit

tests\test_algorithms\test_node_dispatch.py:237
  D:\Git Demo\LogisticSystem\src\backend\tests\test_algorithms\test_node_dispatch.py:237: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.unit

tests\test_algorithms\test_node_dispatch.py:282
  D:\Git Demo\LogisticSystem\src\backend\tests\test_algorithms\test_node_dispatch.py:282: PytestUnknownMarkWarning: Unknown pytest.mark.unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.unit

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 5 passed, 6 warnings in 0.17s ========================

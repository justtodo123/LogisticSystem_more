@echo off
cd /d "%~dp0"
echo Running Phase 5 tests...
python -m pytest tests/test_route_planning.py tests/test_route_service.py tests/test_routes_api.py -v
echo.
echo Tests completed. Press any key to exit...
pause > nul

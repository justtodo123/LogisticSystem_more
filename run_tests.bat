@echo off
cd /d "d:\Git Demo\LogisticSystem\src\backend"
call .venv\Scripts\activate.bat
pytest tests/unit/algorithms/ -v > d:\test_result.txt 2>&1
echo Exit Code: %ERRORLEVEL% >> d:\test_result.txt

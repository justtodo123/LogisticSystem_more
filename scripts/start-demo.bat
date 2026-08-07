@echo off
REM One-click demo launcher for DeepSeek Smart Logistics Platform
REM This batch calls start-demo.ps1 with proper encoding and logging.

cd /d "%~dp0.."

echo Starting DeepSeek Smart Logistics Platform...
echo Log: out-start-demo.md
echo.

powershell -NoLogo -NonInteractive -File "scripts\start-demo.ps1" 2>&1 | findstr /V "^$"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Startup failed. Check out-start-demo.md for details.
    pause
    exit /b %ERRORLEVEL%
)

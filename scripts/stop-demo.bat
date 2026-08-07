@echo off
REM One-click stop script for DeepSeek Smart Logistics Platform demo services
REM This batch calls stop-demo.ps1 with proper encoding and logging.

cd /d "%~dp0.."

echo Stopping DeepSeek Smart Logistics Platform services...
echo Log: out-stop-demo.md
echo.

powershell -NoLogo -NonInteractive -File "scripts\stop-demo.ps1" > out-stop-demo.md 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some ports may still be occupied. Check out-stop-demo.md for details.
    pause
    exit /b %ERRORLEVEL%
)

echo Services stopped successfully.

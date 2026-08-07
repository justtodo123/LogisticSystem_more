# One-click demo startup script for DeepSeek Logistic System
# Usage: powershell -NoLogo -NonInteractive -OutputEncoding UTF8 -File scripts/start-demo.ps1
# Or use the companion start-demo.bat wrapper.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$BackendDir = Join-Path $ProjectRoot "src\backend"
$FrontendDir = Join-Path $ProjectRoot "src\frontend"
$LogFile = Join-Path $ProjectRoot "out-start-demo.md"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

# Initialize log
$startTime = Get-Date
@"
# Demo Startup Log
**Started**: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))
**Project**: $(Join-Path $ProjectRoot "")
"@ | Set-Content -Path $LogFile

Write-Log "=== DeepSeek Smart Logistics Platform - Demo Startup ==="
Write-Log ""

# ------------------------------------------------------------
# Step 1: Preflight Checks
# ------------------------------------------------------------
Write-Log "[1/6] Checking prerequisites..."

$errors = @()

# Python check
try {
    $pyVersion = python --version 2>&1
    Write-Log "  Python: $pyVersion"
} catch {
    $errors += "Python not found. Please install Python 3.11+ and add to PATH."
}

# Node check
try {
    $nodeVersion = node --version 2>&1
    Write-Log "  Node:   $nodeVersion"
} catch {
    $errors += "Node.js not found. Please install Node 18+ and add to PATH."
}

# npm check
try {
    $npmVersion = npm --version 2>&1
    Write-Log "  npm:    $npmVersion"
} catch {
    $errors += "npm not found. Please install Node 18+ with npm."
}

if ($errors.Count -gt 0) {
    Write-Log ""
    Write-Log "ERROR: Prerequisites check failed:"
    foreach ($e in $errors) { Write-Log "  - $e" }
    exit 1
}

# ------------------------------------------------------------
# Step 2: Virtual environment & dependencies
# ------------------------------------------------------------
Write-Log ""
Write-Log "[2/6] Setting up backend virtual environment..."

if (-not (Test-Path (Join-Path $BackendDir ".venv"))) {
    Write-Log "  Creating virtual environment..."
    Push-Location $BackendDir
    python -m venv .venv
    Pop-Location
}

# Install dependencies using venv python directly (avoids dot-sourcing issues)
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (Test-Path $PythonExe) {
    Write-Log "  Using existing venv python: $PythonExe"
    try {
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $PythonExe -m pip install -q -r (Join-Path $BackendDir "requirements.txt") 2>&1 | Out-Null
        $ErrorActionPreference = $prevEAP
        if ($LASTEXITCODE -ne 0) {
            Write-Log "  WARNING: pip install returned exit code $LASTEXITCODE. Trying to continue..."
        } else {
            Write-Log "  Dependencies verified/installed successfully."
        }
    } catch {
        Write-Log "  WARNING: pip install threw exception: $_"
        Write-Log "  Attempting to continue (dependencies may already be installed)."
    }
} else {
    Write-Log "  ERROR: Python venv not found at $PythonExe"
    Write-Log "  Please run: cd src\backend && python -m venv .venv"
    exit 1
}

# Check/create .env
$EnvFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Log "  Creating .env from .env.example..."
    Copy-Item (Join-Path $BackendDir ".env.example") $EnvFile
    Write-Log "  INFO: Generated default .env. Edit $EnvFile to configure DEEPSEEK_API_KEY for AI features."
}

# ------------------------------------------------------------
# Step 3: Initialize demo data
# ------------------------------------------------------------
Write-Log ""
Write-Log "[3/6] Initializing demo data..."

Push-Location $BackendDir
try {
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $PythonExe -m scripts.init_demo_data 2>&1 | ForEach-Object { Write-Log "  $_" }
    $ErrorActionPreference = $prevEAP
    Write-Log "  Demo data initialized."
} catch {
    Write-Log "  WARNING: init_demo_data failed: $_"
    Write-Log "  Attempting to continue (database may already exist)."
}
Pop-Location

# ------------------------------------------------------------
# Step 4: Check port availability & start backend
# ------------------------------------------------------------
Write-Log ""
Write-Log "[4/6] Starting backend (port 8000)..."

$port8000 = netstat -ano 2>$null | Select-String ":8000 " | Select-String "LISTENING"
if ($port8000) {
    Write-Log "  Port 8000 is in use. Attempting to free it..."
    $existingPid = ($port8000 -split '\s+')[-1]
    if ($existingPid -match '^\d+$') {
        try {
            Stop-Process -Id ([int]$existingPid) -Force -ErrorAction Stop
            Write-Log "  Stopped existing process (PID: $existingPid)."
            Start-Sleep -Seconds 2
        } catch {
            Write-Log "  WARNING: Could not stop PID $existingPid. Backend start may fail."
        }
    }
}

$backendLog = Join-Path $ProjectRoot "out-backend.md"

# Start uvicorn in background using venv python
$backendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $BackendDir `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError (Join-Path $ProjectRoot "out-backend-err.md")

# ------------------------------------------------------------
# Step 5: Health check (wait up to 30s)
# ------------------------------------------------------------
Write-Log ""
Write-Log "[5/6] Waiting for backend health check..."

$maxRetries = 30
$healthy = $false
for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        # Use Python urllib for reliable health check (Invoke-WebRequest can fail in non-interactive context)
        $checkScript = "import urllib.request,json; r=urllib.request.urlopen('http://localhost:8000/api/health',timeout=3); d=json.loads(r.read()); print('OK' if d.get('code')==0 else 'FAIL')"
        $checkResult = & $PythonExe -c $checkScript 2>$null
        if ($checkResult -eq "OK") {
            $healthy = $true
            Write-Log "  Backend is healthy! (attempt $i)"
            break
        }
    } catch {
        # ignore, retry
    }
    Start-Sleep -Seconds 1
}

if (-not $healthy) {
    Write-Log "  ERROR: Backend did not become healthy within $maxRetries seconds."
    Write-Log "  Check backend log. Stopping backend process..."
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# ------------------------------------------------------------
# Step 6: Start frontend
# ------------------------------------------------------------
Write-Log ""
Write-Log "[6/6] Starting frontend (port 5173)..."

# Check frontend node_modules
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Log "  Installing frontend dependencies..."
    Push-Location $FrontendDir
    npm install 2>&1 | Out-Null
    Pop-Location
    Write-Log "  Frontend dependencies installed."
}

# Check/create .env.local
$FrontendEnv = Join-Path $FrontendDir ".env.local"
if (-not (Test-Path $FrontendEnv)) {
    Write-Log "  Creating .env.local from .env.example..."
    Copy-Item (Join-Path $FrontendDir ".env.example") $FrontendEnv
    Write-Host "  NOTE: Set VITE_USE_MOCK_*=false in .env.local to connect to real backend."
}

# Start frontend
$frontendProc = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory $FrontendDir `
    -WindowStyle Hidden `
    -PassThru

Write-Log "  Frontend started (PID: $($frontendProc.Id))"

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
Write-Log ""
Write-Log "============================================"
Write-Log "  Demo startup complete!"
Write-Log "  Backend API : http://localhost:8000/docs"
Write-Log "  Frontend    : http://localhost:5173"
Write-Log "  Health      : http://localhost:8000/api/health"
Write-Log ""
Write-Log "  Demo accounts:"
Write-Log "    dispatcher / 123456 (read-write)"
Write-Log "    manager    / 123456 (read-only)"
Write-Log ""
Write-Log "  Backend PID : $($backendProc.Id)"
Write-Log "  Frontend PID: $($frontendProc.Id)"
Write-Log "============================================"

# Open browser
Start-Process "http://localhost:5173"

# Keep script running until Ctrl+C
Write-Log ""
Write-Log "Demo is running. Press Ctrl+C to stop both services."
Write-Log ""
Write-Host ""
Write-Host "Demo is running. Press Ctrl+C to stop both services." -ForegroundColor Green

# Handle Ctrl+C: cleanup - kill by port scan, not tracked PID
function Cleanup-Services {
    Write-Log ""
    Write-Log "Shutting down services..."
    # Kill processes on port 8000
    $p8000 = netstat -ano 2>$null | Select-String ":8000 " | Select-String "LISTENING"
    if ($p8000) {
        $pid8000 = ($p8000 -split '\s+')[-1]
        if ($pid8000 -match '^\d+$' -and $pid8000 -ne '0') {
            Stop-Process -Id ([int]$pid8000) -Force -ErrorAction SilentlyContinue
            Write-Log "  Backend stopped (PID: $pid8000)."
        }
    }
    # Kill processes on port 5173
    $p5173 = netstat -ano 2>$null | Select-String ":5173 " | Select-String "LISTENING"
    if ($p5173) {
        $pid5173 = ($p5173 -split '\s+')[-1]
        if ($pid5173 -match '^\d+$' -and $pid5173 -ne '0') {
            Stop-Process -Id ([int]$pid5173) -Force -ErrorAction SilentlyContinue
            Write-Log "  Frontend stopped (PID: $pid5173)."
        }
    }
    $endTime = Get-Date
    $elapsed = $endTime - $startTime
    Write-Log ""
    Write-Log "Demo session ended. Duration: $($elapsed.ToString('hh\:mm\:ss'))"
    Write-Log "Full log: $LogFile"
}

try {
    # Monitor via periodic health check, not process tracking
    # (Process tracking can fail in non-interactive execution contexts)
    $consecutiveHealthFails = 0
    while ($true) {
        Start-Sleep -Seconds 5
        # Health check backend
        try {
            $checkScript = "import urllib.request,json; r=urllib.request.urlopen('http://localhost:8000/api/health',timeout=3); d=json.loads(r.read()); print('OK' if d.get('code')==0 else 'FAIL')"
            $checkResult = & $PythonExe -c $checkScript 2>$null
            if ($checkResult -eq "OK") {
                $consecutiveHealthFails = 0
            } else {
                $consecutiveHealthFails++
                Write-Log "WARNING: Backend health check failed ($consecutiveHealthFails/5)"
            }
        } catch {
            $consecutiveHealthFails++
            Write-Log "WARNING: Backend health check error ($consecutiveHealthFails/5)"
        }
        if ($consecutiveHealthFails -ge 5) {
            Write-Log "ERROR: Backend health check failed 5 times consecutively. Exiting."
            break
        }
    }
} finally {
    Cleanup-Services
}

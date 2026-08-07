# One-click stop script for DeepSeek Logistic System demo services
# Usage: powershell -NoLogo -NonInteractive -OutputEncoding UTF8 -File scripts/stop-demo.ps1
# Or use the companion stop-demo.bat wrapper.

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$LogFile = Join-Path $ProjectRoot "out-stop-demo.md"

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
# Demo Stop Log
**Started**: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))
**Project**: $(Join-Path $ProjectRoot "")
"@ | Set-Content -Path $LogFile

Write-Log "=== DeepSeek Smart Logistics Platform - Stop Demo Services ==="
Write-Log ""

# ------------------------------------------------------------
# Step 1: Scan and kill backend (port 8000)
# ------------------------------------------------------------
Write-Log "[1/2] Stopping backend (port 8000)..."

$killedBackend = $false
$p8000 = netstat -ano 2>$null | Select-String ":8000 " | Select-String "LISTENING"
if ($p8000) {
    foreach ($line in $p8000) {
        $parts = ($line -split '\s+') | Where-Object { $_ -ne '' }
        $pid8000 = $parts[-1]
        if ($pid8000 -match '^\d+$' -and $pid8000 -ne '0') {
            try {
                $procInfo = Get-Process -Id ([int]$pid8000) -ErrorAction SilentlyContinue
                $procName = if ($procInfo) { $procInfo.ProcessName } else { "unknown" }
                Stop-Process -Id ([int]$pid8000) -Force -ErrorAction Stop
                Write-Log "  Stopped backend: $procName (PID: $pid8000)"
                $killedBackend = $true
            } catch {
                Write-Log "  WARNING: Failed to stop PID $pid8000 : $_"
            }
        }
    }
}
if (-not $killedBackend) {
    Write-Log "  No backend process found on port 8000."
}

# ------------------------------------------------------------
# Step 2: Scan and kill frontend (port 5173)
# ------------------------------------------------------------
Write-Log ""
Write-Log "[2/2] Stopping frontend (port 5173)..."

$killedFrontend = $false
$p5173 = netstat -ano 2>$null | Select-String ":5173 " | Select-String "LISTENING"
if ($p5173) {
    foreach ($line in $p5173) {
        $parts = ($line -split '\s+') | Where-Object { $_ -ne '' }
        $pid5173 = $parts[-1]
        if ($pid5173 -match '^\d+$' -and $pid5173 -ne '0') {
            try {
                $procInfo = Get-Process -Id ([int]$pid5173) -ErrorAction SilentlyContinue
                $procName = if ($procInfo) { $procInfo.ProcessName } else { "unknown" }
                Stop-Process -Id ([int]$pid5173) -Force -ErrorAction Stop
                Write-Log "  Stopped frontend: $procName (PID: $pid5173)"
                $killedFrontend = $true
            } catch {
                Write-Log "  WARNING: Failed to stop PID $pid5173 : $_"
            }
        }
    }
}
if (-not $killedFrontend) {
    Write-Log "  No frontend process found on port 5173."
}

# ------------------------------------------------------------
# Final verification
# ------------------------------------------------------------
Write-Log ""
Write-Log "Verifying ports are released..."

$still8000 = netstat -ano 2>$null | Select-String ":8000 " | Select-String "LISTENING"
$still5173 = netstat -ano 2>$null | Select-String ":5173 " | Select-String "LISTENING"

$strictFailures = 0
if ($still8000) {
    # Check if the remaining PID is actually reachable (zombie entries can linger)
    $remainingPid = ($still8000 -split '\s+' | Where-Object { $_ -ne '' })[-1]
    $procExists = Get-Process -Id ([int]$remainingPid) -ErrorAction SilentlyContinue
    if ($procExists) {
        Write-Log "  WARNING: Port 8000 still occupied by $($procExists.ProcessName) (PID: $remainingPid)."
        $strictFailures++
    } else {
        Write-Log "  Port 8000: zombie entry (PID $remainingPid no longer exists). Will auto-clear."
    }
}
if ($still5173) {
    $remainingPid = ($still5173 -split '\s+' | Where-Object { $_ -ne '' })[-1]
    $procExists = Get-Process -Id ([int]$remainingPid) -ErrorAction SilentlyContinue
    if ($procExists) {
        Write-Log "  WARNING: Port 5173 still occupied by $($procExists.ProcessName) (PID: $remainingPid)."
        $strictFailures++
    } else {
        Write-Log "  Port 5173: zombie entry (PID $remainingPid no longer exists). Will auto-clear."
    }
}

if ($strictFailures -eq 0) {
    Write-Log "  All demo services stopped."
    $resultCode = 0
} else {
    Write-Log "  $strictFailures port(s) still occupied by running processes."
    Write-Log "  Try: tasklist | findstr python or tasklist | findstr node to locate remaining processes."
    $resultCode = 1
}

$endTime = Get-Date
$elapsed = $endTime - $startTime
Write-Log ""
Write-Log "=== Stop completed in $($elapsed.TotalSeconds.ToString('0.0'))s ==="
Write-Log "Full log: $LogFile"

exit $resultCode

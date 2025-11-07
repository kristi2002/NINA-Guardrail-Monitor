# PowerShell script to forcefully kill Kafka and ZooKeeper processes
# This handles the case where ports are still in use

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Killing Kafka and ZooKeeper Processes" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Kill all Java processes that might be Kafka or ZooKeeper
Write-Host "Step 1: Finding Java processes..." -ForegroundColor Yellow
$javaProcesses = Get-Process -Name "java" -ErrorAction SilentlyContinue

if ($javaProcesses) {
    Write-Host "Found $($javaProcesses.Count) Java process(es)" -ForegroundColor Cyan
    
    foreach ($proc in $javaProcesses) {
        try {
            $commandLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($commandLine -like "*kafka*" -or $commandLine -like "*zookeeper*" -or $commandLine -like "*QuorumPeerMain*") {
                Write-Host "Killing process $($proc.Id): $($commandLine.Substring(0, [Math]::Min(80, $commandLine.Length)))..." -ForegroundColor Yellow
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                Write-Host "OK - Process $($proc.Id) killed" -ForegroundColor Green
            }
        } catch {
            Write-Host "WARNING - Could not kill process $($proc.Id): $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "OK - No Java processes found" -ForegroundColor Green
}
Write-Host ""

# Check what's using port 2181 (ZooKeeper)
Write-Host "Step 2: Checking port 2181 (ZooKeeper)..." -ForegroundColor Yellow
try {
    $port2181 = Get-NetTCPConnection -LocalPort 2181 -ErrorAction SilentlyContinue
    if ($port2181) {
        Write-Host "WARNING - Port 2181 is still in use by PID: $($port2181.OwningProcess)" -ForegroundColor Yellow
        $proc = Get-Process -Id $port2181.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Killing process $($proc.Id) ($($proc.ProcessName))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "OK - Process killed" -ForegroundColor Green
        }
    } else {
        Write-Host "OK - Port 2181 is free" -ForegroundColor Green
    }
} catch {
    Write-Host "OK - Port 2181 check completed" -ForegroundColor Green
}
Write-Host ""

# Check what's using port 9092 (Kafka)
Write-Host "Step 3: Checking port 9092 (Kafka)..." -ForegroundColor Yellow
try {
    $port9092 = Get-NetTCPConnection -LocalPort 9092 -ErrorAction SilentlyContinue
    if ($port9092) {
        Write-Host "WARNING - Port 9092 is still in use by PID: $($port9092.OwningProcess)" -ForegroundColor Yellow
        $proc = Get-Process -Id $port9092.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Killing process $($proc.Id) ($($proc.ProcessName))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "OK - Process killed" -ForegroundColor Green
        }
    } else {
        Write-Host "OK - Port 9092 is free" -ForegroundColor Green
    }
} catch {
    Write-Host "OK - Port 9092 check completed" -ForegroundColor Green
}
Write-Host ""

# Wait a moment for ports to be released
Write-Host "Step 4: Waiting for ports to be released..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Verify ports are free
$port2181Final = Get-NetTCPConnection -LocalPort 2181 -ErrorAction SilentlyContinue
$port9092Final = Get-NetTCPConnection -LocalPort 9092 -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if (-not $port2181Final -and -not $port9092Final) {
    Write-Host "OK - Both ports are now free" -ForegroundColor Green
    Write-Host "Port 2181 (ZooKeeper): FREE" -ForegroundColor Green
    Write-Host "Port 9092 (Kafka): FREE" -ForegroundColor Green
} else {
    Write-Host "WARNING - Some ports may still be in use" -ForegroundColor Yellow
    if ($port2181Final) {
        Write-Host "Port 2181: IN USE by PID $($port2181Final.OwningProcess)" -ForegroundColor Red
    } else {
        Write-Host "Port 2181: FREE" -ForegroundColor Green
    }
    if ($port9092Final) {
        Write-Host "Port 9092: IN USE by PID $($port9092Final.OwningProcess)" -ForegroundColor Red
    } else {
        Write-Host "Port 9092: FREE" -ForegroundColor Green
    }
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now you can:" -ForegroundColor Yellow
Write-Host "1. Start ZooKeeper" -ForegroundColor White
Write-Host "2. Start Kafka" -ForegroundColor White
Write-Host "3. Run: python scripts\create_guardrail_control_topic.py" -ForegroundColor White
Write-Host ""


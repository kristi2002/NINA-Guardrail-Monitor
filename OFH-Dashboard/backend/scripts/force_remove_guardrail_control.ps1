# PowerShell script to forcefully remove the guardrail.control-0 directory
# This handles Windows file locking and permission issues

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$PROBLEM_DIR = "guardrail.control-0"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Force Removing guardrail.control-0 Directory" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop all processes
Write-Host "Step 1: Stopping Kafka and ZooKeeper..." -ForegroundColor Yellow
Get-Process -Name "java" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmd -like "*kafka*" -or $cmd -like "*zookeeper*") {
            Write-Host "  Stopping process $($_.Id)..." -ForegroundColor Cyan
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Ignore
    }
}
Start-Sleep -Seconds 5
Write-Host "OK - Processes stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Wait a bit for file handles to be released
Write-Host "Step 2: Waiting for file handles to be released..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "OK - Wait complete" -ForegroundColor Green
Write-Host ""

# Step 3: Check if directory exists
$dirPath = Join-Path $KAFKA_LOG_DIR $PROBLEM_DIR
Write-Host "Step 3: Removing $PROBLEM_DIR directory..." -ForegroundColor Yellow

if (-not (Test-Path $dirPath)) {
    Write-Host "OK - Directory does not exist (already removed)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Directory Already Removed" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
}

Write-Host "  Found directory: $dirPath" -ForegroundColor Cyan

# Step 4: Try multiple methods to remove the directory
Write-Host "  Attempting removal..." -ForegroundColor Cyan

# Method 1: Normal removal
try {
    Remove-Item -Path $dirPath -Recurse -Force -ErrorAction Stop
    Write-Host "  OK - Directory removed successfully (Method 1)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Success - Directory Removed" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  Method 1 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 2: Remove read-only attributes first, then delete
try {
    Write-Host "  Trying Method 2: Remove read-only attributes..." -ForegroundColor Cyan
    Get-ChildItem -Path $dirPath -Recurse -Force -ErrorAction SilentlyContinue | 
        ForEach-Object { 
            try {
                $_.IsReadOnly = $false
                if ($_.PSIsContainer -eq $false) {
                    $file = $_.FullName
                    Remove-Item -Path $file -Force -ErrorAction SilentlyContinue
                }
            } catch {
                # Ignore individual file errors
            }
        }
    Start-Sleep -Seconds 1
    Remove-Item -Path $dirPath -Recurse -Force -ErrorAction Stop
    Write-Host "  OK - Directory removed successfully (Method 2)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Success - Directory Removed" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  Method 2 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 3: Use takeown and attrib commands
try {
    Write-Host "  Trying Method 3: Using takeown and attrib..." -ForegroundColor Cyan
    Write-Host "    Taking ownership..." -ForegroundColor Gray
    & takeown /F $dirPath /R /D Y 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    
    Write-Host "    Removing attributes..." -ForegroundColor Gray
    & attrib -R "$dirPath\*.*" /S /D 2>&1 | Out-Null
    Start-Sleep -Seconds 1
    
    Write-Host "    Deleting..." -ForegroundColor Gray
    Remove-Item -Path $dirPath -Recurse -Force -ErrorAction Stop
    Write-Host "  OK - Directory removed successfully (Method 3)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Success - Directory Removed" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  Method 3 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 4: Use cmd.exe rmdir (sometimes works when PowerShell doesn't)
try {
    Write-Host "  Trying Method 4: Using cmd rmdir..." -ForegroundColor Cyan
    $cmd = "cmd.exe /c rmdir /s /q `"$dirPath`""
    Invoke-Expression $cmd 2>&1 | Out-Null
    Start-Sleep -Seconds 1
    
    if (-not (Test-Path $dirPath)) {
        Write-Host "  OK - Directory removed successfully (Method 4)" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "Success - Directory Removed" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
        exit 0
    } else {
        throw "Directory still exists"
    }
} catch {
    Write-Host "  Method 4 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# If all methods failed
Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host "ERROR - Could Not Remove Directory" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "All removal methods failed. The directory may be locked by:" -ForegroundColor Yellow
Write-Host "  1. A running process (check with Process Explorer or Handle.exe)" -ForegroundColor White
Write-Host "  2. Windows Search Indexer" -ForegroundColor White
Write-Host "  3. Antivirus software" -ForegroundColor White
Write-Host ""
Write-Host "Manual steps:" -ForegroundColor Cyan
Write-Host "  1. Close all applications that might access this directory" -ForegroundColor White
Write-Host "  2. Try deleting it manually in Windows Explorer" -ForegroundColor White
Write-Host "  3. Restart your computer if necessary" -ForegroundColor White
Write-Host "  4. Or rename it and delete later:" -ForegroundColor White
Write-Host "     Rename-Item -Path '$dirPath' -NewName 'guardrail.control-0.DELETE_ME'" -ForegroundColor Gray
Write-Host ""
exit 1


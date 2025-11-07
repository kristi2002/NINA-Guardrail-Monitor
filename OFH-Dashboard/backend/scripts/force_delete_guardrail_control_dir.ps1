# PowerShell script to forcefully delete the guardrail.control-0 directory
# This handles Windows file locking and permission issues

$dirPath = "C:\tmp\kafka-logs\guardrail.control-0"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Force Deleting guardrail.control-0 Directory" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $dirPath)) {
    Write-Host "Directory does not exist. Nothing to delete." -ForegroundColor Green
    exit 0
}

Write-Host "Directory found: $dirPath" -ForegroundColor Yellow
Write-Host ""

# Step 1: Kill all Java processes (Kafka/ZooKeeper)
Write-Host "Step 1: Stopping all Java processes..." -ForegroundColor Yellow
Get-Process -Name "java" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Stopping process $($_.Id)..." -ForegroundColor Cyan
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 5
Write-Host "OK - Java processes stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Check what's using the directory
Write-Host "Step 2: Checking for processes locking the directory..." -ForegroundColor Yellow
Write-Host "  (This may take a moment)" -ForegroundColor Gray

# Try to use handle.exe if available, otherwise skip
$handlePath = "C:\Sysinternals\handle.exe"
if (Test-Path $handlePath) {
    Write-Host "  Found handle.exe, checking locks..." -ForegroundColor Cyan
    $locks = & $handlePath -a $dirPath 2>&1 | Select-String -Pattern "java|kafka"
    if ($locks) {
        Write-Host "  Found locks:" -ForegroundColor Yellow
        $locks | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    }
} else {
    Write-Host "  handle.exe not found (optional - skipping)" -ForegroundColor Gray
}
Write-Host ""

# Step 3: Wait for file handles to be released
Write-Host "Step 3: Waiting for file handles to be released..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "OK - Wait complete" -ForegroundColor Green
Write-Host ""

# Step 4: Try multiple deletion methods
Write-Host "Step 4: Attempting deletion..." -ForegroundColor Yellow

# Method 1: Normal PowerShell deletion
try {
    Write-Host "  Trying Method 1: PowerShell Remove-Item..." -ForegroundColor Cyan
    Remove-Item -Path $dirPath -Recurse -Force -ErrorAction Stop
    Write-Host "  ✅ Success! Directory deleted (Method 1)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Directory Deleted Successfully" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  ❌ Method 1 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 2: Remove read-only attributes first
try {
    Write-Host "  Trying Method 2: Remove read-only attributes..." -ForegroundColor Cyan
    Get-ChildItem -Path $dirPath -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $_.IsReadOnly = $false
        if (-not $_.PSIsContainer) {
            $file = $_.FullName
            try {
                [System.IO.File]::SetAttributes($file, [System.IO.FileAttributes]::Normal)
            } catch {
                # Ignore
            }
        }
    }
    Start-Sleep -Seconds 1
    Remove-Item -Path $dirPath -Recurse -Force -ErrorAction Stop
    Write-Host "  ✅ Success! Directory deleted (Method 2)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Directory Deleted Successfully" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  ❌ Method 2 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 3: Use takeown and attrib
try {
    Write-Host "  Trying Method 3: Take ownership and remove attributes..." -ForegroundColor Cyan
    Write-Host "    Taking ownership..." -ForegroundColor Gray
    $result1 = & takeown /F $dirPath /R /D Y 2>&1
    Start-Sleep -Seconds 2
    
    Write-Host "    Removing attributes..." -ForegroundColor Gray
    $result2 = & attrib -R "$dirPath\*.*" /S /D 2>&1
    Start-Sleep -Seconds 1
    
    Write-Host "    Deleting..." -ForegroundColor Gray
    Remove-Item -Path $dirPath -Recurse -Force -ErrorAction Stop
    Write-Host "  ✅ Success! Directory deleted (Method 3)" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Directory Deleted Successfully" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  ❌ Method 3 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 4: Use cmd.exe rmdir
try {
    Write-Host "  Trying Method 4: CMD rmdir..." -ForegroundColor Cyan
    $cmd = "cmd.exe /c rmdir /s /q `"$dirPath`""
    Invoke-Expression $cmd 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    
    if (-not (Test-Path $dirPath)) {
        Write-Host "  ✅ Success! Directory deleted (Method 4)" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "Directory Deleted Successfully" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
        exit 0
    } else {
        throw "Directory still exists"
    }
} catch {
    Write-Host "  ❌ Method 4 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Method 5: Rename and delete later
try {
    Write-Host "  Trying Method 5: Rename directory (delete manually later)..." -ForegroundColor Cyan
    $newName = "$dirPath.DELETE_ME_$(Get-Date -Format 'yyyyMMddHHmmss')"
    Rename-Item -Path $dirPath -NewName (Split-Path $newName -Leaf) -ErrorAction Stop
    Write-Host "  ⚠️  Directory renamed to: $(Split-Path $newName -Leaf)" -ForegroundColor Yellow
    Write-Host "  You can delete it manually later or restart your computer" -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Directory Renamed (Can be deleted after restart)" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 0
} catch {
    Write-Host "  ❌ Method 5 failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# All methods failed
Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host "ERROR - Could Not Delete Directory" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "All deletion methods failed. The directory may be locked by:" -ForegroundColor Yellow
Write-Host "  1. Windows Search Indexer" -ForegroundColor White
Write-Host "  2. Antivirus software" -ForegroundColor White
Write-Host "  3. Windows Explorer (if the folder is open)" -ForegroundColor White
Write-Host "  4. Another application" -ForegroundColor White
Write-Host ""
Write-Host "Try these solutions:" -ForegroundColor Cyan
Write-Host "  1. Close Windows Explorer if the folder is open" -ForegroundColor White
Write-Host "  2. Restart your computer" -ForegroundColor White
Write-Host "  3. Use Process Explorer to find what's locking it:" -ForegroundColor White
Write-Host "     https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer" -ForegroundColor Gray
Write-Host "  4. Or just leave it - Kafka won't try to manage it anymore" -ForegroundColor White
Write-Host "     (since we deleted it from ZooKeeper)" -ForegroundColor Gray
Write-Host ""
Write-Host "The directory is: $dirPath" -ForegroundColor Yellow
Write-Host ""

exit 1


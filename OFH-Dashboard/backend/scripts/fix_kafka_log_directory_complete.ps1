# PowerShell script to completely fix Kafka log directory issues
# This handles the "all log dirs have failed" error

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$OLD_TOPIC_DIR = "guardrail.control-0"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Complete Kafka Log Directory Fix" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop all Kafka processes
Write-Host "Step 1: Stopping Kafka and ZooKeeper..." -ForegroundColor Yellow
Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    $cmd -like "*kafka*" -or $cmd -like "*zookeeper*"
} | ForEach-Object {
    Write-Host "Stopping process $($_.Id)..." -ForegroundColor Cyan
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3
Write-Host "OK - All processes stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Check if directory exists
if (-not (Test-Path $KAFKA_LOG_DIR)) {
    Write-Host "Creating Kafka log directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $KAFKA_LOG_DIR -Force | Out-Null
    Write-Host "OK - Directory created" -ForegroundColor Green
    Write-Host ""
    exit 0
}

# Step 3: Remove all lock files
Write-Host "Step 2: Removing all lock files..." -ForegroundColor Yellow
$lockFiles = Get-ChildItem -Path $KAFKA_LOG_DIR -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue
$removedLocks = 0
foreach ($lockFile in $lockFiles) {
    try {
        Remove-Item -Path $lockFile.FullName -Force -ErrorAction Stop
        $removedLocks++
        Write-Host "  Removed: $($lockFile.Name)" -ForegroundColor Gray
    } catch {
        Write-Host "  WARNING - Could not remove: $($lockFile.Name)" -ForegroundColor Yellow
    }
}
if ($removedLocks -gt 0) {
    Write-Host "OK - Removed $removedLocks lock file(s)" -ForegroundColor Green
} else {
    Write-Host "OK - No lock files found" -ForegroundColor Green
}
Write-Host ""

# Step 4: Remove the problematic old guardrail.control directory
Write-Host "Step 3: Removing old guardrail.control directory..." -ForegroundColor Yellow
$oldTopicPath = Join-Path $KAFKA_LOG_DIR $OLD_TOPIC_DIR
if (Test-Path $oldTopicPath) {
    try {
        # Try to remove read-only files
        Get-ChildItem -Path $oldTopicPath -Recurse -Force | ForEach-Object {
            $_.IsReadOnly = $false
        }
        Remove-Item -Path $oldTopicPath -Recurse -Force -ErrorAction Stop
        Write-Host "OK - Removed old topic directory: $OLD_TOPIC_DIR" -ForegroundColor Green
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "WARNING - Could not remove old directory: $errorMsg" -ForegroundColor Yellow
        Write-Host "  Attempting to take ownership and remove..." -ForegroundColor Cyan
        try {
            # Take ownership
            takeown /F $oldTopicPath /R /D Y 2>&1 | Out-Null
            # Remove read-only attribute
            attrib -R $oldTopicPath /S /D 2>&1 | Out-Null
            # Try removing again
            Remove-Item -Path $oldTopicPath -Recurse -Force -ErrorAction Stop
            Write-Host "OK - Removed old topic directory after taking ownership" -ForegroundColor Green
        } catch {
            Write-Host "ERROR - Still cannot remove. Manual intervention may be required." -ForegroundColor Red
            Write-Host "  Try running this script as Administrator" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "OK - Old topic directory not found" -ForegroundColor Green
}
Write-Host ""

# Step 5: Check and fix permissions
Write-Host "Step 4: Verifying directory permissions..." -ForegroundColor Yellow
try {
    $acl = Get-Acl $KAFKA_LOG_DIR
    $hasWrite = $false
    foreach ($access in $acl.Access) {
        if ($access.IdentityReference -like "*Authenticated Users*" -or 
            $access.IdentityReference -like "*Users*" -or
            $access.IdentityReference -like "*Everyone*") {
            if ($access.FileSystemRights -match "Write|Modify|FullControl") {
                $hasWrite = $true
                break
            }
        }
    }
    
    if (-not $hasWrite) {
        Write-Host "WARNING - Directory may not have proper write permissions" -ForegroundColor Yellow
        Write-Host "  Attempting to add write permissions..." -ForegroundColor Cyan
        $newAcl = Get-Acl $KAFKA_LOG_DIR
        $permission = "BUILTIN\Users", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow"
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
        $newAcl.SetAccessRule($accessRule)
        Set-Acl -Path $KAFKA_LOG_DIR -AclObject $newAcl
        Write-Host "OK - Permissions updated" -ForegroundColor Green
    } else {
        Write-Host "OK - Permissions look good" -ForegroundColor Green
    }
} catch {
    $errorMsg = $_.Exception.Message
    Write-Host "WARNING - Could not verify/fix permissions: $errorMsg" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Check for corrupted checkpoint files
Write-Host "Step 5: Checking checkpoint files..." -ForegroundColor Yellow
$checkpointFiles = @(
    "cleaner-offset-checkpoint",
    "log-start-offset-checkpoint",
    "recovery-point-offset-checkpoint",
    "replication-offset-checkpoint"
)

foreach ($checkpoint in $checkpointFiles) {
    $checkpointPath = Join-Path $KAFKA_LOG_DIR $checkpoint
    if (Test-Path $checkpointPath) {
        try {
            $content = Get-Content $checkpointPath -Raw -ErrorAction Stop
            if ($null -eq $content -or $content.Length -eq 0) {
                Write-Host "  Found empty checkpoint: $checkpoint - Removing..." -ForegroundColor Yellow
                Remove-Item -Path $checkpointPath -Force -ErrorAction Stop
                Write-Host "  OK - Removed empty checkpoint" -ForegroundColor Green
            } else {
                Write-Host "  OK - Checkpoint $checkpoint is valid" -ForegroundColor Gray
            }
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Host "  WARNING - Could not read checkpoint $checkpoint : $errorMsg" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# Step 7: Verify directory is accessible
Write-Host "Step 6: Testing directory write access..." -ForegroundColor Yellow
try {
    $testFile = Join-Path $KAFKA_LOG_DIR ".write_test_$(Get-Date -Format 'yyyyMMddHHmmss')"
    "test" | Out-File -FilePath $testFile -ErrorAction Stop
    Remove-Item -Path $testFile -Force -ErrorAction Stop
    Write-Host "OK - Directory is writable" -ForegroundColor Green
} catch {
    $errorMsg = $_.Exception.Message
    Write-Host "ERROR - Directory is not writable: $errorMsg" -ForegroundColor Red
    Write-Host "  You may need to run this script as Administrator" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start ZooKeeper" -ForegroundColor White
Write-Host "2. Start Kafka" -ForegroundColor White
Write-Host "3. If Kafka still fails, you may need to:" -ForegroundColor White
Write-Host "   - Delete and recreate the log directory (BACKUP FIRST!)" -ForegroundColor Gray
Write-Host "   - Or check Kafka logs for specific errors" -ForegroundColor Gray
Write-Host ""


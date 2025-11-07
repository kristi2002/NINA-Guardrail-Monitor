# PowerShell script to fix Kafka log directory issues
# This script will:
# 1. Stop Kafka if running
# 2. Remove lock files
# 3. Clean up old/corrupted topic directories
# 4. Verify directory permissions

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$OLD_TOPIC_DIR = "guardrail.control-0"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔧 Fixing Kafka Log Directory Issues" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if directory exists
if (-not (Test-Path $KAFKA_LOG_DIR)) {
    Write-Host "❌ Kafka log directory does not exist: $KAFKA_LOG_DIR" -ForegroundColor Red
    Write-Host "   Creating directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $KAFKA_LOG_DIR -Force | Out-Null
    Write-Host "   ✅ Directory created" -ForegroundColor Green
}

Write-Host "📁 Kafka log directory: $KAFKA_LOG_DIR" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check for Kafka processes
Write-Host "Step 1: Checking for running Kafka processes..." -ForegroundColor Yellow
$kafkaProcesses = Get-Process -Name "*kafka*" -ErrorAction SilentlyContinue
if ($kafkaProcesses) {
    Write-Host "   ⚠️  Found running Kafka processes. Please stop Kafka before running this script." -ForegroundColor Yellow
    Write-Host "   Processes found:" -ForegroundColor Yellow
    $kafkaProcesses | ForEach-Object { Write-Host "     - $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray }
    Write-Host ""
    $response = Read-Host "   Stop Kafka processes now? (y/n)"
    if ($response -eq 'y') {
        Write-Host "   Stopping Kafka processes..." -ForegroundColor Yellow
        $kafkaProcesses | Stop-Process -Force
        Start-Sleep -Seconds 2
        Write-Host "   ✅ Kafka processes stopped" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Please stop Kafka manually and run this script again" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "   ✅ No Kafka processes running" -ForegroundColor Green
}
Write-Host ""

# Step 2: Remove lock files
Write-Host "Step 2: Removing lock files..." -ForegroundColor Yellow
$lockFiles = Get-ChildItem -Path $KAFKA_LOG_DIR -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue
if ($lockFiles) {
    Write-Host "   Found $($lockFiles.Count) lock file(s)" -ForegroundColor Yellow
    foreach ($lockFile in $lockFiles) {
        try {
            Remove-Item -Path $lockFile.FullName -Force -ErrorAction Stop
            Write-Host "   ✅ Removed: $($lockFile.Name)" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Failed to remove: $($lockFile.Name) - $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ✅ No lock files found" -ForegroundColor Green
}
Write-Host ""

# Step 3: Clean up old guardrail.control directory
Write-Host "Step 3: Cleaning up old topic directory..." -ForegroundColor Yellow
$oldTopicPath = Join-Path $KAFKA_LOG_DIR $OLD_TOPIC_DIR
if (Test-Path $oldTopicPath) {
    Write-Host "   Found old topic directory: $OLD_TOPIC_DIR" -ForegroundColor Yellow
    Write-Host "   This directory is from the old 'guardrail.control' topic (with dot)" -ForegroundColor Gray
    Write-Host "   It should be safe to remove since we're creating 'guardrail_control' (with underscore)" -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host "   Remove old topic directory? (y/n)"
    if ($response -eq 'y') {
        try {
            Remove-Item -Path $oldTopicPath -Recurse -Force -ErrorAction Stop
            Write-Host "   ✅ Removed old topic directory" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Failed to remove directory: $_" -ForegroundColor Red
            Write-Host "   You may need to remove it manually or restart as administrator" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Keeping old directory (may cause issues)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✅ Old topic directory not found (already removed)" -ForegroundColor Green
}
Write-Host ""

# Step 4: Check for corrupted log segments
Write-Host "Step 4: Checking for corrupted log files..." -ForegroundColor Yellow
$corruptedLogs = Get-ChildItem -Path $KAFKA_LOG_DIR -Recurse -Filter "*.log" -ErrorAction SilentlyContinue | 
    Where-Object { $_.Length -eq 0 -and $_.LastWriteTime -lt (Get-Date).AddDays(-1) }
if ($corruptedLogs) {
    Write-Host "   Found $($corruptedLogs.Count) potentially corrupted log file(s)" -ForegroundColor Yellow
    Write-Host "   (Empty log files older than 1 day)" -ForegroundColor Gray
    $response = Read-Host "   Remove corrupted log files? (y/n)"
    if ($response -eq 'y') {
        foreach ($logFile in $corruptedLogs) {
            try {
                Remove-Item -Path $logFile.FullName -Force -ErrorAction Stop
                Write-Host "   ✅ Removed: $($logFile.Name)" -ForegroundColor Green
            } catch {
                Write-Host "   ⚠️  Could not remove: $($logFile.Name)" -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "   ✅ No obviously corrupted log files found" -ForegroundColor Green
}
Write-Host ""

# Step 5: Verify permissions
Write-Host "Step 5: Verifying directory permissions..." -ForegroundColor Yellow
try {
    $acl = Get-Acl $KAFKA_LOG_DIR
    $hasWriteAccess = $false
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    
    foreach ($accessRule in $acl.Access) {
        if ($accessRule.IdentityReference -eq $currentUser -or 
            $accessRule.IdentityReference -like "*Users*" -or
            $accessRule.IdentityReference -like "*Authenticated*") {
            if ($accessRule.FileSystemRights -match "Write|Modify|FullControl") {
                $hasWriteAccess = $true
                break
            }
        }
    }
    
    if ($hasWriteAccess) {
        Write-Host "   ✅ Write permissions OK" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  May not have write permissions" -ForegroundColor Yellow
        Write-Host "   Current user: $currentUser" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not verify permissions: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Log Directory Fix Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart Kafka" -ForegroundColor White
Write-Host "2. Run: python scripts\create_guardrail_control_topic.py" -ForegroundColor White
Write-Host ""


# PowerShell script to automatically fix Kafka log directory issues
# Non-interactive version - automatically fixes issues

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$OLD_TOPIC_DIR = "guardrail.control-0"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Fixing Kafka Log Directory Issues (Auto)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$issuesFixed = @()

# Step 1: Check if directory exists
if (-not (Test-Path $KAFKA_LOG_DIR)) {
    Write-Host "Creating Kafka log directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $KAFKA_LOG_DIR -Force | Out-Null
    Write-Host "OK - Directory created" -ForegroundColor Green
    $issuesFixed += "Created missing directory"
}

# Step 2: Remove lock files
Write-Host "Removing lock files..." -ForegroundColor Yellow
$lockFiles = Get-ChildItem -Path $KAFKA_LOG_DIR -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue
if ($lockFiles) {
    foreach ($lockFile in $lockFiles) {
        try {
            Remove-Item -Path $lockFile.FullName -Force -ErrorAction Stop
            Write-Host "OK - Removed lock file: $($lockFile.Name)" -ForegroundColor Green
            $issuesFixed += "Removed lock file: $($lockFile.Name)"
        } catch {
            Write-Host "WARNING - Could not remove: $($lockFile.Name)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "OK - No lock files found" -ForegroundColor Green
}

# Step 3: Remove old guardrail.control directory
Write-Host "Removing old topic directory..." -ForegroundColor Yellow
$oldTopicPath = Join-Path $KAFKA_LOG_DIR $OLD_TOPIC_DIR
if (Test-Path $oldTopicPath) {
    try {
        Remove-Item -Path $oldTopicPath -Recurse -Force -ErrorAction Stop
        Write-Host "OK - Removed old topic directory: $OLD_TOPIC_DIR" -ForegroundColor Green
        $issuesFixed += "Removed old topic directory"
    } catch {
        Write-Host "WARNING - Could not remove old directory (may be in use): $_" -ForegroundColor Yellow
        Write-Host "   You may need to stop Kafka and try again" -ForegroundColor Yellow
    }
} else {
    Write-Host "OK - Old topic directory not found" -ForegroundColor Green
}

# Step 4: Remove empty log files older than 1 day
Write-Host "Cleaning up empty log files..." -ForegroundColor Yellow
$emptyLogs = Get-ChildItem -Path $KAFKA_LOG_DIR -Recurse -Filter "*.log" -ErrorAction SilentlyContinue | 
    Where-Object { $_.Length -eq 0 -and $_.LastWriteTime -lt (Get-Date).AddDays(-1) }
if ($emptyLogs) {
    $removed = 0
    foreach ($logFile in $emptyLogs) {
        try {
            Remove-Item -Path $logFile.FullName -Force -ErrorAction Stop
            $removed++
        } catch {
            # Ignore errors
        }
    }
    if ($removed -gt 0) {
        Write-Host "OK - Removed $removed empty log file(s)" -ForegroundColor Green
        $issuesFixed += "Cleaned up empty logs"
    }
} else {
    Write-Host "OK - No empty log files to clean" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if ($issuesFixed.Count -gt 0) {
    Write-Host "Fixed Issues:" -ForegroundColor Green
    foreach ($issue in $issuesFixed) {
        Write-Host "   - $issue" -ForegroundColor Gray
    }
} else {
    Write-Host "No issues found - directory is clean" -ForegroundColor Green
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart Kafka" -ForegroundColor White
Write-Host "2. Run the create topic script" -ForegroundColor White
Write-Host ""

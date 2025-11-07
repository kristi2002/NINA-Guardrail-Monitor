# PowerShell script to fix Kafka "log dir already offline" error
# This happens when Kafka marks a directory as failed and needs to be reset

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Fixing Kafka Failed Log Directory" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Stop Kafka and ZooKeeper" -ForegroundColor White
Write-Host "2. Check for corrupted partition files" -ForegroundColor White
Write-Host "3. Remove lock files" -ForegroundColor White
Write-Host "4. Check and fix the problematic __consumer_offsets-42 partition" -ForegroundColor White
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
        # Ignore errors
    }
}
Start-Sleep -Seconds 5
Write-Host "OK - Processes stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Check the problematic partition
Write-Host "Step 2: Checking __consumer_offsets-42 partition..." -ForegroundColor Yellow
$problemPartition = Join-Path $KAFKA_LOG_DIR "__consumer_offsets-42"
if (Test-Path $problemPartition) {
    Write-Host "  Found partition directory" -ForegroundColor Cyan
    
    # Check for segment files
    $segmentFiles = Get-ChildItem -Path $problemPartition -Filter "*.log" -ErrorAction SilentlyContinue
    $indexFiles = Get-ChildItem -Path $problemPartition -Filter "*.index" -ErrorAction SilentlyContinue
    $timeIndexFiles = Get-ChildItem -Path $problemPartition -Filter "*.timeindex" -ErrorAction SilentlyContinue
    
    Write-Host "  Segment files: $($segmentFiles.Count)" -ForegroundColor Gray
    Write-Host "  Index files: $($indexFiles.Count)" -ForegroundColor Gray
    Write-Host "  Time index files: $($timeIndexFiles.Count)" -ForegroundColor Gray
    
    # Check for empty or zero-length files
    $emptyFiles = Get-ChildItem -Path $problemPartition -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -eq 0 }
    if ($emptyFiles) {
        Write-Host "  WARNING - Found $($emptyFiles.Count) empty file(s)" -ForegroundColor Yellow
        foreach ($emptyFile in $emptyFiles) {
            Write-Host "    Removing empty file: $($emptyFile.Name)" -ForegroundColor Gray
            Remove-Item -Path $emptyFile.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Check for leader-epoch-checkpoint file
    $checkpointFile = Join-Path $problemPartition "leader-epoch-checkpoint"
    if (Test-Path $checkpointFile) {
        try {
            $content = Get-Content $checkpointFile -Raw -ErrorAction Stop
            if ($null -eq $content -or $content.Trim().Length -eq 0) {
                Write-Host "  WARNING - Empty leader-epoch-checkpoint, recreating..." -ForegroundColor Yellow
                "0`n0" | Out-File -FilePath $checkpointFile -NoNewline -Encoding ASCII -ErrorAction Stop
                Write-Host "  OK - Recreated checkpoint file" -ForegroundColor Green
            }
        } catch {
            Write-Host "  WARNING - Could not read checkpoint file: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  Partition directory not found (this is OK)" -ForegroundColor Green
}
Write-Host ""

# Step 3: Remove all lock files
Write-Host "Step 3: Removing lock files..." -ForegroundColor Yellow
$lockFiles = Get-ChildItem -Path $KAFKA_LOG_DIR -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue
$removedLocks = 0
foreach ($lockFile in $lockFiles) {
    try {
        Remove-Item -Path $lockFile.FullName -Force -ErrorAction Stop
        $removedLocks++
    } catch {
        # Ignore errors
    }
}
Write-Host "OK - Removed $removedLocks lock file(s)" -ForegroundColor Green
Write-Host ""

# Step 4: Check meta.properties for corruption
Write-Host "Step 4: Checking meta.properties..." -ForegroundColor Yellow
$metaFile = Join-Path $KAFKA_LOG_DIR "meta.properties"
if (Test-Path $metaFile) {
    try {
        $metaContent = Get-Content $metaFile -Raw -ErrorAction Stop
        if ($metaContent -match "broker\.id=(\d+)") {
            Write-Host "  OK - meta.properties is valid (broker.id=$($Matches[1]))" -ForegroundColor Green
        } else {
            Write-Host "  WARNING - meta.properties may be corrupted" -ForegroundColor Yellow
            Write-Host "  Attempting to fix..." -ForegroundColor Cyan
            "version=0`nbroker.id=0" | Out-File -FilePath $metaFile -NoNewline -Encoding ASCII -ErrorAction Stop
            Write-Host "  OK - Recreated meta.properties" -ForegroundColor Green
        }
    } catch {
        Write-Host "  WARNING - Could not read meta.properties: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Creating meta.properties..." -ForegroundColor Cyan
    "version=0`nbroker.id=0" | Out-File -FilePath $metaFile -NoNewline -Encoding ASCII -ErrorAction Stop
    Write-Host "  OK - Created meta.properties" -ForegroundColor Green
}
Write-Host ""

# Step 5: Try to repair the specific partition by removing corrupted segments
Write-Host "Step 5: Checking for corrupted segments in __consumer_offsets-42..." -ForegroundColor Yellow
if (Test-Path $problemPartition) {
    # Get all .log files and check if they have matching .index files
    $logFiles = Get-ChildItem -Path $problemPartition -Filter "*.log" -ErrorAction SilentlyContinue
    $orphanedLogs = 0
    foreach ($logFile in $logFiles) {
        $indexFile = Join-Path $problemPartition "$($logFile.BaseName).index"
        if (-not (Test-Path $indexFile)) {
            Write-Host "  WARNING - Found orphaned log file: $($logFile.Name)" -ForegroundColor Yellow
            Write-Host "    This may cause issues. Consider removing it if Kafka still fails." -ForegroundColor Gray
            $orphanedLogs++
        }
    }
    if ($orphanedLogs -eq 0) {
        Write-Host "  OK - All log files have matching index files" -ForegroundColor Green
    }
}
Write-Host ""

# Step 6: Nuclear option - if still having issues, suggest recreating the partition
Write-Host "Step 6: Summary and recommendations..." -ForegroundColor Yellow
Write-Host ""
Write-Host "If Kafka still fails with 'log dir already offline' error:" -ForegroundColor Cyan
Write-Host "  Option 1: Delete and recreate the problematic partition directory" -ForegroundColor White
Write-Host "    Remove-Item -Path '$problemPartition' -Recurse -Force" -ForegroundColor Gray
Write-Host "    (Kafka will recreate it automatically, but offsets will be lost)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Option 2: If multiple partitions are corrupted, you may need to:" -ForegroundColor White
Write-Host "    - Backup the directory: Copy-Item '$KAFKA_LOG_DIR' -Destination 'C:\tmp\kafka-logs-backup' -Recurse" -ForegroundColor Gray
Write-Host "    - Delete and recreate the log directory" -ForegroundColor Gray
Write-Host "    - (This will lose ALL topics and data - use only as last resort)" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start ZooKeeper" -ForegroundColor White
Write-Host "2. Start Kafka" -ForegroundColor White
Write-Host "3. If Kafka still fails, try removing __consumer_offsets-42 partition" -ForegroundColor White
Write-Host ""


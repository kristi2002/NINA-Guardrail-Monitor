# PowerShell script to reset Kafka's failed log directory state
# This clears Kafka's internal state about failed directories

$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Resetting Kafka Log Directory State" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will clear Kafka's memory of failed directories." -ForegroundColor Yellow
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

# Step 2: Remove lock files
Write-Host "Step 2: Removing lock files..." -ForegroundColor Yellow
$lockFiles = Get-ChildItem -Path $KAFKA_LOG_DIR -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue
foreach ($lockFile in $lockFiles) {
    Remove-Item -Path $lockFile.FullName -Force -ErrorAction SilentlyContinue
}
Write-Host "OK - Lock files removed" -ForegroundColor Green
Write-Host ""

# Step 3: Delete and recreate meta.properties to reset state
Write-Host "Step 3: Resetting meta.properties..." -ForegroundColor Yellow
$metaFile = Join-Path $KAFKA_LOG_DIR "meta.properties"
if (Test-Path $metaFile) {
    Write-Host "  Backing up existing meta.properties..." -ForegroundColor Cyan
    $backupFile = "$metaFile.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -Path $metaFile -Destination $backupFile -ErrorAction SilentlyContinue
    
    Write-Host "  Reading broker.id from existing file..." -ForegroundColor Cyan
    $metaContent = Get-Content $metaFile -Raw -ErrorAction SilentlyContinue
    $brokerId = "0"
    if ($metaContent -match "broker\.id=(\d+)") {
        $brokerId = $Matches[1]
        Write-Host "  Found broker.id=$brokerId" -ForegroundColor Gray
    }
    
    Write-Host "  Recreating meta.properties with fresh state..." -ForegroundColor Cyan
    "version=0`nbroker.id=$brokerId" | Out-File -FilePath $metaFile -NoNewline -Encoding ASCII -ErrorAction Stop
    Write-Host "  OK - meta.properties recreated" -ForegroundColor Green
} else {
    Write-Host "  Creating new meta.properties..." -ForegroundColor Cyan
    "version=0`nbroker.id=0" | Out-File -FilePath $metaFile -NoNewline -Encoding ASCII -ErrorAction Stop
    Write-Host "  OK - meta.properties created" -ForegroundColor Green
}
Write-Host ""

# Step 4: Remove any recreated problematic partitions
Write-Host "Step 4: Cleaning up problematic partitions..." -ForegroundColor Yellow
$problemPartitions = @("__consumer_offsets-42", "guardrail.control-0")
foreach ($partition in $problemPartitions) {
    $partitionPath = Join-Path $KAFKA_LOG_DIR $partition
    if (Test-Path $partitionPath) {
        Write-Host "  Removing $partition..." -ForegroundColor Cyan
        try {
            Get-ChildItem -Path $partitionPath -Recurse -Force -ErrorAction SilentlyContinue | 
                ForEach-Object { $_.IsReadOnly = $false }
            Remove-Item -Path $partitionPath -Recurse -Force -ErrorAction Stop
            Write-Host "  OK - Removed $partition" -ForegroundColor Green
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Host "  WARNING - Could not remove $partition : $errorMsg" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# Step 5: Verify directory is clean
Write-Host "Step 5: Verifying directory state..." -ForegroundColor Yellow
$hasLockFiles = (Get-ChildItem -Path $KAFKA_LOG_DIR -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue).Count -gt 0
if ($hasLockFiles) {
    Write-Host "  WARNING - Lock files still present" -ForegroundColor Yellow
} else {
    Write-Host "  OK - No lock files" -ForegroundColor Green
}

$metaExists = Test-Path $metaFile
if ($metaExists) {
    Write-Host "  OK - meta.properties exists" -ForegroundColor Green
} else {
    Write-Host "  ERROR - meta.properties missing" -ForegroundColor Red
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Reset Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Kafka's log directory state has been reset." -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start ZooKeeper" -ForegroundColor White
Write-Host "2. Start Kafka" -ForegroundColor White
Write-Host "3. If Kafka still fails, you may need to:" -ForegroundColor White
Write-Host "   - Clear ZooKeeper metadata (more aggressive)" -ForegroundColor Gray
Write-Host "   - Or recreate the log directory entirely" -ForegroundColor Gray
Write-Host ""


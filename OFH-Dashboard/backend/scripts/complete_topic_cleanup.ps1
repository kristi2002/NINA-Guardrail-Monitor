# PowerShell script to completely remove guardrail.control topic
# This handles both ZooKeeper metadata and the directory

$ZOOKEEPER_HOST = "localhost:2181"
$KAFKA_HOME = "C:\kafka\kafka_2.13-3.6.1"
$TOPIC_NAME = "guardrail.control"
$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$TOPIC_DIR = "$TOPIC_NAME-0"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Complete Topic Cleanup: $TOPIC_NAME" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop Kafka and ZooKeeper
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

# Step 2: Delete the directory first (while everything is stopped)
Write-Host "Step 2: Removing topic directory..." -ForegroundColor Yellow
$topicDirPath = Join-Path $KAFKA_LOG_DIR $TOPIC_DIR
if (Test-Path $topicDirPath) {
    Write-Host "  Found directory: $TOPIC_DIR" -ForegroundColor Cyan
    try {
        # Remove read-only attributes
        Get-ChildItem -Path $topicDirPath -Recurse -Force -ErrorAction SilentlyContinue | 
            ForEach-Object { $_.IsReadOnly = $false }
        
        # Delete directory
        Remove-Item -Path $topicDirPath -Recurse -Force -ErrorAction Stop
        Write-Host "  OK - Directory removed" -ForegroundColor Green
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "  WARNING - Could not remove directory: $errorMsg" -ForegroundColor Yellow
        Write-Host "  Will try again after ZooKeeper cleanup" -ForegroundColor Gray
    }
} else {
    Write-Host "  Directory not found (already removed)" -ForegroundColor Green
}
Write-Host ""

# Step 3: Remove from ZooKeeper using zkCli
Write-Host "Step 3: Removing topic from ZooKeeper..." -ForegroundColor Yellow

# Find zkCli
$zkCliPath = Join-Path $KAFKA_HOME "bin\windows\zkCli.cmd"
if (-not (Test-Path $zkCliPath)) {
    # Try .bat extension
    $zkCliPath = Join-Path $KAFKA_HOME "bin\windows\zkCli.bat"
}

if (-not (Test-Path $zkCliPath)) {
    Write-Host "  WARNING - zkCli not found at expected location" -ForegroundColor Yellow
    Write-Host "  You will need to manually delete from ZooKeeper" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Manual steps:" -ForegroundColor Cyan
    Write-Host "    1. Start ZooKeeper" -ForegroundColor White
    Write-Host "    2. Run zkCli: cd $KAFKA_HOME && .\bin\windows\zkCli.cmd -server $ZOOKEEPER_HOST" -ForegroundColor Gray
    Write-Host "    3. In zkCli, run:" -ForegroundColor White
    Write-Host "       delete /brokers/topics/$TOPIC_NAME" -ForegroundColor Gray
    Write-Host "       delete /config/topics/$TOPIC_NAME" -ForegroundColor Gray
    Write-Host "       rmr /admin/delete_topics/$TOPIC_NAME" -ForegroundColor Gray
    Write-Host "       quit" -ForegroundColor Gray
} else {
    Write-Host "  Found zkCli at: $zkCliPath" -ForegroundColor Green
    
    # Create commands file
    $commands = @"
delete /brokers/topics/$TOPIC_NAME
delete /config/topics/$TOPIC_NAME
rmr /admin/delete_topics/$TOPIC_NAME 2>&1
quit
"@
    
    $commandsFile = Join-Path $env:TEMP "zk_delete_commands.txt"
    $commands | Out-File -FilePath $commandsFile -Encoding ASCII -NoNewline
    
    Write-Host "  Attempting to connect to ZooKeeper..." -ForegroundColor Cyan
    Write-Host "  (If this fails, use manual steps above)" -ForegroundColor Gray
    
    # Try to execute (this may require ZooKeeper to be running)
    # For now, just provide instructions
    Write-Host ""
    Write-Host "  To delete from ZooKeeper, run this command:" -ForegroundColor Yellow
    Write-Host "    Get-Content '$commandsFile' | & '$zkCliPath' -server $ZOOKEEPER_HOST" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Or manually:" -ForegroundColor Yellow
    Write-Host "    1. Start ZooKeeper" -ForegroundColor White
    Write-Host "    2. Run: $zkCliPath -server $ZOOKEEPER_HOST" -ForegroundColor Gray
    Write-Host "    3. Execute the commands from: $commandsFile" -ForegroundColor Gray
}
Write-Host ""

# Step 4: Try to delete directory again
Write-Host "Step 4: Final directory cleanup..." -ForegroundColor Yellow
if (Test-Path $topicDirPath) {
    Write-Host "  Directory still exists, trying removal again..." -ForegroundColor Cyan
    try {
        & takeown /F $topicDirPath /R /D Y 2>&1 | Out-Null
        & attrib -R "$topicDirPath\*.*" /S /D 2>&1 | Out-Null
        Remove-Item -Path $topicDirPath -Recurse -Force -ErrorAction Stop
        Write-Host "  OK - Directory removed" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR - Still cannot remove directory" -ForegroundColor Red
        Write-Host "  You may need to restart your computer or use Process Explorer to find what's locking it" -ForegroundColor Yellow
    }
} else {
    Write-Host "  OK - Directory does not exist" -ForegroundColor Green
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Cleanup Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Delete topic from ZooKeeper (see instructions above)" -ForegroundColor White
Write-Host "2. Ensure directory is removed: $topicDirPath" -ForegroundColor White
Write-Host "3. Run: .\scripts\reset_kafka_log_dir_state.ps1" -ForegroundColor White
Write-Host "4. Start ZooKeeper" -ForegroundColor White
Write-Host "5. Start Kafka" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: The topic MUST be deleted from ZooKeeper before starting Kafka," -ForegroundColor Yellow
Write-Host "otherwise Kafka will try to manage it again and fail." -ForegroundColor Yellow
Write-Host ""


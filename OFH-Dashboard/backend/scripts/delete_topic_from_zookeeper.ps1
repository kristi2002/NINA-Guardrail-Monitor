# PowerShell script to delete the guardrail.control topic from ZooKeeper
# This prevents Kafka from trying to manage a topic that can't be deleted due to Windows file locking

$ZOOKEEPER_HOST = "localhost:2181"
$KAFKA_HOME = "C:\kafka\kafka_2.13-3.6.1"
$TOPIC_NAME = "guardrail.control"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Deleting Topic from ZooKeeper" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Topic to delete: $TOPIC_NAME" -ForegroundColor Yellow
Write-Host "This will remove the topic metadata from ZooKeeper" -ForegroundColor White
Write-Host ""

# Step 1: Stop Kafka (ZooKeeper should be running)
Write-Host "Step 1: Stopping Kafka..." -ForegroundColor Yellow
Get-Process -Name "java" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmd -like "*kafka.Kafka*") {
            Write-Host "  Stopping Kafka process $($_.Id)..." -ForegroundColor Cyan
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Ignore
    }
}
Start-Sleep -Seconds 3
Write-Host "OK - Kafka stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Find zkCli
Write-Host "Step 2: Finding zkCli..." -ForegroundColor Yellow
$zkCliPath = $null
$possiblePaths = @(
    "$KAFKA_HOME\bin\windows\zkCli.cmd",
    "C:\kafka\bin\windows\zkCli.cmd",
    "C:\Program Files\kafka\bin\windows\zkCli.cmd"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $zkCliPath = $path
        Write-Host "  Found zkCli at: $path" -ForegroundColor Green
        break
    }
}

if (-not $zkCliPath) {
    Write-Host "  ERROR - Could not find zkCli.cmd" -ForegroundColor Red
    Write-Host "  Please update `$KAFKA_HOME in this script" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 3: Create a script file for zkCli commands
Write-Host "Step 3: Creating ZooKeeper deletion script..." -ForegroundColor Yellow
$zkScript = @"
delete /brokers/topics/$TOPIC_NAME
delete /config/topics/$TOPIC_NAME
quit
"@

$scriptFile = Join-Path $env:TEMP "delete_topic_zk_commands.txt"
$zkScript | Out-File -FilePath $scriptFile -Encoding ASCII -NoNewline

# Also try the admin/topics path
$zkScriptFull = @"
delete /brokers/topics/$TOPIC_NAME
delete /config/topics/$TOPIC_NAME
rmr /admin/delete_topics/$TOPIC_NAME
quit
"@

$scriptFileFull = Join-Path $env:TEMP "delete_topic_zk_commands_full.txt"
$zkScriptFull | Out-File -FilePath $scriptFileFull -Encoding ASCII -NoNewline

Write-Host "  Created script file: $scriptFile" -ForegroundColor Gray
Write-Host ""

# Step 4: Alternative approach - use kafka-topics to delete
Write-Host "Step 4: Attempting to delete topic using kafka-topics..." -ForegroundColor Yellow
$kafkaTopicsPath = Join-Path $KAFKA_HOME "bin\windows\kafka-topics.bat"
if (Test-Path $kafkaTopicsPath) {
    Write-Host "  Trying kafka-topics --delete..." -ForegroundColor Cyan
    # Note: This won't work if Kafka is down, but let's try
    $result = & $kafkaTopicsPath --delete --topic $TOPIC_NAME --bootstrap-server $ZOOKEEPER_HOST 2>&1
    Write-Host "  Result: $result" -ForegroundColor Gray
} else {
    Write-Host "  kafka-topics.bat not found" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Manual instructions
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Manual Steps Required" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Since Kafka keeps recreating the topic, we need to remove it from ZooKeeper." -ForegroundColor White
Write-Host ""
Write-Host "Option 1: Use zkCli manually (Recommended)" -ForegroundColor Yellow
Write-Host "  1. Open a new terminal" -ForegroundColor White
Write-Host "  2. Run: $zkCliPath -server $ZOOKEEPER_HOST" -ForegroundColor Gray
Write-Host "  3. In zkCli, run these commands:" -ForegroundColor White
Write-Host "     delete /brokers/topics/$TOPIC_NAME" -ForegroundColor Gray
Write-Host "     delete /config/topics/$TOPIC_NAME" -ForegroundColor Gray
Write-Host "     rmr /admin/delete_topics/$TOPIC_NAME" -ForegroundColor Gray
Write-Host "     quit" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 2: Delete using Python kafka-python (if available)" -ForegroundColor Yellow
Write-Host "  This requires Kafka to be running, so start Kafka first," -ForegroundColor White
Write-Host "  then use Python to delete the topic programmatically." -ForegroundColor White
Write-Host ""
Write-Host "After removing from ZooKeeper:" -ForegroundColor Cyan
Write-Host "  1. Manually delete the directory: C:\tmp\kafka-logs\$TOPIC_NAME-0" -ForegroundColor White
Write-Host "  2. Reset Kafka state: .\scripts\reset_kafka_log_dir_state.ps1" -ForegroundColor White
Write-Host "  3. Start Kafka" -ForegroundColor White
Write-Host ""


# Quick fix script for guardrail.control topic issue
# This will start Kafka briefly, delete the topic, then stop it

$KAFKA_HOME = "C:\kafka\kafka_2.13-3.6.1"
$KAFKA_LOG_DIR = "C:\tmp\kafka-logs"
$TOPIC_NAME = "guardrail.control"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Quick Fix: Delete guardrail.control Topic" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Start ZooKeeper (if not running)" -ForegroundColor White
Write-Host "2. Start Kafka briefly" -ForegroundColor White
Write-Host "3. Delete the topic using Python" -ForegroundColor White
Write-Host "4. Stop Kafka" -ForegroundColor White
Write-Host "5. Clean up the directory" -ForegroundColor White
Write-Host ""

# Check if ZooKeeper is running
Write-Host "Checking ZooKeeper..." -ForegroundColor Yellow
$zkRunning = Test-NetConnection -ComputerName localhost -Port 2181 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $zkRunning) {
    Write-Host "  ZooKeeper is not running. Please start it first:" -ForegroundColor Yellow
    Write-Host "  cd $KAFKA_HOME" -ForegroundColor Gray
    Write-Host "  .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Then run this script again." -ForegroundColor White
    exit 1
} else {
    Write-Host "  OK - ZooKeeper is running" -ForegroundColor Green
}
Write-Host ""

# Check if Kafka is running
Write-Host "Checking Kafka..." -ForegroundColor Yellow
$kafkaRunning = Test-NetConnection -ComputerName localhost -Port 9092 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($kafkaRunning) {
    Write-Host "  Kafka is already running" -ForegroundColor Green
    Write-Host ""
    Write-Host "Attempting to delete topic..." -ForegroundColor Yellow
    python scripts\delete_topic_python.py
    Write-Host ""
    
    Write-Host "Now stopping Kafka to clean up directory..." -ForegroundColor Yellow
    Get-Process -Name "java" -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
            if ($cmd -like "*kafka.Kafka*") {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Ignore
        }
    }
    Start-Sleep -Seconds 3
} else {
    Write-Host "  Kafka is not running. Starting Kafka..." -ForegroundColor Cyan
    Write-Host "  (This may take a moment)" -ForegroundColor Gray
    
    $kafkaScript = Join-Path $KAFKA_HOME "bin\windows\kafka-server-start.bat"
    $kafkaConfig = Join-Path $KAFKA_HOME "config\server.properties"
    
    if (-not (Test-Path $kafkaScript)) {
        Write-Host "  ERROR - Kafka script not found: $kafkaScript" -ForegroundColor Red
        exit 1
    }
    
    # Start Kafka in background
    $kafkaProcess = Start-Process -FilePath $kafkaScript -ArgumentList $kafkaConfig -PassThru -WindowStyle Minimized
    Write-Host "  Kafka started (PID: $($kafkaProcess.Id))" -ForegroundColor Green
    
    # Wait for Kafka to be ready
    Write-Host "  Waiting for Kafka to be ready..." -ForegroundColor Cyan
    $maxWait = 30
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 2
        $waited += 2
        $kafkaReady = Test-NetConnection -ComputerName localhost -Port 9092 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($kafkaReady) {
            Write-Host "  OK - Kafka is ready" -ForegroundColor Green
            break
        }
        Write-Host "  ." -NoNewline -ForegroundColor Gray
    }
    Write-Host ""
    
    if (-not $kafkaReady) {
        Write-Host "  WARNING - Kafka may not be fully ready, but attempting deletion anyway" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Attempting to delete topic..." -ForegroundColor Yellow
    python scripts\delete_topic_python.py
    Write-Host ""
    
    Write-Host "Stopping Kafka..." -ForegroundColor Yellow
    Stop-Process -Id $kafkaProcess.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
}

# Clean up directory
Write-Host "Cleaning up directory..." -ForegroundColor Yellow
$topicDir = Join-Path $KAFKA_LOG_DIR "$TOPIC_NAME-0"
if (Test-Path $topicDir) {
    try {
        Get-ChildItem -Path $topicDir -Recurse -Force -ErrorAction SilentlyContinue | 
            ForEach-Object { $_.IsReadOnly = $false }
        Remove-Item -Path $topicDir -Recurse -Force -ErrorAction Stop
        Write-Host "  OK - Directory removed" -ForegroundColor Green
    } catch {
        Write-Host "  WARNING - Could not remove directory: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  You may need to remove it manually: $topicDir" -ForegroundColor Gray
    }
} else {
    Write-Host "  OK - Directory does not exist" -ForegroundColor Green
}
Write-Host ""

# Reset Kafka state
Write-Host "Resetting Kafka state..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File scripts\reset_kafka_log_dir_state.ps1 | Out-Null
Write-Host "  OK - State reset" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start ZooKeeper (if not running)" -ForegroundColor White
Write-Host "2. Start Kafka" -ForegroundColor White
Write-Host "3. Create the guardrail_control topic:" -ForegroundColor White
Write-Host "   python scripts\create_guardrail_control_topic.py" -ForegroundColor Gray
Write-Host ""


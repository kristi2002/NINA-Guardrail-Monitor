# PowerShell script to fix ZooKeeper stale node and restart Kafka
# This handles the common error: "node already exists and owner does not match current session"

$ZOOKEEPER_HOST = "localhost:2181"
$KAFKA_HOME = "C:\kafka\kafka_2.13-3.6.1"  # Adjust this path if needed

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Fixing ZooKeeper Stale Node and Restarting Kafka" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop Kafka if running
Write-Host "Step 1: Stopping Kafka..." -ForegroundColor Yellow
$kafkaProcess = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*kafka.Kafka*" }
if ($kafkaProcess) {
    Write-Host "Found Kafka process (PID: $($kafkaProcess.Id))" -ForegroundColor Cyan
    Stop-Process -Id $kafkaProcess.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "OK - Kafka stopped" -ForegroundColor Green
} else {
    Write-Host "OK - Kafka is not running" -ForegroundColor Green
}
Write-Host ""

# Step 2: Stop ZooKeeper if running
Write-Host "Step 2: Stopping ZooKeeper..." -ForegroundColor Yellow
$zkProcess = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*QuorumPeerMain*" -or $_.CommandLine -like "*zookeeper*" }
if ($zkProcess) {
    Write-Host "Found ZooKeeper process (PID: $($zkProcess.Id))" -ForegroundColor Cyan
    Stop-Process -Id $zkProcess.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "OK - ZooKeeper stopped" -ForegroundColor Green
} else {
    Write-Host "OK - ZooKeeper is not running" -ForegroundColor Green
}
Write-Host ""

# Step 3: Wait a bit for cleanup
Write-Host "Step 3: Waiting for processes to fully terminate..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "OK - Ready to restart" -ForegroundColor Green
Write-Host ""

# Step 4: Find ZooKeeper and Kafka scripts
Write-Host "Step 4: Locating Kafka installation..." -ForegroundColor Yellow
$zkScript = $null
$kafkaScript = $null

$possiblePaths = @(
    "C:\kafka\kafka_2.13-3.6.1",
    "C:\kafka",
    "C:\Program Files\kafka"
)

foreach ($basePath in $possiblePaths) {
    $zkPath = Join-Path $basePath "bin\windows\zookeeper-server-start.bat"
    $kafkaPath = Join-Path $basePath "bin\windows\kafka-server-start.bat"
    
    if (Test-Path $zkPath) {
        $zkScript = $zkPath
        $KAFKA_HOME = $basePath
    }
    if (Test-Path $kafkaPath) {
        $kafkaScript = $kafkaPath
        $KAFKA_HOME = $basePath
    }
}

if (-not $zkScript -or -not $kafkaScript) {
    Write-Host "ERROR - Could not find Kafka installation" -ForegroundColor Red
    Write-Host "Please update `$KAFKA_HOME in this script to point to your Kafka installation" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual steps:" -ForegroundColor Cyan
    Write-Host "1. Start ZooKeeper:" -ForegroundColor White
    Write-Host "   cd $KAFKA_HOME" -ForegroundColor Gray
    Write-Host "   .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. In a new terminal, start Kafka:" -ForegroundColor White
    Write-Host "   cd $KAFKA_HOME" -ForegroundColor Gray
    Write-Host "   .\bin\windows\kafka-server-start.bat .\config\server.properties" -ForegroundColor Gray
    exit 1
}

Write-Host "OK - Found Kafka at: $KAFKA_HOME" -ForegroundColor Green
Write-Host ""

# Step 5: Start ZooKeeper
Write-Host "Step 5: Starting ZooKeeper..." -ForegroundColor Yellow
$zkConfig = Join-Path $KAFKA_HOME "config\zookeeper.properties"
if (-not (Test-Path $zkConfig)) {
    Write-Host "ERROR - ZooKeeper config not found: $zkConfig" -ForegroundColor Red
    exit 1
}

Write-Host "Starting ZooKeeper in background..." -ForegroundColor Cyan
$zkJob = Start-Process -FilePath $zkScript -ArgumentList $zkConfig -PassThru -WindowStyle Minimized
Start-Sleep -Seconds 5

# Check if ZooKeeper started
$zkRunning = Get-Process -Id $zkJob.Id -ErrorAction SilentlyContinue
if ($zkRunning) {
    Write-Host "OK - ZooKeeper started (PID: $($zkJob.Id))" -ForegroundColor Green
    Write-Host "Waiting for ZooKeeper to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
} else {
    Write-Host "WARNING - ZooKeeper may have failed to start" -ForegroundColor Yellow
    Write-Host "Check the ZooKeeper logs for errors" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Start Kafka
Write-Host "Step 6: Starting Kafka..." -ForegroundColor Yellow
$kafkaConfig = Join-Path $KAFKA_HOME "config\server.properties"
if (-not (Test-Path $kafkaConfig)) {
    Write-Host "ERROR - Kafka config not found: $kafkaConfig" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Kafka in background..." -ForegroundColor Cyan
$kafkaJob = Start-Process -FilePath $kafkaScript -ArgumentList $kafkaConfig -PassThru -WindowStyle Minimized
Start-Sleep -Seconds 5

# Check if Kafka started
$kafkaRunning = Get-Process -Id $kafkaJob.Id -ErrorAction SilentlyContinue
if ($kafkaRunning) {
    Write-Host "OK - Kafka started (PID: $($kafkaJob.Id))" -ForegroundColor Green
    Write-Host "Waiting for Kafka to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
} else {
    Write-Host "WARNING - Kafka may have failed to start" -ForegroundColor Yellow
    Write-Host "Check the Kafka logs for errors" -ForegroundColor Yellow
}
Write-Host ""

# Step 7: Verify
Write-Host "Step 7: Verifying services..." -ForegroundColor Yellow
$zkFinal = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*QuorumPeerMain*" }
$kafkaFinal = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*kafka.Kafka*" }

if ($zkFinal -and $kafkaFinal) {
    Write-Host "OK - Both ZooKeeper and Kafka are running" -ForegroundColor Green
    Write-Host "ZooKeeper PID: $($zkFinal.Id)" -ForegroundColor Gray
    Write-Host "Kafka PID: $($kafkaFinal.Id)" -ForegroundColor Gray
} else {
    Write-Host "WARNING - One or both services may not be running properly" -ForegroundColor Yellow
    if (-not $zkFinal) {
        Write-Host "  - ZooKeeper is not running" -ForegroundColor Red
    }
    if (-not $kafkaFinal) {
        Write-Host "  - Kafka is not running" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Restart Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step: Create the guardrail_control topic" -ForegroundColor Yellow
Write-Host "  python scripts\create_guardrail_control_topic.py" -ForegroundColor White
Write-Host ""


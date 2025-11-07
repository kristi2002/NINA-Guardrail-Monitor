# PowerShell script to fix ZooKeeper stale node issue
# This happens when Kafka didn't shut down cleanly and left an ephemeral node

$ZOOKEEPER_HOST = "localhost:2181"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Fixing ZooKeeper Stale Node Issue" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if ZooKeeper is running
Write-Host "Step 1: Checking ZooKeeper status..." -ForegroundColor Yellow
$zkProcess = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*zookeeper*" -or $_.CommandLine -like "*QuorumPeerMain*" }
if (-not $zkProcess) {
    Write-Host "WARNING - ZooKeeper doesn't appear to be running" -ForegroundColor Yellow
    Write-Host "You may need to start ZooKeeper first" -ForegroundColor Yellow
} else {
    Write-Host "OK - ZooKeeper process found (PID: $($zkProcess.Id))" -ForegroundColor Green
}
Write-Host ""

# Check if Kafka is running
Write-Host "Step 2: Checking Kafka status..." -ForegroundColor Yellow
$kafkaProcess = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*kafka.Kafka*" }
if ($kafkaProcess) {
    Write-Host "WARNING - Kafka is still running (PID: $($kafkaProcess.Id))" -ForegroundColor Yellow
    Write-Host "Please stop Kafka first before fixing ZooKeeper nodes" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To stop Kafka, find the process and kill it:" -ForegroundColor White
    Write-Host "  Stop-Process -Id $($kafkaProcess.Id) -Force" -ForegroundColor Gray
    exit 1
} else {
    Write-Host "OK - Kafka is not running" -ForegroundColor Green
}
Write-Host ""

# Instructions for manual cleanup
Write-Host "Step 3: ZooKeeper Node Cleanup Options" -ForegroundColor Yellow
Write-Host ""
Write-Host "The error indicates a stale ephemeral node at /brokers/ids/0" -ForegroundColor White
Write-Host ""
Write-Host "Option 1: Restart ZooKeeper (Recommended - Clears all stale nodes)" -ForegroundColor Cyan
Write-Host "  1. Stop ZooKeeper" -ForegroundColor White
Write-Host "  2. Start ZooKeeper" -ForegroundColor White
Write-Host "  3. Start Kafka" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Delete the stale node manually using zkCli" -ForegroundColor Cyan
Write-Host "  1. Open a new terminal" -ForegroundColor White
Write-Host "  2. Run: zkCli.cmd -server $ZOOKEEPER_HOST" -ForegroundColor Gray
Write-Host "  3. In zkCli, run: delete /brokers/ids/0" -ForegroundColor Gray
Write-Host "  4. Exit zkCli: quit" -ForegroundColor Gray
Write-Host "  5. Start Kafka" -ForegroundColor White
Write-Host ""

# Try to find zkCli path
Write-Host "Step 4: Looking for zkCli tool..." -ForegroundColor Yellow
$possibleZkPaths = @(
    "C:\kafka\kafka_2.13-3.6.1\bin\windows\zkCli.cmd",
    "C:\kafka\bin\windows\zkCli.cmd",
    "C:\Program Files\kafka\bin\windows\zkCli.cmd"
)

$zkCliPath = $null
foreach ($path in $possibleZkPaths) {
    if (Test-Path $path) {
        $zkCliPath = $path
        Write-Host "OK - Found zkCli at: $path" -ForegroundColor Green
        break
    }
}

if (-not $zkCliPath) {
    Write-Host "WARNING - Could not find zkCli.cmd automatically" -ForegroundColor Yellow
    Write-Host "You'll need to locate it manually in your Kafka installation" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Quick fix command (run in a new terminal):" -ForegroundColor Cyan
    Write-Host "  $zkCliPath -server $ZOOKEEPER_HOST" -ForegroundColor Gray
    Write-Host "  Then in zkCli: delete /brokers/ids/0" -ForegroundColor Gray
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "The easiest solution is to restart ZooKeeper:" -ForegroundColor White
Write-Host "  1. Stop ZooKeeper" -ForegroundColor Gray
Write-Host "  2. Start ZooKeeper" -ForegroundColor Gray
Write-Host "  3. Start Kafka" -ForegroundColor Gray
Write-Host ""
Write-Host "This will clear all stale ephemeral nodes automatically." -ForegroundColor White
Write-Host ""


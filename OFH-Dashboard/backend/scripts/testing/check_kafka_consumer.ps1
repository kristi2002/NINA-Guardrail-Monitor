# Quick diagnostic script to check if Kafka consumer is running

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kafka Consumer Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if OFH Dashboard is running
Write-Host "1. Checking if OFH Dashboard API is running..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   ✅ OFH Dashboard is running" -ForegroundColor Green
    Write-Host "   Status: $($healthResponse.status)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ OFH Dashboard is NOT running (port 5000)" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please start OFH Dashboard first:" -ForegroundColor Yellow
    Write-Host "   cd OFH-Dashboard\backend" -ForegroundColor White
    Write-Host "   python app.py" -ForegroundColor White
    exit
}

Write-Host ""
Write-Host "2. Checking Kafka connectivity..." -ForegroundColor Yellow
$kafkaHost = "localhost"
$kafkaPort = 9092

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($kafkaHost, $kafkaPort, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(2000, $false)
    
    if ($wait) {
        $tcpClient.EndConnect($connect)
        Write-Host "   ✅ Kafka broker is reachable at ${kafkaHost}:${kafkaPort}" -ForegroundColor Green
        $tcpClient.Close()
    } else {
        Write-Host "   ❌ Kafka broker is NOT reachable at ${kafkaHost}:${kafkaPort}" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Cannot connect to Kafka: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. Checking Guardrail-Strategy service..." -ForegroundColor Yellow
try {
    $guardrailHealth = Invoke-RestMethod -Uri "http://localhost:5001/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   ✅ Guardrail-Strategy is running" -ForegroundColor Green
    Write-Host "   Kafka Status: $($guardrailHealth.kafka)" -ForegroundColor Cyan
} catch {
    Write-Host "   ⚠️ Guardrail-Strategy is NOT running (port 5001)" -ForegroundColor Yellow
    Write-Host "   (This is OK if you're only testing the consumer)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If OFH Dashboard is running, you should see in its terminal:" -ForegroundColor Yellow
Write-Host "  - '✅ Enhanced Kafka Consumer listening for events...'" -ForegroundColor White
Write-Host "  - '🔄 Kafka consumer polling (poll #X)...' (every 10 seconds)" -ForegroundColor White
Write-Host "  - '📨 Received X message batch(es) from Kafka' (when messages arrive)" -ForegroundColor White
Write-Host ""
Write-Host "If you don't see these logs:" -ForegroundColor Yellow
Write-Host "  1. Check OFH Dashboard terminal for connection errors" -ForegroundColor White
Write-Host "  2. Verify Kafka is running: docker ps (if using Docker)" -ForegroundColor White
Write-Host "  3. Check .env file has correct KAFKA_BOOTSTRAP_SERVERS" -ForegroundColor White
Write-Host "  4. Restart OFH Dashboard to ensure consumer starts" -ForegroundColor White
Write-Host ""


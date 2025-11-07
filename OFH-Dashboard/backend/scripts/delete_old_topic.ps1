# PowerShell script to delete the old guardrail.control topic
# This resolves the conflict with guardrail_control

$KAFKA_HOME = $env:KAFKA_HOME
$BOOTSTRAP_SERVER = "localhost:9092"
$OLD_TOPIC = "guardrail.control"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🗑️  Deleting Old Kafka Topic: guardrail.control" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Try to find kafka-topics script
$kafkaTopicsScript = $null

# Check common locations
$possiblePaths = @(
    "$KAFKA_HOME\bin\windows\kafka-topics.bat",
    "$KAFKA_HOME\bin\kafka-topics.sh",
    "kafka-topics.bat",
    "kafka-topics"
)

foreach ($path in $possiblePaths) {
    if (Get-Command $path -ErrorAction SilentlyContinue) {
        $kafkaTopicsScript = $path
        break
    }
}

if (-not $kafkaTopicsScript) {
    Write-Host "❌ Could not find kafka-topics script" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this command manually:" -ForegroundColor Yellow
    Write-Host "  kafka-topics --delete --topic guardrail.control --bootstrap-server localhost:9092" -ForegroundColor White
    Write-Host ""
    Write-Host "Or if using Kafka in Docker:" -ForegroundColor Yellow
    Write-Host "  docker exec -it <kafka-container> kafka-topics --delete --topic guardrail.control --bootstrap-server localhost:9092" -ForegroundColor White
    exit 1
}

Write-Host "Found kafka-topics at: $kafkaTopicsScript" -ForegroundColor Green
Write-Host "Deleting topic: $OLD_TOPIC" -ForegroundColor Yellow
Write-Host ""

try {
    if ($kafkaTopicsScript -like "*.bat" -or $kafkaTopicsScript -like "*.sh") {
        & $kafkaTopicsScript --delete --topic $OLD_TOPIC --bootstrap-server $BOOTSTRAP_SERVER
    } else {
        & $kafkaTopicsScript --delete --topic $OLD_TOPIC --bootstrap-server $BOOTSTRAP_SERVER
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Successfully deleted topic: $OLD_TOPIC" -ForegroundColor Green
        Write-Host ""
        Write-Host "Now you can run the Python script to create guardrail_control:" -ForegroundColor Cyan
        Write-Host "  python scripts\create_guardrail_control_topic.py" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "⚠️  Topic deletion may have failed or topic doesn't exist" -ForegroundColor Yellow
        Write-Host "   (This is OK if the topic was already deleted)" -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error deleting topic: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this command manually:" -ForegroundColor Yellow
    Write-Host "  kafka-topics --delete --topic guardrail.control --bootstrap-server localhost:9092" -ForegroundColor White
    exit 1
}


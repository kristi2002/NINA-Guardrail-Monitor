# Full Flow Test: Simulates AI -> Guardrail-Strategy -> Kafka -> OFH Dashboard -> Frontend
# This PowerShell script tests the complete message flow

$GUARDRAIL_STRATEGY_URL = "http://localhost:5001"
$OFH_DASHBOARD_URL = "http://localhost:5000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FULL FLOW TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This test simulates:" -ForegroundColor Yellow
Write-Host "1. AI sends message to Guardrail-Strategy" -ForegroundColor White
Write-Host "2. Guardrail-Strategy validates and sends to Kafka" -ForegroundColor White
Write-Host "3. OFH Dashboard consumes from Kafka" -ForegroundColor White
Write-Host "4. Frontend displays the conversation" -ForegroundColor White
Write-Host ""
Write-Host "Make sure both services are running:" -ForegroundColor Yellow
Write-Host "  - Guardrail-Strategy: $GUARDRAIL_STRATEGY_URL" -ForegroundColor White
Write-Host "  - OFH Dashboard: $OFH_DASHBOARD_URL" -ForegroundColor White
Write-Host ""

# Test scenarios
$testScenarios = @(
    @{
        Name = "Valid message (should pass)"
        Message = "Hello, I need help with my medication schedule"
        ConversationId = "test-flow-valid-$(Get-Date -Format 'yyyyMMddHHmmss')"
        UserId = "user-123"
    },
    @{
        Name = "Message with PII - email (should fail and send to Kafka)"
        Message = "Contact me at patient@example.com for follow-up"
        ConversationId = "test-flow-pii-$(Get-Date -Format 'yyyyMMddHHmmss')"
        UserId = "user-123"
    },
    @{
        Name = "Message with phone number (should fail)"
        Message = "Call me at 555-123-4567"
        ConversationId = "test-flow-phone-$(Get-Date -Format 'yyyyMMddHHmmss')"
        UserId = "user-123"
    },
    @{
        Name = "Normal conversation message"
        Message = "I'm feeling better today, thank you"
        ConversationId = "test-flow-normal-$(Get-Date -Format 'yyyyMMddHHmmss')"
        UserId = "user-123"
    }
)

$results = @()

foreach ($scenario in $testScenarios) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "TEST: $($scenario.Name)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Step 1: Send to Guardrail-Strategy
    Write-Host "Step 1: Sending message to Guardrail-Strategy..." -ForegroundColor Yellow
    Write-Host "  Message: $($scenario.Message)" -ForegroundColor Gray
    Write-Host "  Conversation ID: $($scenario.ConversationId)" -ForegroundColor Gray
    
    $body = @{
        message = $scenario.Message
        conversation_id = $scenario.ConversationId
        user_id = $scenario.UserId
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$GUARDRAIL_STRATEGY_URL/validate" `
            -Method Post `
            -Body $body `
            -ContentType "application/json" `
            -ErrorAction Stop
        
        $isValid = $response.valid
        $kafkaSent = $response.event.kafka_sent
        
        if ($isValid) {
            Write-Host "  ✅ Validation: PASS" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Validation: FAIL (Guardrail violation)" -ForegroundColor Yellow
        }
        
        Write-Host "  Kafka Event Sent: $kafkaSent" -ForegroundColor Cyan
        
        if ($kafkaSent) {
            Write-Host ""
            Write-Host "Step 2: Waiting for OFH Dashboard to consume from Kafka..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            Write-Host "  ✅ Check OFH Dashboard terminal for:" -ForegroundColor Green
            Write-Host "     - '📨 Received X message batch(es) from Kafka'" -ForegroundColor Gray
            Write-Host "     - '✅ Successfully processed guardrail event'" -ForegroundColor Gray
        } else {
            Write-Host "  ℹ️ No Kafka event (validation passed, no violation)" -ForegroundColor Gray
        }
        
        $results += @{
            Scenario = $scenario.Name
            Valid = $isValid
            KafkaSent = $kafkaSent
            ConversationId = $scenario.ConversationId
        }
        
    } catch {
        Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            Scenario = $scenario.Name
            Error = $_.Exception.Message
        }
    }
    
    Start-Sleep -Seconds 1
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $results) {
    if ($result.Error) {
        Write-Host "❌ $($result.Scenario)" -ForegroundColor Red
        Write-Host "   Error: $($result.Error)" -ForegroundColor Red
    } else {
        $icon = if ($result.KafkaSent) { "✅" } else { "ℹ️" }
        Write-Host "$icon $($result.Scenario)" -ForegroundColor $(if ($result.KafkaSent) { "Green" } else { "Gray" })
        Write-Host "   Validation: $(if ($result.Valid) { 'PASS' } else { 'FAIL' })" -ForegroundColor Cyan
        Write-Host "   Kafka Sent: $($result.KafkaSent)" -ForegroundColor Cyan
        Write-Host "   Conversation ID: $($result.ConversationId)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Check Guardrail-Strategy terminal for validation logs" -ForegroundColor Yellow
Write-Host "2. Check OFH Dashboard terminal for Kafka consumer logs:" -ForegroundColor Yellow
Write-Host "   - Look for '📨 Received X message batch(es) from Kafka'" -ForegroundColor White
Write-Host "   - Look for '✅ Successfully processed guardrail event'" -ForegroundColor White
Write-Host "3. Check Frontend - conversations should appear in dashboard" -ForegroundColor Yellow
Write-Host "4. If frontend shows 500 error, check backend terminal for error details" -ForegroundColor Yellow
Write-Host ""


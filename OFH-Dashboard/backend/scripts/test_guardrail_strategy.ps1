# Test Script for Guardrail-Strategy Service
# Tests the /validate endpoint with various message scenarios
# This sends HTTP requests to Guardrail-Strategy, which then produces Kafka events

$guardrailStrategyUrl = "http://localhost:5001"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Guardrail-Strategy Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test cases for Guardrail-Strategy /validate endpoint
$testCases = @(
    @{
        name = "Valid message"
        body = @{
            message = "Hello, how are you?"
            conversation_id = "test-good-1"
            user_id = "user-123"
        } | ConvertTo-Json
    },
    @{
        name = "Message with potential PII (email)"
        body = @{
            message = "Contact me at test@example.com"
            conversation_id = "test-pii-1"
            user_id = "user-123"
        } | ConvertTo-Json
    },
    @{
        name = "Message with potential PII (phone)"
        body = @{
            message = "Call me at 555-1234"
            conversation_id = "test-pii-2"
            user_id = "user-123"
        } | ConvertTo-Json
    },
    @{
        name = "Toxic/inappropriate message"
        body = @{
            message = "This is a test of inappropriate content"
            conversation_id = "test-toxic-1"
            user_id = "user-123"
        } | ConvertTo-Json
    },
    @{
        name = "Missing conversation_id (should generate one)"
        body = @{
            message = "Test message without conversation_id"
        } | ConvertTo-Json
    },
    @{
        name = "Empty message"
        body = @{
            message = ""
            conversation_id = "test-empty-1"
        } | ConvertTo-Json
    },
    @{
        name = "Very long message"
        body = @{
            message = "A" * 10000
            conversation_id = "test-long-1"
        } | ConvertTo-Json
    },
    @{
        name = "Message with special characters"
        body = @{
            message = "Test with special chars: !@#$%^&*()_+-=[]{}|;:,.<>?"
            conversation_id = "test-special-1"
        } | ConvertTo-Json
    },
    @{
        name = "Message with numbers only"
        body = @{
            message = "1234567890"
            conversation_id = "test-numbers-1"
        } | ConvertTo-Json
    },
    @{
        name = "Missing message field (should fail)"
        body = @{
            conversation_id = "test-missing-msg-1"
        } | ConvertTo-Json
    }
)

$successCount = 0
$failureCount = 0

foreach ($testCase in $testCases) {
    Write-Host "Testing: $($testCase.name)" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "$guardrailStrategyUrl/validate" `
            -Method Post `
            -Body $testCase.body `
            -ContentType "application/json" `
            -ErrorAction Stop
        
        Write-Host "  ✅ Success" -ForegroundColor Green
        Write-Host "  Valid: $($response.valid)" -ForegroundColor Cyan
        Write-Host "  Conversation ID: $($response.conversation_id)" -ForegroundColor Cyan
        Write-Host "  Kafka Sent: $($response.event.kafka_sent)" -ForegroundColor Cyan
        
        if ($response.validation_results) {
            Write-Host "  Validation Details:" -ForegroundColor Gray
            $response.validation_results | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
        }
        
        $successCount++
    }
    catch {
        Write-Host "  ❌ Failed" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($_.ErrorDetails.Message) {
            try {
                $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
                Write-Host "  Details: $($errorDetails.error)" -ForegroundColor Red
            }
            catch {
                Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
            }
        }
        
        $failureCount++
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 500  # Small delay between requests
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Success: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor Red
Write-Host ""

Write-Host "Note: Check Guardrail-Strategy terminal for validation logs" -ForegroundColor Yellow
Write-Host "      Check OFH Dashboard terminal for Kafka consumer logs" -ForegroundColor Yellow


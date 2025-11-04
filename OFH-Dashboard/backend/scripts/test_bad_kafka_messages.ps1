# Test Script for Bad Kafka Messages
# Tests error handling, validation, and DLQ processing

$kafkaBootstrap = "localhost:9092"
$guardrailTopic = "guardrail_events"
$operatorTopic = "operator_actions"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Bad Kafka Messages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Import kafka-python equivalent - we'll use kafka-console-producer or Python
# For Windows PowerShell, we'll use Python to send messages

$pythonScript = @"
import json
import sys
from kafka import KafkaProducer
from datetime import datetime

bootstrap_servers = "$kafkaBootstrap"
guardrail_topic = "$guardrailTopic"
operator_topic = "$operatorTopic"

producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None
)

test_cases = [
    {
        'name': 'Missing conversation_id',
        'topic': guardrail_topic,
        'message': {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'alarm_triggered',
            'severity': 'high',
            'message': 'Test message without conversation_id'
        }
    },
    {
        'name': 'Invalid event_type (not in enum)',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-bad-1',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'invalid_event_type_xyz',
            'severity': 'high',
            'message': 'Test with invalid event_type'
        }
    },
    {
        'name': 'Invalid severity (not in enum)',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-bad-2',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'alarm_triggered',
            'severity': 'super_critical',
            'message': 'Test with invalid severity'
        }
    },
    {
        'name': 'Missing required fields (no timestamp)',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-bad-3',
            'event_type': 'warning_triggered',
            'severity': 'medium',
            'message': 'Test missing timestamp'
        }
    },
    {
        'name': 'Wrong data type (severity as number)',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-bad-4',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'alarm_triggered',
            'severity': 12345,
            'message': 'Test with wrong data type'
        }
    },
    {
        'name': 'Completely empty message',
        'topic': guardrail_topic,
        'message': {}
    },
    {
        'name': 'Null conversation_id',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': None,
            'timestamp': datetime.now().isoformat(),
            'event_type': 'conversation_started',
            'severity': 'info',
            'message': 'Test with null conversation_id'
        }
    },
    {
        'name': 'Invalid timestamp format',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-bad-8',
            'timestamp': 'not-a-valid-date',
            'event_type': 'alarm_triggered',
            'severity': 'high',
            'message': 'Test with invalid timestamp'
        }
    },
    {
        'name': 'Missing required fields for operator action',
        'topic': operator_topic,
        'message': {
            'conversation_id': 'test-bad-9',
            'timestamp': datetime.now().isoformat(),
            'action_type': 'stop_conversation'
            # Missing operator_id and message
        }
    },
    {
        'name': 'Invalid operator action_type',
        'topic': operator_topic,
        'message': {
            'conversation_id': 'test-bad-10',
            'timestamp': datetime.now().isoformat(),
            'action_type': 'invalid_action_xyz',
            'operator_id': 'operator_123',
            'message': 'Test with invalid action_type'
        }
    },
    {
        'name': 'Malformed nested object (invalid detection_metadata)',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-bad-11',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'alarm_triggered',
            'severity': 'high',
            'message': 'Test with malformed nested object',
            'detection_metadata': 'this should be an object not a string'
        }
    },
    {
        'name': 'Valid message (should succeed)',
        'topic': guardrail_topic,
        'message': {
            'conversation_id': 'test-good-1',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'conversation_started',
            'severity': 'info',
            'message': 'This is a valid test message'
        }
    }
]

print("Sending test messages to Kafka...")
print(f"Bootstrap servers: {bootstrap_servers}")
print(f"Topics: {guardrail_topic}, {operator_topic}")
print("")

for i, test_case in enumerate(test_cases, 1):
    try:
        topic = test_case['topic']
        message = test_case['message']
        name = test_case['name']
        
        # Generate a key from conversation_id if available
        key = message.get('conversation_id', f'test-{i}')
        
        print(f"[{i}/{len(test_cases)}] {name}")
        print(f"  Topic: {topic}")
        print(f"  Key: {key}")
        print(f"  Message: {json.dumps(message, indent=2)}")
        
        future = producer.send(topic, value=message, key=key)
        record_metadata = future.get(timeout=10)
        
        print(f"  ✅ Sent successfully to {record_metadata.topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
        print("")
        
    except Exception as e:
        print(f"  ❌ Failed to send: {e}")
        print("")

producer.flush()
producer.close()
print("All test messages sent!")
"@

# Write Python script to temp file
$tempScript = Join-Path $env:TEMP "test_bad_kafka_messages.py"
$pythonScript | Out-File -FilePath $tempScript -Encoding UTF8

Write-Host "Running Python script to send test messages..." -ForegroundColor Yellow
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    
    # Check if kafka-python is installed
    $kafkaCheck = python -c "import kafka; print('kafka-python installed')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: kafka-python not installed!" -ForegroundColor Red
        Write-Host "Install with: pip install kafka-python" -ForegroundColor Yellow
        exit 1
    }
    
    # Run the Python script
    python $tempScript
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Test messages sent!" -ForegroundColor Green
    Write-Host "Check your backend logs for:" -ForegroundColor Yellow
    Write-Host "  - Schema validation failures" -ForegroundColor Yellow
    Write-Host "  - Error handling messages" -ForegroundColor Yellow
    Write-Host "  - DLQ processing (if enabled)" -ForegroundColor Yellow
    Write-Host "  - Retry attempts" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR: Python not found or script failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Use kafka-console-producer if available:" -ForegroundColor Yellow
    Write-Host "  echo '{\"conversation_id\":\"test-bad\",\"message\":\"test\"}' | kafka-console-producer --broker-list localhost:9092 --topic guardrail_events" -ForegroundColor Gray
}

# Cleanup
Remove-Item $tempScript -ErrorAction SilentlyContinue


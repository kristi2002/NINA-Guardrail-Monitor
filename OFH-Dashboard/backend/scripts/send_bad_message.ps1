# Quick PowerShell command to send a bad message to Kafka
# This tests error handling in the consumer

$body = @{
    conversation_id = $null  # NULL conversation_id - should fail
    timestamp = "not-a-valid-date"
    event_type = "invalid_event_type_xyz"  # Not in enum
    severity = 12345  # Wrong type - should be string
    message = "This is a bad test message"
} | ConvertTo-Json

# Send to Kafka using kafka-python (requires Python)
python -c "
from kafka import KafkaProducer
import json
import sys

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

message = $body
future = producer.send('guardrail_events', value=message)
record_metadata = future.get(timeout=10)
print(f'Message sent to {record_metadata.topic}[{record_metadata.partition}] @ offset {record_metadata.offset}')
producer.close()
"


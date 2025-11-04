#!/usr/bin/env python3
"""
Test script to send bad/invalid messages to Kafka
Tests error handling, validation, and DLQ processing
"""

import json
import sys
from kafka import KafkaProducer
from datetime import datetime

BOOTSTRAP_SERVERS = "localhost:9092"
GUARDRAIL_TOPIC = "guardrail_events"
OPERATOR_TOPIC = "operator_actions"

def send_message(producer, topic, message, key=None, name=""):
    """Send a message to Kafka"""
    try:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print(f"Topic: {topic}")
        print(f"Key: {key or 'None'}")
        print(f"Message:")
        print(json.dumps(message, indent=2))
        
        future = producer.send(topic, value=message, key=key)
        record_metadata = future.get(timeout=10)
        
        print(f"✅ SUCCESS: Sent to {record_metadata.topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
        return True
    except Exception as e:
        print(f"❌ FAILED to send: {e}")
        return False

def main():
    """Run all test cases"""
    print("="*60)
    print("BAD KAFKA MESSAGE TEST SUITE")
    print("="*60)
    print(f"Bootstrap servers: {BOOTSTRAP_SERVERS}")
    print(f"Topics: {GUARDRAIL_TOPIC}, {OPERATOR_TOPIC}")
    
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
    )
    
    test_cases = [
        # Test 1: Missing conversation_id
        {
            'name': 'Missing conversation_id',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-1',
            'message': {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'alarm_triggered',
                'severity': 'high',
                'message': 'Test message without conversation_id'
            }
        },
        
        # Test 2: Invalid event_type (not in enum)
        {
            'name': 'Invalid event_type (not in enum)',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-2',
            'message': {
                'conversation_id': 'test-bad-2',
                'timestamp': datetime.now().isoformat(),
                'event_type': 'invalid_event_type_xyz',
                'severity': 'high',
                'message': 'Test with invalid event_type'
            }
        },
        
        # Test 3: Invalid severity (not in enum)
        {
            'name': 'Invalid severity (not in enum)',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-3',
            'message': {
                'conversation_id': 'test-bad-3',
                'timestamp': datetime.now().isoformat(),
                'event_type': 'alarm_triggered',
                'severity': 'super_critical',
                'message': 'Test with invalid severity'
            }
        },
        
        # Test 4: Missing required fields
        {
            'name': 'Missing required fields (no timestamp, no event_id)',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-4',
            'message': {
                'conversation_id': 'test-bad-4',
                'event_type': 'warning_triggered',
                'severity': 'medium',
                'message': 'Test missing required fields'
            }
        },
        
        # Test 5: Wrong data type (severity as number)
        {
            'name': 'Wrong data type (severity as number)',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-5',
            'message': {
                'conversation_id': 'test-bad-5',
                'timestamp': datetime.now().isoformat(),
                'event_type': 'alarm_triggered',
                'severity': 12345,
                'message': 'Test with wrong data type'
            }
        },
        
        # Test 6: Completely empty message
        {
            'name': 'Completely empty message',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-6',
            'message': {}
        },
        
        # Test 7: Null conversation_id
        {
            'name': 'Null conversation_id',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-7',
            'message': {
                'conversation_id': None,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'conversation_started',
                'severity': 'info',
                'message': 'Test with null conversation_id'
            }
        },
        
        # Test 8: Invalid timestamp format
        {
            'name': 'Invalid timestamp format',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-8',
            'message': {
                'conversation_id': 'test-bad-8',
                'timestamp': 'not-a-valid-date',
                'event_type': 'alarm_triggered',
                'severity': 'high',
                'message': 'Test with invalid timestamp'
            }
        },
        
        # Test 9: Missing required fields for operator action
        {
            'name': 'Missing required fields for operator action',
            'topic': OPERATOR_TOPIC,
            'key': 'test-bad-9',
            'message': {
                'conversation_id': 'test-bad-9',
                'timestamp': datetime.now().isoformat(),
                'action_type': 'stop_conversation'
                # Missing operator_id and message
            }
        },
        
        # Test 10: Invalid operator action_type
        {
            'name': 'Invalid operator action_type',
            'topic': OPERATOR_TOPIC,
            'key': 'test-bad-10',
            'message': {
                'conversation_id': 'test-bad-10',
                'timestamp': datetime.now().isoformat(),
                'action_type': 'invalid_action_xyz',
                'operator_id': 'operator_123',
                'message': 'Test with invalid action_type'
            }
        },
        
        # Test 11: Malformed nested object
        {
            'name': 'Malformed nested object (invalid detection_metadata)',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-bad-11',
            'message': {
                'conversation_id': 'test-bad-11',
                'timestamp': datetime.now().isoformat(),
                'event_type': 'alarm_triggered',
                'severity': 'high',
                'message': 'Test with malformed nested object',
                'detection_metadata': 'this should be an object not a string'
            }
        },
        
        # Test 12: Valid message (should succeed)
        {
            'name': 'VALID message (should succeed)',
            'topic': GUARDRAIL_TOPIC,
            'key': 'test-good-1',
            'message': {
                'conversation_id': 'test-good-1',
                'timestamp': datetime.now().isoformat(),
                'event_type': 'conversation_started',
                'severity': 'info',
                'message': 'This is a valid test message',
                'schema_version': '1.0',
                'event_id': f'event-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            }
        },
    ]
    
    print(f"\nSending {len(test_cases)} test messages...")
    print("="*60)
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        success = send_message(
            producer,
            test_case['topic'],
            test_case['message'],
            test_case.get('key'),
            f"[{i}/{len(test_cases)}] {test_case['name']}"
        )
        results.append((test_case['name'], success))
    
    producer.flush()
    producer.close()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✅ SENT" if success else "❌ FAILED"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print("Check your backend logs for:")
    print("  - Schema validation failures")
    print("  - Error handling messages")
    print("  - DLQ processing (if enabled)")
    print("  - Retry attempts")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


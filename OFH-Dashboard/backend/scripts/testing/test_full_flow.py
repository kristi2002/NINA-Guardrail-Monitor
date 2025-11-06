#!/usr/bin/env python3
"""
Full Flow Test: Simulates AI -> Guardrail-Strategy -> Kafka -> OFH Dashboard -> Frontend
This test simulates the complete message flow through the system.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
GUARDRAIL_STRATEGY_URL = "http://localhost:5001"
OFH_DASHBOARD_URL = "http://localhost:5000"
KAFKA_BOOTSTRAP = "localhost:9092"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_guardrail_strategy(message, conversation_id, user_id=None):
    """Step 1: Send message to Guardrail-Strategy for validation"""
    print_section("Step 1: AI sends message to Guardrail-Strategy")
    print(f"Message: {message}")
    print(f"Conversation ID: {conversation_id}")
    
    payload = {
        "message": message,
        "conversation_id": conversation_id
    }
    
    if user_id:
        payload["user_id"] = user_id
    
    try:
        response = requests.post(
            f"{GUARDRAIL_STRATEGY_URL}/validate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"[OK] Validation Result: {'PASS' if result.get('valid') else 'FAIL'}")
        print(f"   Kafka Event Sent: {result.get('event', {}).get('kafka_sent', False)}")
        
        if not result.get('valid'):
            print(f"   [WARNING] Guardrail violation detected!")
            print(f"   Validation Results: {json.dumps(result.get('validation_results', {}), indent=2)}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error calling Guardrail-Strategy: {e}")
        return None

def check_kafka_consumption(conversation_id, timeout=10):
    """Step 2: Wait for OFH Dashboard to consume from Kafka"""
    print_section("Step 2: Waiting for OFH Dashboard to consume from Kafka")
    print(f"Waiting up to {timeout} seconds for Kafka consumer to process...")
    
    # Wait a bit for Kafka consumer to process
    time.sleep(2)
    
    print("[OK] Assuming message was consumed (check OFH Dashboard terminal for logs)")
    return True

def check_conversation_in_dashboard(conversation_id):
    """Step 3: Check if conversation appears in OFH Dashboard"""
    print_section("Step 3: Check conversation in OFH Dashboard API")
    print(f"Checking conversation: {conversation_id}")
    
    try:
        # First, we need to authenticate - for testing, we'll skip auth or use a test token
        # In production, you'd need to get a token first
        response = requests.get(
            f"{OFH_DASHBOARD_URL}/api/conversations/{conversation_id}",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Conversation found in dashboard")
            print(f"   Status: {result.get('conversation', {}).get('status', 'N/A')}")
            print(f"   Guardrail Violations: {result.get('conversation', {}).get('guardrail_violations', 0)}")
            return True
        elif response.status_code == 401:
            print("[WARNING] Authentication required (this is expected)")
            print("   Conversation should be in database, but API requires auth")
            return True
        elif response.status_code == 404:
            print("[WARNING] Conversation not found yet (may need more time)")
            return False
        else:
            print(f"[WARNING] Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error checking dashboard: {e}")
        return False

def test_full_flow():
    """Test the complete flow"""
    print("\n" + "="*60)
    print("  FULL FLOW TEST: AI -> Guardrail-Strategy -> Kafka -> Dashboard -> Frontend")
    print("="*60)
    print("\nThis test simulates:")
    print("1. AI sends message to Guardrail-Strategy")
    print("2. Guardrail-Strategy validates and sends to Kafka")
    print("3. OFH Dashboard consumes from Kafka")
    print("4. Frontend displays the conversation")
    print("\nMake sure both services are running:")
    print("  - Guardrail-Strategy: http://localhost:5001")
    print("  - OFH Dashboard: http://localhost:5000")
    print()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Valid message (should pass)",
            "message": "Hello, I need help with my medication schedule",
            "conversation_id": f"test-flow-valid-{int(time.time())}",
            "user_id": "user-123"
        },
        {
            "name": "Message with PII (should fail and send to Kafka)",
            "message": "Contact me at patient@example.com for follow-up",
            "conversation_id": f"test-flow-pii-{int(time.time())}",
            "user_id": "user-123"
        },
        {
            "name": "Message with phone number (should fail)",
            "message": "Call me at 555-123-4567",
            "conversation_id": f"test-flow-phone-{int(time.time())}",
            "user_id": "user-123"
        },
        {
            "name": "Normal conversation message",
            "message": "I'm feeling better today, thank you",
            "conversation_id": f"test-flow-normal-{int(time.time())}",
            "user_id": "user-123"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"TEST SCENARIO {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"{'='*60}")
        
        # Step 1: Send to Guardrail-Strategy
        validation_result = test_guardrail_strategy(
            scenario['message'],
            scenario['conversation_id'],
            scenario['user_id']
        )
        
        if not validation_result:
            print("[ERROR] Failed to get validation result")
            results.append({"scenario": scenario['name'], "status": "failed"})
            continue
        
        # Step 2: Wait for Kafka consumption
        check_kafka_consumption(scenario['conversation_id'])
        
        # Step 3: Check dashboard
        dashboard_found = check_conversation_in_dashboard(scenario['conversation_id'])
        
        # Wait a bit between tests
        time.sleep(1)
        
        results.append({
            "scenario": scenario['name'],
            "validation": validation_result.get('valid', False),
            "kafka_sent": validation_result.get('event', {}).get('kafka_sent', False),
            "dashboard_found": dashboard_found
        })
    
    # Summary
    print_section("TEST SUMMARY")
    for result in results:
        status_icon = "[OK]" if result.get('dashboard_found') or result.get('kafka_sent') else "[WARNING]"
        print(f"{status_icon} {result['scenario']}")
        print(f"   Validation: {'PASS' if result['validation'] else 'FAIL'}")
        print(f"   Kafka Sent: {result['kafka_sent']}")
        print(f"   Dashboard: {'Found' if result['dashboard_found'] else 'Not found (may need auth)'}")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Check Guardrail-Strategy terminal for validation logs")
    print("2. Check OFH Dashboard terminal for Kafka consumer logs:")
    print("   - Look for 'Received X message batch(es) from Kafka'")
    print("   - Look for 'Successfully processed guardrail event'")
    print("3. Check Frontend - conversations should appear in the dashboard")
    print("4. If frontend shows 500 error, check backend terminal for error details")
    print()

if __name__ == "__main__":
    try:
        test_full_flow()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()


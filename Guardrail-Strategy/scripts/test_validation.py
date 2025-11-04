#!/usr/bin/env python3
"""
Test script for Guardrail-Strategy /validate endpoint
Sends various test messages to test validation logic
"""

import requests
import json
import time
from datetime import datetime

GUARDRAIL_URL = "http://localhost:5001"

def test_validation(message, conversation_id=None, user_id=None, test_name=""):
    """Test a single validation request"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    
    payload = {
        "message": message
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if user_id:
        payload["user_id"] = user_id
    
    try:
        response = requests.post(
            f"{GUARDRAIL_URL}/validate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"Valid: {result.get('valid', 'N/A')}")
        print(f"Conversation ID: {result.get('conversation_id', 'N/A')}")
        print(f"Kafka Sent: {result.get('event', {}).get('kafka_sent', 'N/A')}")
        
        if result.get('validation_results'):
            print("\nValidation Results:")
            print(json.dumps(result['validation_results'], indent=2))
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

def main():
    print("="*60)
    print("Guardrail-Strategy Validation Test Suite")
    print("="*60)
    print(f"Target: {GUARDRAIL_URL}/validate")
    print("")
    
    # Test cases
    test_cases = [
        {
            "name": "Valid normal message",
            "message": "Hello, how are you today?",
            "conversation_id": "test-good-1",
            "user_id": "user-123"
        },
        {
            "name": "Message with email (PII)",
            "message": "Contact me at test@example.com for more info",
            "conversation_id": "test-pii-email",
            "user_id": "user-123"
        },
        {
            "name": "Message with phone number (PII)",
            "message": "My phone is 555-123-4567",
            "conversation_id": "test-pii-phone",
            "user_id": "user-123"
        },
        {
            "name": "Message with SSN (PII)",
            "message": "My SSN is 123-45-6789",
            "conversation_id": "test-pii-ssn",
            "user_id": "user-123"
        },
        {
            "name": "Toxic/inappropriate content",
            "message": "This message contains inappropriate language",
            "conversation_id": "test-toxic-1",
            "user_id": "user-123"
        },
        {
            "name": "Missing conversation_id (auto-generated)",
            "message": "Test message without conversation_id",
            "user_id": "user-123"
        },
        {
            "name": "Empty message",
            "message": "",
            "conversation_id": "test-empty-1"
        },
        {
            "name": "Very long message",
            "message": "A" * 5000,
            "conversation_id": "test-long-1"
        },
        {
            "name": "Special characters",
            "message": "Test with !@#$%^&*()_+-=[]{}|;:,.<>?",
            "conversation_id": "test-special-1"
        },
        {
            "name": "Missing message field (should fail)",
            "message": None,
            "conversation_id": "test-missing-msg"
        }
    ]
    
    success_count = 0
    failure_count = 0
    
    for test_case in test_cases:
        # Skip None messages (test for missing field)
        if test_case["message"] is None:
            test_case["message"] = ""  # Let it fail validation
        
        success = test_validation(
            message=test_case["message"],
            conversation_id=test_case.get("conversation_id"),
            user_id=test_case.get("user_id"),
            test_name=test_case["name"]
        )
        
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Success: {success_count}")
    print(f"Failed: {failure_count}")
    print("")
    print("Note: Check Guardrail-Strategy terminal for validation logs")
    print("      Check OFH Dashboard terminal for Kafka consumer logs")

if __name__ == "__main__":
    main()


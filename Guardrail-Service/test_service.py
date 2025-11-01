#!/usr/bin/env python3
"""
Test script for Guardrail Service
Usage: python test_service.py
"""

import requests
import json
import time
import uuid

# Service URL
SERVICE_URL = "http://localhost:5001"

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to service. Make sure it's running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validation_pass():
    """Test validation with a clean message"""
    print("\n" + "="*60)
    print("Testing Validation - Clean Message (Should Pass)")
    print("="*60)
    
    conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    test_message = "Hello, I have a question about general health information."
    
    payload = {
        "message": test_message,
        "conversation_id": conversation_id,
        "user_id": "test_user_1"
    }
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate",
            json=payload,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get('valid'):
            print("✅ Validation passed as expected")
        else:
            print("⚠️ Validation failed (unexpected)")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validation_pii():
    """Test validation with PII (should fail)"""
    print("\n" + "="*60)
    print("Testing Validation - Message with PII (Should Fail)")
    print("="*60)
    
    conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    test_message = "My email is john.doe@example.com and my phone is 555-123-4567"
    
    payload = {
        "message": test_message,
        "conversation_id": conversation_id,
        "user_id": "test_user_2"
    }
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate",
            json=payload,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if not result.get('valid'):
            print("✅ PII detected as expected")
        else:
            print("⚠️ PII not detected (might be expected if PII detection is disabled)")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validation_toxicity():
    """Test validation with potentially toxic content"""
    print("\n" + "="*60)
    print("Testing Validation - Potentially Toxic Content")
    print("="*60)
    
    conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    test_message = "This message contains inappropriate content and harassment"
    
    payload = {
        "message": test_message,
        "conversation_id": conversation_id,
        "user_id": "test_user_3"
    }
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate",
            json=payload,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if not result.get('valid'):
            print("✅ Toxicity detected as expected")
        else:
            print("⚠️ Toxicity not detected")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validation_compliance():
    """Test validation with compliance issues"""
    print("\n" + "="*60)
    print("Testing Validation - Compliance Check")
    print("="*60)
    
    conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    test_message = "You should take this medication at a dosage of 50mg twice daily"
    
    payload = {
        "message": test_message,
        "conversation_id": conversation_id,
        "user_id": "test_user_4"
    }
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate",
            json=payload,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_batch_validation():
    """Test batch validation endpoint"""
    print("\n" + "="*60)
    print("Testing Batch Validation")
    print("="*60)
    
    conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    messages = [
        "Hello, how are you?",
        "My email is test@example.com",
        "This is a normal conversation"
    ]
    
    payload = {
        "messages": messages,
        "conversation_id": conversation_id,
        "user_id": "test_user_5"
    }
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/validate/batch",
            json=payload,
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Guardrail Service Test Suite")
    print("="*60)
    print(f"Testing service at: {SERVICE_URL}")
    print("\nMake sure the service is running before starting tests!")
    print("Start the service with: python app.py")
    
    time.sleep(2)  # Give user time to read
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    time.sleep(1)
    
    results.append(("Validation - Clean Message", test_validation_pass()))
    time.sleep(1)
    
    results.append(("Validation - PII Detection", test_validation_pii()))
    time.sleep(1)
    
    results.append(("Validation - Toxicity", test_validation_toxicity()))
    time.sleep(1)
    
    results.append(("Validation - Compliance", test_validation_compliance()))
    time.sleep(1)
    
    results.append(("Batch Validation", test_batch_validation()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()


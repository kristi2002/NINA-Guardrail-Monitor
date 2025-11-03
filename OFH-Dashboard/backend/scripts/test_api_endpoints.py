#!/usr/bin/env python3
"""
Test Script for Updated API Endpoints
Tests alerts, conversations, and security routes with real database calls
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USERNAME = "admin"  # Update with your test user
TEST_PASSWORD = "admin123"  # Update with your test user password

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.headers = {}
        
    def login(self, username, password):
        """Login and get JWT token"""
        print_info(f"Logging in as {username}...")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('token')
                    self.headers = {
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    }
                    print_success(f"Login successful! Token received.")
                    return True
                else:
                    print_error(f"Login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print_error(f"Login failed with status {response.status_code}: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print_error(f"Could not connect to {self.base_url}. Is the Flask server running?")
            print_info("Start the server with: python app.py")
            return False
        except Exception as e:
            print_error(f"Login error: {str(e)}")
            return False
    
    def test_get_alerts(self):
        """Test GET /api/alerts"""
        print_info("\n=== Testing GET /api/alerts ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/alerts",
                headers=self.headers,
                params={"hours": 24, "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    alerts = data.get('alerts', [])
                    print_success(f"Retrieved {len(alerts)} alerts")
                    print(f"  Total: {data.get('total', 0)}")
                    print(f"  Critical: {data.get('critical_count', 0)}")
                    print(f"  Active: {data.get('active_count', 0)}")
                    
                    # Show first alert if available
                    if alerts:
                        first_alert = alerts[0]
                        print(f"\n  First alert:")
                        print(f"    ID: {first_alert.get('id')}")
                        print(f"    Event Type: {first_alert.get('event_type')}")
                        print(f"    Severity: {first_alert.get('severity')}")
                        print(f"    Status: {first_alert.get('status')}")
                        print(f"    Message: {first_alert.get('message', '')[:50]}...")
                        return first_alert.get('id')  # Return first alert ID for other tests
                    return None
                else:
                    print_error(f"Failed to get alerts: {data.get('message', 'Unknown error')}")
                    return None
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print_error(f"Error testing get_alerts: {str(e)}")
            return None
    
    def test_get_alert_details(self, alert_id):
        """Test GET /api/alerts/<alert_id>"""
        print_info(f"\n=== Testing GET /api/alerts/{alert_id} ===")
        if not alert_id:
            print_warning("Skipping: No alert ID available")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/alerts/{alert_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    alert = data.get('alert', {})
                    print_success("Retrieved alert details")
                    print(f"  Event ID: {alert.get('event_id')}")
                    print(f"  Conversation ID: {alert.get('conversation_id')}")
                    print(f"  Status: {alert.get('status')}")
                    print(f"  Severity: {alert.get('severity')}")
                    return alert
                else:
                    print_error(f"Failed to get alert details: {data.get('message', 'Unknown error')}")
                    return None
            elif response.status_code == 404:
                print_warning(f"Alert {alert_id} not found (this is OK if database is empty)")
                return None
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print_error(f"Error testing get_alert_details: {str(e)}")
            return None
    
    def test_acknowledge_alert(self, alert_id):
        """Test POST /api/alerts/<alert_id>/acknowledge"""
        print_info(f"\n=== Testing POST /api/alerts/{alert_id}/acknowledge ===")
        if not alert_id:
            print_warning("Skipping: No alert ID available")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/alerts/{alert_id}/acknowledge",
                headers=self.headers,
                json={"operator_id": "test_operator"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print_success("Alert acknowledged successfully")
                    print(f"  Status: {data.get('data', {}).get('status', 'N/A')}")
                    return True
                else:
                    print_error(f"Failed to acknowledge: {data.get('message', 'Unknown error')}")
                    return False
            elif response.status_code == 404:
                print_warning(f"Alert {alert_id} not found (this is OK if database is empty)")
                return False
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print_error(f"Error testing acknowledge_alert: {str(e)}")
            return False
    
    def test_resolve_alert(self, alert_id):
        """Test POST /api/alerts/<alert_id>/resolve"""
        print_info(f"\n=== Testing POST /api/alerts/{alert_id}/resolve ===")
        if not alert_id:
            print_warning("Skipping: No alert ID available")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/alerts/{alert_id}/resolve",
                headers=self.headers,
                json={
                    "resolution_notes": "Test resolution from API test script",
                    "action": "resolved"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print_success("Alert resolved successfully")
                    print(f"  Status: {data.get('data', {}).get('status', 'N/A')}")
                    return True
                else:
                    print_error(f"Failed to resolve: {data.get('message', 'Unknown error')}")
                    return False
            elif response.status_code == 404:
                print_warning(f"Alert {alert_id} not found (this is OK if database is empty)")
                return False
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print_error(f"Error testing resolve_alert: {str(e)}")
            return False
    
    def test_get_conversations(self):
        """Test GET /api/conversations"""
        print_info("\n=== Testing GET /api/conversations ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/conversations",
                headers=self.headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    conversations = data.get('conversations', [])
                    print_success(f"Retrieved {len(conversations)} conversations")
                    
                    # Show first conversation if available
                    if conversations:
                        first_conv = conversations[0]
                        print(f"\n  First conversation:")
                        print(f"    ID: {first_conv.get('id')}")
                        print(f"    Status: {first_conv.get('status')}")
                        print(f"    Risk Level: {first_conv.get('situationLevel')}")
                        print(f"    Violations: {first_conv.get('guardrail_violations', 0)}")
                        return first_conv.get('id')  # Return first conversation ID
                    return None
                else:
                    print_error(f"Failed to get conversations: {data.get('message', 'Unknown error')}")
                    return None
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print_error(f"Error testing get_conversations: {str(e)}")
            return None
    
    def test_get_conversation_details(self, conversation_id):
        """Test GET /api/conversations/<conversation_id>"""
        print_info(f"\n=== Testing GET /api/conversations/{conversation_id} ===")
        if not conversation_id:
            print_warning("Skipping: No conversation ID available")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/conversations/{conversation_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    conversation = data.get('conversation', {})
                    print_success("Retrieved conversation details")
                    print(f"  Patient: {conversation.get('patientInfo', {}).get('name', 'Unknown')}")
                    print(f"  Status: {conversation.get('status')}")
                    print(f"  Total Events: {len(conversation.get('recent_events', []))}")
                    print(f"  Total Actions: {len(conversation.get('recent_actions', []))}")
                    
                    # Verify actions are from OperatorAction (not guardrail events)
                    actions = conversation.get('recent_actions', [])
                    if actions:
                        print(f"\n  Sample operator actions:")
                        for action in actions[:3]:
                            print(f"    - {action.get('type')} by {action.get('operator')} at {action.get('timestamp')}")
                    
                    return conversation
                else:
                    print_error(f"Failed to get conversation details: {data.get('message', 'Unknown error')}")
                    return None
            elif response.status_code == 404:
                print_warning(f"Conversation {conversation_id} not found (this is OK if database is empty)")
                return None
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print_error(f"Error testing get_conversation_details: {str(e)}")
            return None
    
    def test_get_security_overview(self):
        """Test GET /api/security/overview"""
        print_info("\n=== Testing GET /api/security/overview ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/security/overview",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    security_data = data.get('data', {})
                    summary = security_data.get('summary', {})
                    print_success("Retrieved security overview")
                    print(f"  Total Threats: {summary.get('total_threats', 0)}")
                    print(f"  Active Threats: {summary.get('active_threats', 0)}")
                    print(f"  Security Score: {summary.get('security_score', 0)}")
                    
                    recent_incidents = security_data.get('recent_incidents', [])
                    print(f"  Recent Incidents: {len(recent_incidents)}")
                    
                    return True
                else:
                    print_error(f"Failed to get security overview: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print_error(f"Error testing get_security_overview: {str(e)}")
            return False
    
    def test_get_security_threats(self):
        """Test GET /api/security/threats"""
        print_info("\n=== Testing GET /api/security/threats ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/security/threats",
                headers=self.headers,
                params={"severity": "all", "hours": 24}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    threats_data = data.get('data', {})
                    threats = threats_data.get('threats', [])
                    summary = threats_data.get('summary', {})
                    
                    print_success(f"Retrieved {len(threats)} security threats")
                    print(f"  Total: {summary.get('total', 0)}")
                    print(f"  Active: {summary.get('active', 0)}")
                    print(f"  Resolved: {summary.get('resolved', 0)}")
                    
                    return True
                else:
                    print_error(f"Failed to get security threats: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print_error(f"Request failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print_error(f"Error testing get_security_threats: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{'='*60}")
        print(f"  API Endpoint Test Suite")
        print(f"  Testing: {self.base_url}")
        print(f"{'='*60}\n")
        
        # Step 1: Login
        if not self.login(TEST_USERNAME, TEST_PASSWORD):
            print_error("Cannot proceed without authentication")
            return False
        
        results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Step 2: Test Alerts endpoints
        alert_id = self.test_get_alerts()
        if alert_id:
            results['passed'] += 1
        else:
            results['skipped'] += 1
        
        alert_details = self.test_get_alert_details(alert_id)
        if alert_details:
            results['passed'] += 1
        else:
            results['skipped'] += 1
        
        if alert_id:
            if self.test_acknowledge_alert(alert_id):
                results['passed'] += 1
            else:
                results['skipped'] += 1
            
            if self.test_resolve_alert(alert_id):
                results['passed'] += 1
            else:
                results['skipped'] += 1
        
        # Step 3: Test Conversations endpoints
        conversation_id = self.test_get_conversations()
        if conversation_id:
            results['passed'] += 1
        else:
            results['skipped'] += 1
        
        if conversation_id:
            if self.test_get_conversation_details(conversation_id):
                results['passed'] += 1
            else:
                results['skipped'] += 1
        
        # Step 4: Test Security endpoints
        if self.test_get_security_overview():
            results['passed'] += 1
        else:
            results['skipped'] += 1
        
        if self.test_get_security_threats():
            results['passed'] += 1
        else:
            results['skipped'] += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"  Test Summary")
        print(f"{'='*60}")
        print(f"  Passed: {results['passed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"{'='*60}\n")
        
        return results['failed'] == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test API endpoints')
    parser.add_argument('--url', default=BASE_URL, help='Base URL of the API')
    parser.add_argument('--username', default=TEST_USERNAME, help='Username for login')
    parser.add_argument('--password', default=TEST_PASSWORD, help='Password for login')
    
    args = parser.parse_args()
    
    BASE_URL = args.url
    TEST_USERNAME = args.username
    TEST_PASSWORD = args.password
    
    tester = APITester(BASE_URL)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


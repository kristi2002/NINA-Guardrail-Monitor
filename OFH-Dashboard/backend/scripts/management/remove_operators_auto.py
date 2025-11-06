#!/usr/bin/env python3
"""
Auto-remove operator users via API endpoint
Uses default admin credentials or environment variables
"""

import requests
import sys
import os

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# API endpoint
API_URL = "http://localhost:5000/api/auth/remove-operator-users"
LOGIN_URL = "http://localhost:5000/api/auth/login"

def remove_operators_auto():
    """Remove operator users automatically"""
    print("=" * 60)
    print("OFH Dashboard - Remove Operator Users (Auto)")
    print("=" * 60)
    print()
    
    # Get credentials from environment or use defaults
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    
    print(f"Using username: {username}")
    print("Attempting to connect to backend...")
    
    try:
        # Login to get token
        login_response = requests.post(
            LOGIN_URL,
            json={"username": username, "password": password},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed (Status: {login_response.status_code})")
            print(f"   Response: {login_response.text[:200]}")
            return False
        
        login_data = login_response.json()
        if not login_data.get('success'):
            print(f"❌ Login failed: {login_data.get('message', 'Unknown error')}")
            return False
        
        token = login_data.get('token')
        if not token:
            print("❌ No token received from login")
            return False
        
        print("✅ Login successful")
        print()
        
        # Remove operator users
        print("Removing operator users...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            deleted_count = data.get('data', {}).get('deleted_count', 0)
            message = data.get('message', '')
            
            print(f"✅ Success!")
            print(f"   {message}")
            print(f"   Deleted: {deleted_count} operator user(s)")
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   {error_data.get('message', error_data.get('error', 'Unknown error'))}")
            except:
                print(f"   {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend API")
        print("   Make sure the backend is running on http://localhost:5000")
        print("   You can start it with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = remove_operators_auto()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled")
        sys.exit(1)


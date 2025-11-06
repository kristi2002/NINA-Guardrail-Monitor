#!/usr/bin/env python3
"""
Simple script to remove operator users via API endpoint
Uses requests library (install with: pip install requests)
"""

import requests
import sys
import getpass

# API endpoint
API_URL = "http://localhost:5000/api/auth/remove-operator-users"

def remove_operators_via_api():
    """Remove operator users via API"""
    print("=" * 60)
    print("OFH Dashboard - Remove Operator Users (via API)")
    print("=" * 60)
    print()
    
    # Get admin credentials
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    password = getpass.getpass("Enter admin password: ")
    
    # Login to get token
    print("\nLogging in...")
    login_response = requests.post(
        "http://localhost:5000/api/auth/login",
        json={"username": username, "password": password},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
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
    
    # Confirm deletion
    confirm = input("⚠️  Are you sure you want to delete all operator users? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled")
        return False
    
    # Remove operator users
    print("\nRemoving operator users...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(API_URL, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        deleted_count = data.get('data', {}).get('deleted_count', 0)
        print(f"✅ Successfully removed {deleted_count} operator user(s)")
        print(f"   Message: {data.get('message', '')}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")
        return False

if __name__ == "__main__":
    try:
        success = remove_operators_via_api()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend API")
        print("   Make sure the backend is running on http://localhost:5000")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


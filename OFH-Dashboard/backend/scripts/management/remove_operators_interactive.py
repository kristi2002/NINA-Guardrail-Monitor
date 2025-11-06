#!/usr/bin/env python3
"""
Interactive script to remove operator users via API endpoint
Prompts for admin credentials
"""

import requests
import sys
import getpass

API_URL = "http://localhost:5000/api/auth/remove-operator-users"
LOGIN_URL = "http://localhost:5000/api/auth/login"

def main():
    print("=" * 60)
    print("OFH Dashboard - Remove Operator Users")
    print("=" * 60)
    print()
    
    # Get credentials
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    password = getpass.getpass("Enter admin password: ")
    
    if not password:
        print("❌ Password is required")
        return False
    
    try:
        # Login
        print("\nLogging in...")
        login_response = requests.post(
            LOGIN_URL,
            json={"username": username, "password": password},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed (Status: {login_response.status_code})")
            error_data = login_response.json() if login_response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"   {error_data.get('message', login_response.text[:200])}")
            return False
        
        login_data = login_response.json()
        if not login_data.get('success'):
            print(f"❌ Login failed: {login_data.get('message', 'Unknown error')}")
            return False
        
        token = login_data.get('token')
        if not token:
            print("❌ No token received")
            return False
        
        print("✅ Login successful\n")
        
        # Remove operators
        print("Removing operator users...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            deleted_count = data.get('data', {}).get('deleted_count', 0)
            message = data.get('message', '')
            
            print(f"\n✅ Success!")
            print(f"   {message}")
            if deleted_count > 0:
                print(f"   Removed {deleted_count} operator user(s)")
            else:
                print(f"   No operator users found to remove")
            return True
        elif response.status_code == 403:
            print("❌ Access denied: Admin privileges required")
            return False
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
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


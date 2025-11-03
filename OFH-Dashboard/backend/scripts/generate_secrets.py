#!/usr/bin/env python3
"""
Generate Secure Secret Keys for Production
Generates cryptographically secure keys for SECRET_KEY and JWT_SECRET_KEY
"""

import secrets
import string

def generate_secret_key(length=64):
    """
    Generate a cryptographically secure random string
    
    Args:
        length: Length of the key (default 64)
    
    Returns:
        Secure random string
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    """Generate and display secure keys"""
    print("=" * 60)
    print("OFH Dashboard - Secure Key Generator")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Store these keys securely!")
    print("   - Add them to your .env file (NOT in version control)")
    print("   - Use environment variables in production")
    print("   - Never commit keys to Git!")
    print()
    print("-" * 60)
    print("SECRET_KEY (for Flask session encryption)")
    print("-" * 60)
    secret_key = generate_secret_key(64)
    print(secret_key)
    print()
    print("-" * 60)
    print("JWT_SECRET_KEY (for JWT token signing)")
    print("-" * 60)
    jwt_secret = generate_secret_key(64)
    print(jwt_secret)
    print()
    print("-" * 60)
    print("Add these to your .env file:")
    print("-" * 60)
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    print("=" * 60)
    print("✅ Keys generated successfully")
    print("=" * 60)

if __name__ == '__main__':
    main()


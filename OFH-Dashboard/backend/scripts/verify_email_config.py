#!/usr/bin/env python3
"""
Verify email configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Email Configuration Check")
print("=" * 60)
print()

# Check all email-related env vars
config_vars = {
    'EMAIL_ENABLED': os.getenv('EMAIL_ENABLED', 'Not set'),
    'SMTP_HOST': os.getenv('SMTP_HOST', 'Not set'),
    'SMTP_PORT': os.getenv('SMTP_PORT', 'Not set'),
    'SMTP_USER': os.getenv('SMTP_USER', 'Not set'),
    'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD', 'Not set'),
    'SMTP_USE_TLS': os.getenv('SMTP_USE_TLS', 'Not set'),
    'EMAIL_FROM': os.getenv('EMAIL_FROM', 'Not set'),
}

for key, value in config_vars.items():
    if 'PASSWORD' in key:
        if value and value != 'Not set':
            # Show first 4 chars and length
            masked = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
            print(f"✅ {key}: {masked} (length: {len(value)})")
        else:
            print(f"❌ {key}: Not set")
    else:
        status = "✅" if value != 'Not set' else "❌"
        print(f"{status} {key}: {value}")

print()
print("=" * 60)
print("Password Check:")
print("=" * 60)

password = config_vars['SMTP_PASSWORD']
if password and password != 'Not set':
    # Remove spaces if any
    password_clean = password.replace(' ', '')
    if len(password_clean) != 16:
        print(f"⚠️  Warning: App password should be 16 characters")
        print(f"   Current length: {len(password_clean)}")
        print(f"   Password (with spaces removed): {password_clean}")
    else:
        print(f"✅ Password length is correct (16 characters)")
        if ' ' in password:
            print(f"⚠️  Warning: Password contains spaces - should be removed")
            print(f"   Original: {password}")
            print(f"   Cleaned: {password_clean}")
    print()
    print("To fix: Remove all spaces from the app password in .env")
    print("Example: 'ufrt hmwg wrbz jeww' -> 'ufrthmwgwrwzjeww'")
else:
    print("❌ SMTP_PASSWORD not set!")

print()
print("=" * 60)
print("Recipient: krsiti.komini@gmail.com")
print("=" * 60)


#!/usr/bin/env python3
"""
Helper script to update email configuration in .env file
"""

import os
import re
from pathlib import Path

def update_env_file():
    """Update .env file with email configuration"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Copy env.example to .env first:")
        print("   copy env.example .env")
        return False
    
    # Read current .env
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Email configuration values
    config = {
        'EMAIL_ENABLED': 'True',
        'SMTP_HOST': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'nina.guardrail.alerts@gmail.com',
        'SMTP_PASSWORD': 'ufrthmwgwrwzjeww',  # Removed spaces from app password
        'SMTP_USE_TLS': 'True',
        'EMAIL_FROM': 'nina.guardrail.alerts@gmail.com',
        'EMAIL_FROM_NAME': 'OFH Dashboard'
    }
    
    # Update or add each config value
    updated = False
    for key, value in config.items():
        pattern = rf'^{re.escape(key)}=.*$'
        replacement = f'{key}={value}'
        
        if re.search(pattern, content, re.MULTILINE):
            # Update existing
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            updated = True
        else:
            # Add new line
            # Find EMAIL CONFIGURATION section or add at end
            if '# EMAIL CONFIGURATION' in content:
                # Add after EMAIL CONFIGURATION header
                section_pattern = r'(# ============================================\n# EMAIL CONFIGURATION\n# ============================================)'
                replacement_section = rf'\1\n{key}={value}'
                if key not in content:
                    content = re.sub(section_pattern, replacement_section, content)
                    updated = True
            else:
                # Add at end of file
                if not content.endswith('\n'):
                    content += '\n'
                content += f'{key}={value}\n'
                updated = True
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ Email configuration updated in .env file!")
    print()
    print("Updated settings:")
    for key, value in config.items():
        if key == 'SMTP_PASSWORD':
            print(f"  {key}={value[:4]}**** (hidden)")
        else:
            print(f"  {key}={value}")
    
    return True

if __name__ == '__main__':
    success = update_env_file()
    if success:
        print()
        print("🧪 Now test the email:")
        print("   python scripts/test_email.py")


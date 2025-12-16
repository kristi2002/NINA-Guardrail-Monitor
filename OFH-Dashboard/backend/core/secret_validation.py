#!/usr/bin/env python3
"""
Secret Key Validation and Generation
Validates and optionally generates secure secret keys on startup
"""

import os
import secrets
import string
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Default insecure values that should trigger warnings
INSECURE_DEFAULTS = [
    'default-fallback-secret-key',
    'change-this-in-production-min-32-characters-long',
    'change-this-jwt-secret-in-production',
    'your-secret-key-here',
    'your-jwt-secret-key-here',
    'admin123',
    'secret',
    'password'
]

def generate_secret_key(length: int = 64) -> str:
    """
    Generate a cryptographically secure random string
    
    Args:
        length: Length of the key (default 64)
    
    Returns:
        Secure random string
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_secret_key(key: str, key_name: str, min_length: int = 32) -> Tuple[bool, Optional[str]]:
    """
    Validate a secret key
    
    Args:
        key: The secret key to validate
        key_name: Name of the key (for logging)
        min_length: Minimum required length
    
    Returns:
        Tuple of (is_valid, warning_message)
    """
    if not key:
        return False, f"{key_name} is not set"
    
    if len(key) < min_length:
        return False, f"{key_name} is too short (minimum {min_length} characters, got {len(key)})"
    
    # Check if it's an insecure default
    key_lower = key.lower()
    for insecure in INSECURE_DEFAULTS:
        if insecure in key_lower:
            return False, f"{key_name} appears to be using a default/insecure value"
    
    return True, None

def validate_and_ensure_secrets(flask_debug: bool = False) -> None:
    """
    Validate secret keys on startup and optionally generate them in development
    
    Args:
        flask_debug: Whether Flask is in debug mode (development)
    """
    logger.info("🔐 Validating secret keys...")
    
    # Validate SECRET_KEY
    secret_key = os.getenv('SECRET_KEY', 'default-fallback-secret-key')
    is_valid, warning = validate_secret_key(secret_key, 'SECRET_KEY', min_length=32)
    
    if not is_valid:
        if flask_debug:
            # Auto-generate in development
            new_key = generate_secret_key(64)
            os.environ['SECRET_KEY'] = new_key
            logger.warning(
                f"⚠️  {warning}. Auto-generated new SECRET_KEY for development. "
                "⚠️  IMPORTANT: Set SECRET_KEY in .env file for production!"
            )
        else:
            # Production mode - fail or warn
            logger.error(
                f"❌ SECURITY ERROR: {warning}. "
                "Application may not start securely. "
                "Set SECRET_KEY in environment variables or .env file."
            )
            logger.error(
                "💡 Generate a secure key using: "
                "python OFH-Dashboard/backend/scripts/utils/generate_secrets.py"
            )
    else:
        logger.info("✅ SECRET_KEY: Valid")
    
    # Validate JWT_SECRET_KEY
    jwt_secret = os.getenv('JWT_SECRET_KEY', 'change-this-jwt-secret-in-production')
    is_valid, warning = validate_secret_key(jwt_secret, 'JWT_SECRET_KEY', min_length=32)
    
    if not is_valid:
        if flask_debug:
            # Auto-generate in development
            new_key = generate_secret_key(64)
            os.environ['JWT_SECRET_KEY'] = new_key
            logger.warning(
                f"⚠️  {warning}. Auto-generated new JWT_SECRET_KEY for development. "
                "⚠️  IMPORTANT: Set JWT_SECRET_KEY in .env file for production!"
            )
        else:
            # Production mode - fail or warn
            logger.error(
                f"❌ SECURITY ERROR: {warning}. "
                "JWT tokens may not be secure. "
                "Set JWT_SECRET_KEY in environment variables or .env file."
            )
            logger.error(
                "💡 Generate a secure key using: "
                "python OFH-Dashboard/backend/scripts/utils/generate_secrets.py"
            )
    else:
        logger.info("✅ JWT_SECRET_KEY: Valid")
    
    # Check ADMIN_PASSWORD
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    if admin_password == 'admin123' or len(admin_password) < 8:
        if flask_debug:
            logger.warning(
                "⚠️  ADMIN_PASSWORD is using default or weak password. "
                "Change it in production!"
            )
        else:
            logger.error(
                "❌ SECURITY ERROR: ADMIN_PASSWORD is using default or weak password. "
                "This is a security risk in production!"
            )


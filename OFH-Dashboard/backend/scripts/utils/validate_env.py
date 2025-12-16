#!/usr/bin/env python3
"""
Environment Variable Validation Script
Checks .env file for security issues and missing configurations
"""

import os
import sys
from pathlib import Path

def validate_env_file(env_path='.env'):
    """Validate environment variables for security"""
    issues = []
    warnings = []
    info = []
    
    env_file = Path(env_path)
    
    if not env_file.exists():
        print(f"❌ Error: {env_path} file not found!")
        print(f"   Copy backend/env.example to {env_path} and configure it")
        return False
    
    # Read environment variables
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    print("=" * 60)
    print("OFH Dashboard - Environment Variable Validation")
    print("=" * 60)
    print()
    
    # Critical security checks
    print("🔴 Critical Security Checks:")
    print("-" * 60)
    
    # SECRET_KEY
    secret_key = env_vars.get('SECRET_KEY', '')
    if not secret_key or 'change-this' in secret_key.lower() or len(secret_key) < 32:
        issues.append("SECRET_KEY not changed or too short (minimum 32 characters)")
        print("❌ SECRET_KEY: Not configured or insecure")
    else:
        print("✅ SECRET_KEY: Configured")
        info.append(f"SECRET_KEY length: {len(secret_key)} characters")
    
    # JWT_SECRET_KEY
    jwt_secret = env_vars.get('JWT_SECRET_KEY', '')
    if not jwt_secret or 'change-this' in jwt_secret.lower() or len(jwt_secret) < 32:
        issues.append("JWT_SECRET_KEY not changed or too short (minimum 32 characters)")
        print("❌ JWT_SECRET_KEY: Not configured or insecure")
    else:
        print("✅ JWT_SECRET_KEY: Configured")
        info.append(f"JWT_SECRET_KEY length: {len(jwt_secret)} characters")
    
    # CORS_ORIGINS
    cors_origins = env_vars.get('CORS_ORIGINS', 'http://localhost:3001,http://localhost:3000')
    if cors_origins == '*' or '*' in cors_origins:
        issues.append("CORS_ORIGINS contains wildcard '*' - SECURITY RISK in production!")
        print("❌ CORS_ORIGINS: Contains wildcard '*' (SECURITY RISK - use specific origins)")
    elif not cors_origins or cors_origins.strip() == '':
        issues.append("CORS_ORIGINS is empty - must specify allowed origins")
        print("❌ CORS_ORIGINS: Empty (must specify allowed origins)")
    else:
        origins_list = [o.strip() for o in cors_origins.split(',')]
        print(f"✅ CORS_ORIGINS: Configured with {len(origins_list)} origin(s)")
        info.append(f"CORS origins: {', '.join(origins_list)}")
    
    # APP_DEBUG
    app_debug = env_vars.get('APP_DEBUG', 'True')
    if app_debug.lower() in ['true', '1']:
        warnings.append("APP_DEBUG is True - should be False in production")
        print("⚠️  APP_DEBUG: Set to True (should be False in production)")
    else:
        print("✅ APP_DEBUG: Set to False")
    
    print()
    print("🟡 Configuration Checks:")
    print("-" * 60)
    
    # Database
    database_url = env_vars.get('DATABASE_URL', '')
    if 'sqlite' in database_url.lower():
        warnings.append("Using SQLite - PostgreSQL recommended for production")
        print("⚠️  DATABASE_URL: Using SQLite (PostgreSQL recommended for production)")
    elif 'postgresql' in database_url.lower():
        print("✅ DATABASE_URL: Using PostgreSQL")
        if 'sslmode' not in database_url.lower():
            warnings.append("DATABASE_URL doesn't specify SSL mode")
            print("⚠️  DATABASE_URL: SSL mode not specified (add ?sslmode=require)")
    else:
        print("⚠️  DATABASE_URL: Not configured")
    
    # Redis
    redis_url = env_vars.get('REDIS_URL', 'memory://')
    if redis_url == 'memory://':
        warnings.append("Using in-memory Redis - persistent Redis recommended for production")
        print("⚠️  REDIS_URL: Using in-memory storage (Redis server recommended)")
    elif redis_url.startswith('redis://'):
        print("✅ REDIS_URL: Configured for Redis server")
    else:
        print("⚠️  REDIS_URL: Unknown configuration")
    
    # Email
    email_enabled = env_vars.get('EMAIL_ENABLED', 'False')
    if email_enabled.lower() != 'true':
        info.append("Email notifications disabled")
        print("ℹ️  EMAIL_ENABLED: Disabled (configure for email notifications)")
    else:
        smtp_user = env_vars.get('SMTP_USER', '')
        if not smtp_user or 'your-email' in smtp_user:
            warnings.append("Email enabled but SMTP_USER not configured")
            print("⚠️  EMAIL_ENABLED: Enabled but SMTP_USER not configured")
        else:
            print("✅ EMAIL_ENABLED: Configured")
    
    print()
    print("🟢 Optional Configuration:")
    print("-" * 60)
    
    # Kafka (optional)
    kafka_servers = env_vars.get('KAFKA_BOOTSTRAP_SERVERS', '')
    if kafka_servers:
        print("✅ KAFKA_BOOTSTRAP_SERVERS: Configured")
    else:
        print("ℹ️  KAFKA_BOOTSTRAP_SERVERS: Not configured (optional)")
    
    # Slack (optional)
    slack_webhook = env_vars.get('SLACK_WEBHOOK_URL', '')
    if slack_webhook:
        print("✅ SLACK_WEBHOOK_URL: Configured")
    else:
        print("ℹ️  SLACK_WEBHOOK_URL: Not configured (optional)")
    
    print()
    print("=" * 60)
    
    # Summary
    if issues:
        print("❌ CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
    
    if info:
        print("ℹ️  INFORMATION:")
        for item in info:
            print(f"   - {item}")
        print()
    
    # Final result
    if issues:
        print("=" * 60)
        print("❌ VALIDATION FAILED - Fix critical issues before production!")
        print("=" * 60)
        return False
    elif warnings:
        print("=" * 60)
        print("⚠️  VALIDATION PASSED WITH WARNINGS - Review warnings above")
        print("=" * 60)
        return True
    else:
        print("=" * 60)
        print("✅ VALIDATION PASSED - Environment configuration looks good!")
        print("=" * 60)
        return True

if __name__ == '__main__':
    env_file = sys.argv[1] if len(sys.argv) > 1 else '.env'
    success = validate_env_file(env_file)
    sys.exit(0 if success else 1)


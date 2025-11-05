#!/usr/bin/env python3
"""
Comprehensive Security Service for Healthcare AI Systems
Implements authentication, authorization, audit logging, and security monitoring
"""

import hashlib
import secrets
import jwt
import logging
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import re
from typing import Dict, List, Any, Optional

# Get security logger from centralized logging configuration
security_logger = logging.getLogger('security')

class SecurityService:
    """Comprehensive security service for healthcare AI monitoring"""
    
    def __init__(self, app=None):
        self.app = app
        self.jwt_secret = secrets.token_urlsafe(32)
        self.api_keys = {}  # In production, store in database
        self.failed_attempts = {}  # Rate limiting tracking
        self.audit_logs = []  # In production, store in database
        
        # Security configuration
        self.config = {
            'JWT_EXPIRATION_HOURS': 24,
            'MAX_LOGIN_ATTEMPTS': 5,
            'RATE_LIMIT_WINDOW': 300,  # 5 minutes
            'MAX_REQUESTS_PER_WINDOW': 100,
            'PASSWORD_MIN_LENGTH': 8,
            'REQUIRE_HTTPS': False,  # Set to True in production
            'SESSION_TIMEOUT_MINUTES': 60
        }
        
        # User roles and permissions
        self.roles = {
            'admin': {
                'permissions': ['read', 'write', 'delete', 'admin', 'audit', 'acknowledge_alerts'],
                'description': 'Full system access'
            },
            'viewer': {
                'permissions': ['read'],
                'description': 'Read-only access to dashboards'
            },
            'auditor': {
                'permissions': ['read', 'audit'],
                'description': 'Read access and audit logs'
            }
        }
        
        # Mock users (in production, store in database with proper encryption)
        self.users = {
            'admin': {
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'email': 'admin@hospital.com',
                'active': True,
                'created_at': datetime.now().isoformat()
            },
            'viewer': {
                'password_hash': generate_password_hash('viewer123'),
                'role': 'viewer',
                'email': 'viewer@hospital.com',
                'active': True,
                'created_at': datetime.now().isoformat()
            }
        }
    
    def generate_api_key(self, user_id: str, description: str = "") -> str:
        """Generate a new API key for a user"""
        api_key = f"nina_{secrets.token_urlsafe(32)}"
        self.api_keys[api_key] = {
            'user_id': user_id,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'active': True
        }
        self.log_security_event('api_key_generated', user_id, {'description': description})
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return user info"""
        if api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            if key_info['active']:
                key_info['last_used'] = datetime.now().isoformat()
                return key_info
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials"""
        client_ip = request.remote_addr
        
        # Check rate limiting
        if self.is_rate_limited(client_ip):
            self.log_security_event('rate_limit_exceeded', username, {'ip': client_ip})
            return None
        
        if username in self.users:
            user = self.users[username]
            if user['active'] and check_password_hash(user['password_hash'], password):
                self.log_security_event('login_success', username, {'ip': client_ip})
                return {
                    'username': username,
                    'role': user['role'],
                    'email': user['email'],
                    'permissions': self.roles[user['role']]['permissions']
                }
            else:
                self.record_failed_attempt(client_ip)
                self.log_security_event('login_failed', username, {'ip': client_ip, 'reason': 'invalid_credentials'})
        
        return None
    
    def generate_jwt_token(self, user_info: Dict) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            'username': user_info['username'],
            'role': user_info['role'],
            'permissions': user_info['permissions'],
            'exp': datetime.utcnow() + timedelta(hours=self.config['JWT_EXPIRATION_HOURS']),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return user info"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            self.log_security_event('token_expired', 'unknown', {'token_prefix': token[:10]})
            return None
        except jwt.InvalidTokenError:
            self.log_security_event('token_invalid', 'unknown', {'token_prefix': token[:10]})
            return None
    
    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config['RATE_LIMIT_WINDOW'])
        
        if client_ip not in self.failed_attempts:
            return False
        
        # Clean old attempts
        self.failed_attempts[client_ip] = [
            attempt for attempt in self.failed_attempts[client_ip]
            if attempt > window_start
        ]
        
        return len(self.failed_attempts[client_ip]) >= self.config['MAX_LOGIN_ATTEMPTS']
    
    def record_failed_attempt(self, client_ip: str):
        """Record a failed login attempt"""
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []
        self.failed_attempts[client_ip].append(datetime.now())
    
    def validate_input(self, data: Any, input_type: str = 'general') -> Dict[str, Any]:
        """Validate and sanitize input data"""
        validation_result = {
            'valid': True,
            'errors': [],
            'sanitized_data': data
        }
        
        if input_type == 'sql':
            # Check for SQL injection patterns
            sql_patterns = [
                r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
                r"(--|#|/\*|\*/)",
                r"(\bOR\b.*=.*\bOR\b|\bAND\b.*=.*\bAND\b)",
                r"(\'|\";|\")",
            ]
            
            for pattern in sql_patterns:
                if re.search(pattern, str(data), re.IGNORECASE):
                    validation_result['valid'] = False
                    validation_result['errors'].append('Potential SQL injection detected')
                    self.log_security_event('sql_injection_attempt', 'unknown', {'data': str(data)[:100]})
        
        elif input_type == 'xss':
            # Check for XSS patterns
            xss_patterns = [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>.*?</iframe>",
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, str(data), re.IGNORECASE):
                    validation_result['valid'] = False
                    validation_result['errors'].append('Potential XSS attack detected')
                    self.log_security_event('xss_attempt', 'unknown', {'data': str(data)[:100]})
        
        return validation_result
    
    def log_security_event(self, event_type: str, user_id: str, details: Dict = None):
        """Log security events for audit trail"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': request.remote_addr if request else 'system',
            'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'system',
            'details': details or {}
        }
        
        self.audit_logs.append(event)
        security_logger.info(f"Security Event: {json.dumps(event)}")
        
        # In production, also store in database
        # self.store_audit_log_to_db(event)
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.audit_logs
            if datetime.fromisoformat(event['timestamp']) > last_24h
        ]
        
        metrics = {
            'total_events_24h': len(recent_events),
            'login_attempts_24h': len([e for e in recent_events if 'login' in e['event_type']]),
            'failed_logins_24h': len([e for e in recent_events if e['event_type'] == 'login_failed']),
            'security_violations_24h': len([e for e in recent_events if 'injection' in e['event_type'] or 'xss' in e['event_type']]),
            'active_sessions': len([k for k, v in self.api_keys.items() if v['active']]),
            'rate_limited_ips': len(self.failed_attempts),
            'last_security_event': recent_events[-1]['timestamp'] if recent_events else None
        }
        
        return metrics
    
    def check_permissions(self, required_permission: str, user_permissions: List[str]) -> bool:
        """Check if user has required permission"""
        return required_permission in user_permissions or 'admin' in user_permissions

# Decorators for route protection
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check for API key
        api_key = request.headers.get('X-API-Key')
        
        if not token and not api_key:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Validate token or API key
        user_info = None
        if token:
            user_info = security_service.validate_jwt_token(token)
        elif api_key:
            key_info = security_service.validate_api_key(api_key)
            if key_info:
                username = key_info['user_id']
                if username in security_service.users:
                    user = security_service.users[username]
                    user_info = {
                        'username': username,
                        'role': user['role'],
                        'permissions': security_service.roles[user['role']]['permissions']
                    }
        
        if not user_info:
            return jsonify({'error': 'Invalid authentication'}), 401
        
        g.current_user = user_info
        return f(*args, **kwargs)
    
    return decorated_function

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if not security_service.check_permissions(permission, g.current_user['permissions']):
                security_service.log_security_event('permission_denied', g.current_user['username'], {
                    'required_permission': permission,
                    'user_permissions': g.current_user['permissions'],
                    'endpoint': request.endpoint
                })
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Global security service instance
security_service = SecurityService()

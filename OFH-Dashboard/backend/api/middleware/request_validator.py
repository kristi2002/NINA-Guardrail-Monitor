#!/usr/bin/env python3
"""
Request Validation Middleware
Validates incoming requests to prevent malformed data and common security issues
"""

import logging
from flask import request, jsonify
from functools import wraps
import re

logger = logging.getLogger(__name__)

def validate_json_content(f):
    """Decorator to validate JSON content in requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Invalid content type',
                    'message': 'Request must be JSON'
                }), 400
            
            try:
                data = request.get_json(force=True)
                if data is None:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid JSON',
                        'message': 'Request body must contain valid JSON'
                    }), 400
            except Exception as e:
                logger.warning(f"Invalid JSON in request: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON format',
                    'message': 'Request body contains invalid JSON'
                }), 400
        
        return f(*args, **kwargs)
    return decorated_function

def validate_field_length(max_length, fields):
    """
    Decorator to validate field lengths in JSON requests
    :param max_length: Maximum allowed length for specified fields
    :param fields: List of field names to validate
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json() or {}
                
                for field in fields:
                    if field in data:
                        value = data[field]
                        if isinstance(value, str) and len(value) > max_length:
                            return jsonify({
                                'success': False,
                                'error': 'Field too long',
                                'message': f'Field "{field}" exceeds maximum length of {max_length} characters'
                            }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_input(data, max_depth=10):
    """
    Sanitize input data to prevent injection attacks
    Recursively processes dictionaries and lists
    """
    if max_depth <= 0:
        return data
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            if isinstance(key, str):
                # Remove potential SQL injection patterns
                key = re.sub(r'[;\'"\\]', '', key)
            sanitized[key] = sanitize_input(value, max_depth - 1)
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_input(item, max_depth - 1) for item in data]
    
    elif isinstance(data, str):
        # Remove potential SQL and XSS patterns
        sanitized = data
        # Remove SQL injection patterns
        sanitized = re.sub(r'(;|--|/\*|\*/|xp_|sp_)', '', sanitized, flags=re.IGNORECASE)
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        return sanitized
    
    return data

def validate_no_sql_injection(f):
    """Decorator to check for SQL injection patterns in request data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH', 'GET']:
            # Check query parameters
            for key, value in request.args.items():
                if isinstance(value, str) and _contains_sql_injection(value):
                    logger.warning(f"Potential SQL injection detected in query param: {key}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid request',
                        'message': 'Request contains potentially malicious content'
                    }), 400
            
            # Check JSON body
            if request.is_json:
                data = request.get_json()
                if _contains_sql_injection_recursive(data):
                    logger.warning("Potential SQL injection detected in request body")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid request',
                        'message': 'Request contains potentially malicious content'
                    }), 400
        
        return f(*args, **kwargs)
    return decorated_function

def _contains_sql_injection(value):
    """Check if a string contains SQL injection patterns"""
    if not isinstance(value, str):
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r';\s*(drop|delete|update|insert|create|alter)\s+',
        r'--',
        r'/\*.*?\*/',
        r'union\s+select',
        r'xp_\w+',
        r'sp_\w+',
        r'exec\s*\(',
        r'execute\s*\(',
    ]
    
    value_lower = value.lower()
    for pattern in sql_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True
    return False

def _contains_sql_injection_recursive(data, max_depth=10):
    """Recursively check for SQL injection patterns in data structures"""
    if max_depth <= 0:
        return False
    
    if isinstance(data, dict):
        for key, value in data.items():
            if _contains_sql_injection(key) or _contains_sql_injection_recursive(value, max_depth - 1):
                return True
    elif isinstance(data, list):
        for item in data:
            if _contains_sql_injection_recursive(item, max_depth - 1):
                return True
    elif isinstance(data, str):
        return _contains_sql_injection(data)
    
    return False

def validate_required_fields(required_fields):
    """
    Decorator to validate that required fields are present in request
    :param required_fields: List of required field names
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json() or {}
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': 'Missing required fields',
                        'message': f'Required fields missing: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


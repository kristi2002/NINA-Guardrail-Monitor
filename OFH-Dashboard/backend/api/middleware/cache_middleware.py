#!/usr/bin/env python3
"""
Cache Headers Middleware
Adds appropriate cache control headers to API responses
"""

import logging
from flask import request, g
from functools import wraps

logger = logging.getLogger(__name__)

# Cache duration constants (in seconds)
CACHE_DURATIONS = {
    'public': 300,      # 5 minutes - for public data
    'private': 60,      # 1 minute - for user-specific data
    'no-cache': 0,      # No caching - for dynamic data
    'static': 86400,    # 24 hours - for static resources
}

def add_cache_headers(response, cache_type='no-cache', max_age=None):
    """
    Add cache control headers to response
    
    Args:
        response: Flask response object
        cache_type: Type of caching ('public', 'private', 'no-cache', 'static')
        max_age: Override max_age in seconds (optional)
    """
    if cache_type == 'no-cache':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    elif cache_type == 'public':
        max_age = max_age or CACHE_DURATIONS['public']
        response.headers['Cache-Control'] = f'public, max-age={max_age}'
    elif cache_type == 'private':
        max_age = max_age or CACHE_DURATIONS['private']
        response.headers['Cache-Control'] = f'private, max-age={max_age}'
    elif cache_type == 'static':
        max_age = max_age or CACHE_DURATIONS['static']
        response.headers['Cache-Control'] = f'public, max-age={max_age}, immutable'
    
    return response

def cache_control(cache_type='no-cache', max_age=None):
    """
    Decorator to add cache headers to route responses
    
    Usage:
        @cache_control('public', max_age=300)
        def my_route():
            return jsonify(data)
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                add_cache_headers(response, cache_type, max_age)
            return response
        return wrapper
    return decorator

def register_cache_middleware(app):
    """Register cache middleware with Flask app"""
    
    @app.after_request
    def add_default_cache_headers(response):
        """Add default cache headers to all responses"""
        # Skip cache headers for error responses
        if response.status_code >= 400:
            return add_cache_headers(response, 'no-cache')
        
        # Skip cache headers if already set by route
        if 'Cache-Control' in response.headers:
            return response
        
        # Default: no cache for API responses
        # Individual routes can override with @cache_control decorator
        path = request.path
        
        # Add ETag support for better caching
        if hasattr(g, 'cache_key'):
            response.headers['ETag'] = f'"{g.cache_key}"'
        
        # Set default no-cache for API endpoints
        if path.startswith('/api/'):
            return add_cache_headers(response, 'no-cache')
        
        return response


#!/usr/bin/env python3
"""
Request Timeout Middleware
Handles request timeouts to prevent long-running requests from blocking the server
"""

import os
import signal
import logging
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# Default timeout in seconds (30 seconds)
DEFAULT_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30'))

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutError("Request timeout")

def apply_request_timeout(timeout_seconds=DEFAULT_TIMEOUT):
    """
    Decorator to apply timeout to Flask routes
    
    Note: This uses signal-based timeout which only works on Unix systems.
    On Windows, this will log a warning but not enforce timeout.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if os.name == 'nt':  # Windows
                logger.warning("Timeout middleware not fully supported on Windows")
                return f(*args, **kwargs)
            
            # Set up timeout signal
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = f(*args, **kwargs)
                return result
            except TimeoutError:
                logger.warning(f"Request timeout after {timeout_seconds}s: {request.path}")
                return jsonify({
                    'success': False,
                    'error': 'Request timeout',
                    'message': f'Request exceeded maximum time limit of {timeout_seconds} seconds'
                }), 408
            finally:
                # Cancel alarm and restore old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

def register_timeout_middleware(app):
    """
    Register timeout middleware with Flask app
    
    Note: For production, consider using WSGI server-level timeouts (gunicorn --timeout)
    instead of application-level timeouts.
    """
    @app.before_request
    def set_request_start_time():
        """Store request start time"""
        g.request_start_time = os.times()[0] if hasattr(os, 'times') else None


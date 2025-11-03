#!/usr/bin/env python3
"""
API Versioning Middleware
Handles API versioning by rewriting /api/v1/* requests to /api/* internally
"""

import logging
from flask import request, g

logger = logging.getLogger(__name__)

def register_versioning_middleware(app):
    """Register API versioning middleware with Flask app"""
    
    @app.before_request
    def handle_api_versioning():
        """Handle API versioning by rewriting v1 URLs"""
        path = request.path
        
        # If request is to /api/v1/*, rewrite to /api/* internally
        if path.startswith('/api/v1/'):
            # Store original path for reference
            g.api_version = 'v1'
            g.original_path = path
            
            # Rewrite path by removing /v1
            new_path = path.replace('/api/v1/', '/api/', 1)
            request.environ['PATH_INFO'] = new_path
            
            logger.debug(f"API versioning: {path} -> {new_path}")
        elif path.startswith('/api/'):
            # Track that this is the current (non-versioned) API
            g.api_version = 'current'
            g.original_path = path


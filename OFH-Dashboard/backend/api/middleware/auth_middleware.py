#!/usr/bin/env python3
"""
Authentication Middleware
Handles JWT token validation and user authentication
"""

from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Get the JWT secret key from environment
JWT_SECRET_KEY = os.getenv('SECRET_KEY', 'nina-guardrail-monitor-secret-key')

def token_required(f):
    """Decorator to require valid JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid token format',
                    'message': 'Token must be in format: Bearer <token>'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token missing',
                'message': 'Authorization token is required'
            }), 401
        
        try:
            # Decode the token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
            current_user = data.get('username', 'unknown')
            
            # Store user info in Flask's g object for use in route handlers
            g.current_user_id = current_user_id
            g.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': 'Token expired',
                'message': 'Authorization token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': 'Invalid token',
                'message': 'Authorization token is invalid'
            }), 401
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Token validation failed',
                'message': 'Unable to validate authorization token'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # First check if user is authenticated
        if not hasattr(g, 'current_user'):
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'User must be authenticated'
            }), 401
        
        # Check if user has admin privileges
        # This is a simplified check - in production, you'd check against a database
        if g.current_user != 'admin':
            return jsonify({
                'success': False,
                'error': 'Insufficient privileges',
                'message': 'Admin privileges required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated

def get_current_user():
    """Get the current authenticated user from Flask's g object"""
    return getattr(g, 'current_user', None)

def get_current_user_id():
    """Get the current authenticated user ID from Flask's g object"""
    return getattr(g, 'current_user_id', None)

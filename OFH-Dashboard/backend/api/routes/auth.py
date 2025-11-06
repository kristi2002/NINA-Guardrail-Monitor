#!/usr/bin/env python3
"""
Authentication Routes
Handles login, logout, token validation, and user management
"""

from flask import Blueprint, request, jsonify, g, current_app
from datetime import datetime, timedelta
import jwt
import logging
import os
from api.middleware.auth_middleware import token_required, admin_required, get_current_user
from api.middleware.request_validator import validate_json_content, validate_required_fields, validate_no_sql_injection
from services.user_service import UserService

logger = logging.getLogger(__name__)

# Get the JWT secret key from environment
JWT_SECRET_KEY = os.getenv('SECRET_KEY', 'nina-guardrail-monitor-secret-key')

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@validate_json_content
@validate_no_sql_injection
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Missing credentials',
                'message': 'Username and password are required'
            }), 400
        
        # Use database-backed authentication
        user_service = UserService()
        auth_result = user_service.authenticate_user(username, password)
        
        if auth_result['success']:
            user = user_service.user_repo.get_by_username(username)
            
            # Generate JWT token
            token = user.generate_token()
            
            logger.info(f"User {username} logged in successfully")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict_safe(),
                'expires_in': 86400  # 24 hours
            })
        else:
            error_message = auth_result.get('message', 'Username or password is incorrect')
            logger.warning(f"Failed login attempt for username: {username} - {error_message}")
            
            # Log detailed error if available
            if 'errors' in auth_result and auth_result['errors']:
                logger.error(f"Authentication errors: {auth_result['errors']}")
            
            # Determine error type for better client handling
            if 'password is incorrect' in error_message.lower() or 'password' in error_message.lower():
                error_type = 'invalid_password'
            elif 'username not found' in error_message.lower() or 'not found' in error_message.lower():
                error_type = 'user_not_found'
            elif 'locked' in error_message.lower():
                error_type = 'account_locked'
            elif 'deactivated' in error_message.lower():
                error_type = 'account_deactivated'
            elif 'authentication error' in error_message.lower():
                error_type = 'authentication_error'
                # Include the actual error in the message for debugging
                if 'errors' in auth_result and auth_result['errors']:
                    error_message = f"{error_message}: {', '.join(auth_result['errors'])}"
            else:
                error_type = 'invalid_credentials'
            
            return jsonify({
                'success': False,
                'error': error_type,
                'message': error_message
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An error occurred during login'
        }), 500

@auth_bp.route('/validate', methods=['GET', 'POST'])
def validate_token():
    """Validate JWT token endpoint"""
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            # For GET requests, check Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False,
                    'error': 'Token required',
                    'message': 'Authorization header with Bearer token is required'
                }), 400
            token = auth_header.split(' ')[1]
        else:
            # For POST requests, check JSON body
            data = request.get_json()
            if not data or 'token' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Token required',
                    'message': 'Token is required in request body'
                }), 400
            token = data['token']
        
        try:
            # Decode and validate token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            
            return jsonify({
                'success': True,
                'valid': True,
                'user': {
                    'id': payload['user_id'],
                    'username': payload['username']
                },
                'expires_at': datetime.fromtimestamp(payload['exp']).isoformat()
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Token expired'
            })
        except jwt.InvalidTokenError:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Invalid token'
            })
            
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An error occurred during token validation'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token():
    """Refresh JWT token endpoint"""
    try:
        current_user = get_current_user()
        
        # Generate new token
        token_payload = {
            'user_id': g.current_user_id,
            'username': current_user,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        new_token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')
        
        logger.info(f"Token refreshed for user: {current_user}")
        
        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'token': new_token,
            'expires_in': 86400
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An error occurred during token refresh'
        }), 500

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """User logout endpoint - token optional since user is logging out"""
    try:
        # Try to get current user if token is provided, but don't require it
        current_user = None
        try:
            # Check if token is provided and valid
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
                    current_user = data.get('username', 'unknown')
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                    # Token invalid/expired, but that's OK for logout
                    pass
        except Exception:
            # If we can't get user info, that's fine for logout
            pass
        
        if current_user:
            logger.info(f"User {current_user} logged out")
        else:
            logger.info("User logged out (no valid token)")
        
        # Create response explicitly to avoid WSGI issues
        response = jsonify({
            'success': True,
            'message': 'Logout successful'
        })
        response.status_code = 200
        return response
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        # Even if there's an error, return success since logout is idempotent
        # Use explicit response creation
        try:
            response = jsonify({
                'success': True,
                'message': 'Logout completed'
            })
            response.status_code = 200
            return response
        except Exception as response_error:
            # If even jsonify fails, return plain text
            from flask import Response
            return Response('Logout completed', status=200, mimetype='text/plain')

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    try:
        current_user = get_current_user()
        current_user_id = g.current_user_id
        
        return jsonify({
            'success': True,
            'user': {
                'id': current_user_id,
                'username': current_user,
                'role': 'admin',
                'last_login': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An error occurred while fetching profile'
        }), 500

@auth_bp.route('/remove-operator-users', methods=['POST'])
@token_required
@admin_required
def remove_operator_users():
    """Remove all operator users from the database (admin only)"""
    try:
        user_service = UserService()
        result = user_service.delete_users_by_role('operator')
        
        if result.get('success'):
            deleted_count = result.get('data', {}).get('deleted_count', 0)
            logger.info(f"Removed {deleted_count} operator user(s) from database")
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error removing operator users: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': f'An error occurred while removing operator users: {str(e)}'
        }), 500
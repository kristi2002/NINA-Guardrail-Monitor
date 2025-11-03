#!/usr/bin/env python3
"""
Centralized Error Handling Middleware
Handles all API errors consistently
"""

from flask import jsonify, request
import logging
import traceback
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request data',
            'status_code': 400
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'Insufficient permissions',
            'status_code': 403
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'Resource not found',
            'status_code': 404
        }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        return jsonify({
            'success': False,
            'error': 'Unprocessable Entity',
            'message': 'Invalid input data',
            'status_code': 422
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all other HTTP exceptions"""
        return jsonify({
            'success': False,
            'error': error.name,
            'message': str(error.description),
            'status_code': error.code
        }), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all other unhandled exceptions"""
        try:
            # Skip error handling for SocketIO endpoints - let SocketIO handle its own errors
            # Also skip WSGI errors that occur during WebSocket upgrades
            request_path = getattr(request, 'path', '')
            if request_path.startswith('/socket.io/'):
                # Don't handle SocketIO errors - let them propagate to SocketIO's error handler
                # Just log and re-raise
                logger.debug(f"SocketIO request - skipping Flask error handler: {request_path}")
                raise
            
            # Check if this is a WSGI-related error (often happens with SocketIO)
            if 'write() before start_response' in str(error) or isinstance(error, AssertionError):
                # For WSGI errors, especially with WebSocket connections, don't try to return a response
                logger.error(f"WSGI error detected (likely SocketIO related): {error}")
                # Don't try to return a response - just log and let it fail gracefully
                from flask import Response
                return Response('', status=500, mimetype='text/plain')
            
            logger.error(f"Unhandled Exception: {str(error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Try to return JSON response
            response = jsonify({
                'success': False,
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            })
            response.status_code = 500
            return response
        except Exception as handler_error:
            # If even the error handler fails, try minimal response
            logger.critical(f"Error handler failed: {handler_error}")
            try:
                from flask import Response
                return Response('', status=500, mimetype='text/plain')
            except:
                # Last resort - just return None and let WSGI handle it
                return None

    @app.before_request
    def log_request():
        """Log all incoming requests"""
        try:
            # Skip SocketIO endpoints - they handle their own logging and shouldn't go through Flask middleware
            if request.path.startswith('/socket.io/'):
                return
            logger.info(f"{request.method} {request.path} - {request.remote_addr}")
        except Exception:
            # Don't let logging errors break the request
            pass

    @app.after_request
    def log_response(response):
        """Log all outgoing responses"""
        try:
            # Skip SocketIO endpoints - they handle their own logging
            if request.path.startswith('/socket.io/'):
                return response
            logger.info(f"Response: {response.status_code}")
        except Exception:
            # Don't let logging errors break the response
            pass
        return response

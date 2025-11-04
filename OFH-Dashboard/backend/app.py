#!/usr/bin/env python3
"""
Enhanced OFH Dashboard Backend - Clean Architecture
Main Flask application with modular route structure
"""

import os
from dotenv import load_dotenv  # <-- IMPORT THIS
load_dotenv()                   # <-- AND CALL THIS

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from flasgger import Swagger
import logging
from datetime import datetime
import signal
import threading

# Import route modules
from api.routes import register_routes
from api.middleware.error_handler import register_error_handlers
from api.middleware.cache_middleware import register_cache_middleware
from api.middleware.timeout_middleware import register_timeout_middleware
from api.middleware.versioning_middleware import register_versioning_middleware
from core.database import init_database, get_database_manager
from core.logging_config import get_logger  # Import centralized logging
from models import create_all_tables
from services.kafka_integration_service import KafkaIntegrationService

# Initialize Flask app
app = Flask(__name__)
# The SECRET_KEY will now be loaded from your .env file
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-fallback-secret-key')

# Database configuration
# The DATABASE_URL will now be loaded from your .env file
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy()
db.init_app(app)

# Initialize compression
Compress(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'),  # Use Redis in production
    strategy="fixed-window"
)

# Configure SocketIO with error handling
# CRITICAL: SocketIO must be properly configured to handle WebSocket upgrades
# This prevents WSGI "write() before start_response" errors
# NOTE: Using 'threading' mode - eventlet is NOT needed (linter warnings in flask_socketio are safe to ignore)

# Initialize CORS with environment-based configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

# Use same CORS origins for SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins=CORS_ORIGINS if '*' not in CORS_ORIGINS else '*',
    logger=True,
    engineio_logger=False,  # Disable verbose engineio logging
    # async_mode='threading',  # Explicitly use threading mode (no eventlet required)
    ping_timeout=60,  # WebSocket ping timeout
    ping_interval=25,  # WebSocket ping interval
    max_http_buffer_size=1e6  # Max HTTP buffer size for upgrades
)

# Get logger from centralized logging configuration
# (logging_config sets up all handlers on import)
logger = get_logger(__name__)

# Initialize Swagger/OpenAPI documentation
try:
    from api.swagger_config import SWAGGER_CONFIG
    swagger = Swagger(app, config=SWAGGER_CONFIG, template={
        "info": {
            "title": "OFH Dashboard API",
            "version": "2.0.0",
            "description": "Complete API reference for OFH Dashboard"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer YOUR_TOKEN'"
            }
        }
    })
    logger.info("✅ Swagger API documentation initialized at /api/docs")
except Exception as e:
    logger.warning(f"⚠️ Swagger initialization failed: {e}. API documentation will not be available.")

# Register routes and middleware
# IMPORTANT: Versioning middleware must be registered BEFORE routes
# so it can rewrite URLs before route matching
register_versioning_middleware(app)
register_routes(app)
register_error_handlers(app)
register_cache_middleware(app)
register_timeout_middleware(app)

# Make limiter accessible to blueprints
app.extensions['limiter'] = limiter

# Initialize Kafka integration service
kafka_service = None
try:
    # The KAFKA_BOOTSTRAP_SERVERS will now be loaded from your .env file
    kafka_service = KafkaIntegrationService(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        socketio=socketio,
        app=app,
        db=db  # CRITICAL: Pass db instance for database operations
    )
    logger.info("Kafka integration service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Kafka integration service: {e}", exc_info=True)
    logger.warning("Application will continue without Kafka integration")

# Make kafka_service available to routes
app.kafka_service = kafka_service

# WebSocket events (simplified)
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        logger.info(f"Client connected: {request.sid}")
        emit('status', {'message': 'Connected to OFH Dashboard'})
    except Exception as e:
        logger.error(f"Error in handle_connect: {e}", exc_info=True)
        # Don't raise - let SocketIO handle the error

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        logger.info(f"Client disconnected: {request.sid}")
    except Exception as e:
        logger.error(f"Error in handle_disconnect: {e}", exc_info=True)
        # Don't raise - disconnect should always succeed

@socketio.on('join_room')
def handle_join_room(data):
    """Handle client joining a room"""
    try:
        room = data.get('room', 'default') if data else 'default'
        join_room(room)
        logger.info(f"Client {request.sid} joined room: {room}")
        emit('status', {'message': f'Joined room: {room}'})
    except Exception as e:
        logger.error(f"Error in handle_join_room: {e}", exc_info=True)

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle client leaving a room"""
    try:
        room = data.get('room', 'default') if data else 'default'
        leave_room(room)
        logger.info(f"Client {request.sid} left room: {room}")
        emit('status', {'message': f'Left room: {room}'})
    except Exception as e:
        logger.error(f"Error in handle_leave_room: {e}", exc_info=True)

# SocketIO error handler
@socketio.on_error_default
def default_error_handler(e):
    """Handle SocketIO errors"""
    try:
        logger.error(f"SocketIO error: {e}", exc_info=True)
    except Exception:
        # Even logging can fail - just pass
        pass

# Root endpoint
@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'OFH Dashboard API',
        'version': '2.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'auth': '/api/auth',
            'alerts': '/api/alerts',
            'conversations': '/api/conversations',
            'analytics': '/api/analytics',
            'security': '/api/security',
            'metrics': '/api/metrics',
            'health': '/api/health'
        }
    })

if __name__ == '__main__':
    print("=" * 60)
    print("[START] Starting Enhanced OFH Dashboard - Clean Architecture")
    print("=" * 60)
    
    # Get host and port from environment variables
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1']

    print(f"[MODULE] Modular Route Structure")
    print(f"[API] API: http://{API_HOST}:{API_PORT}")
    print(f"[WS] WebSocket: ws://{API_HOST}:{API_PORT}")
    print(f"[DEBUG] Debug Mode: {FLASK_DEBUG}")
    print("=" * 60)
    
    # Initialize database and create tables
    with app.app_context():
        try:
            # Initialize database manager
            db_manager = init_database(DATABASE_URL)
            
            # Test database connection
            if db_manager.test_connection():
                logger.info("✅ Database connection successful")
            else:
                logger.error("❌ Database connection failed")
                raise Exception("Database connection failed")
            
            # Create tables using new models
            if db_manager.create_tables():
                logger.info("✅ Database tables created successfully")
            else:
                logger.error("❌ Failed to create database tables")
                raise Exception("Failed to create database tables")
            
            # Create initial admin and operator users if they don't exist
            try:
                from init_database import create_initial_admin_user, create_initial_operator_user
                logger.info("Checking for initial users...")
                create_initial_admin_user()
                create_initial_operator_user()
            except Exception as user_init_error:
                logger.warning(f"⚠️ Could not initialize users: {user_init_error}")
                logger.warning("You may need to run init_database.py manually or create users via API")
                
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise
    
    # Start Kafka consumer if service is available
    if kafka_service:
        try:
            kafka_service.start_consumer()
            logger.info("✅ Kafka consumer started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
            logger.warning("Application will continue without Kafka consumer")
    else:
        logger.warning("⚠️ Kafka service not available, skipping consumer startup")
    
    # Start the application
    # CRITICAL: Use socketio.run() instead of app.run() to properly handle WebSocket connections
    # This prevents WSGI "write() before start_response" errors
    logger.info("🚀 Starting Flask-SocketIO server...")
    socketio.run(
        app,
        host=API_HOST,
        port=API_PORT,
        debug=FLASK_DEBUG,
        allow_unsafe_werkzeug=True,  # Required for Werkzeug reloader with SocketIO in debug mode
    )
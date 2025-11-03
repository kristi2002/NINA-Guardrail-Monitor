#!/usr/bin/env python3
"""
Centralized Logging Configuration
Provides log rotation and structured logging across the application
"""

import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

def setup_logging():
    """Setup application-wide logging with rotation"""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Get log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Base format for all logs
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Detailed format for file logs
    detailed_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # ==========================================
    # Application Log (Rotating by Size)
    # ==========================================
    app_log_path = os.path.join(logs_dir, 'application.log')
    app_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB per file
        backupCount=5,  # Keep 5 backup files
        encoding='utf-8'
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(detailed_format)
    app_handler.set_name('app_handler')
    
    # ==========================================
    # Error Log (Rotating by Size)
    # ==========================================
    error_log_path = os.path.join(logs_dir, 'errors.log')
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB per file
        backupCount=5,  # Keep 5 backup files
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_format)
    error_handler.set_name('error_handler')
    
    # ==========================================
    # Security Log (Daily Rotation)
    # ==========================================
    security_log_path = os.path.join(logs_dir, 'security.log')
    security_handler = TimedRotatingFileHandler(
        security_log_path,
        when='midnight',
        interval=1,  # Daily
        backupCount=30,  # Keep 30 days
        encoding='utf-8'
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(log_format)
    security_handler.set_name('security_handler')
    
    # ==========================================
    # Audit Log (Daily Rotation)
    # ==========================================
    audit_log_path = os.path.join(logs_dir, 'audit.log')
    audit_handler = TimedRotatingFileHandler(
        audit_log_path,
        when='midnight',
        interval=1,  # Daily
        backupCount=90,  # Keep 90 days for compliance
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(log_format)
    audit_handler.set_name('audit_handler')
    
    # ==========================================
    # Console Handler (for development)
    # ==========================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if os.getenv('APP_DEBUG', 'False').lower() == 'true' else logging.WARNING)
    console_handler.setFormatter(log_format)
    console_handler.set_name('console_handler')
    
    # ==========================================
    # Configure Root Logger
    # ==========================================
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove default handlers to avoid duplicates
    root_logger.handlers = []
    
    # Add all handlers
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # ==========================================
    # Configure Specialized Loggers
    # ==========================================
    
    # Security logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False  # Don't propagate to root
    
    # Audit logger
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)
    audit_logger.propagate = False  # Don't propagate to root
    
    # Error alerts logger (legacy support)
    error_alerts_logger = logging.getLogger('error_alerts')
    error_alerts_logger.setLevel(logging.ERROR)
    error_alerts_logger.addHandler(error_handler)
    error_alerts_logger.propagate = False
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Application Logging Initialized")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Logs Directory: {logs_dir}")
    logger.info("Application Log: Rotating (10MB, 5 backups)")
    logger.info("Error Log: Rotating (10MB, 5 backups)")
    logger.info("Security Log: Daily rotation (30 days retention)")
    logger.info("Audit Log: Daily rotation (90 days retention)")
    logger.info("=" * 60)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

# Auto-setup logging when module is imported
setup_logging()


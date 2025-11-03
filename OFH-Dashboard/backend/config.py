#!/usr/bin/env python3
"""
Configuration Management for NINA Guardrail Monitor
Centralized configuration using environment variables with fallback defaults
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
# load_dotenv()  # Commented out to use default database configuration

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults"""
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load all configuration values"""
        # Kafka Configuration
        self._config.update({
            'KAFKA_BOOTSTRAP_SERVERS': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'KAFKA_GROUP_ID': os.getenv('KAFKA_GROUP_ID', 'nina-dashboard-v2'),
            'KAFKA_CLIENT_ID': os.getenv('KAFKA_CLIENT_ID', 'nina-topic-manager'),
        })
        
        # Database Configuration
        self._config.update({
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///nina_guardrail.db'),
            'DATABASE_HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'DATABASE_PORT': int(os.getenv('DATABASE_PORT', '5432')),
            'DATABASE_NAME': os.getenv('DATABASE_NAME', 'nina_db'),
            'DATABASE_USER': os.getenv('DATABASE_USER', 'nina_user'),
            'DATABASE_PASSWORD': os.getenv('DATABASE_PASSWORD', 'nina_password'),
        })
        
        # Topic Configuration
        self._config.update({
            'TOPIC_RETENTION_MS': int(os.getenv('TOPIC_RETENTION_MS', '604800000')),  # 7 days
            'TOPIC_CLEANUP_POLICY': os.getenv('TOPIC_CLEANUP_POLICY', 'delete'),
            'TOPIC_SEGMENT_MS': int(os.getenv('TOPIC_SEGMENT_MS', '86400000')),  # 1 day
            'TOPIC_COMPRESSION_TYPE': os.getenv('TOPIC_COMPRESSION_TYPE', 'snappy'),
            'TOPIC_MIN_INSYNC_REPLICAS': int(os.getenv('TOPIC_MIN_INSYNC_REPLICAS', '1')),
            'TOPIC_REPLICATION_FACTOR': int(os.getenv('TOPIC_REPLICATION_FACTOR', '1')),
        })
        
        # Application Configuration
        self._config.update({
            'APP_HOST': os.getenv('APP_HOST', '0.0.0.0'),
            'APP_PORT': int(os.getenv('APP_PORT', '5000')),
            'APP_DEBUG': os.getenv('APP_DEBUG', 'True').lower() == 'true',
            'APP_SECRET_KEY': os.getenv('APP_SECRET_KEY', 'your-secret-key-here'),
        })
        
        # Security Configuration
        self._config.update({
            'SECURITY_ENABLED': os.getenv('SECURITY_ENABLED', 'True').lower() == 'true',
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here'),
            'JWT_EXPIRATION_HOURS': int(os.getenv('JWT_EXPIRATION_HOURS', '24')),
        })
        
        # Monitoring Configuration
        self._config.update({
            'MONITORING_ENABLED': os.getenv('MONITORING_ENABLED', 'True').lower() == 'true',
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'ALERT_EMAIL': os.getenv('ALERT_EMAIL', 'admin@example.com'),
        })
        
        # Redis Configuration
        self._config.update({
            'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
            'REDIS_PORT': int(os.getenv('REDIS_PORT', '6379')),
            'REDIS_DB': int(os.getenv('REDIS_DB', '0')),
        })
        
        # Dead Letter Queue Configuration
        self._config.update({
            'DLQ_ENABLED': os.getenv('DLQ_ENABLED', 'True').lower() == 'true',
            'DLQ_MAX_RETRIES': int(os.getenv('DLQ_MAX_RETRIES', '3')),
            'DLQ_RETRY_DELAY': int(os.getenv('DLQ_RETRY_DELAY', '1000')),
        })
        
        # Performance Configuration
        self._config.update({
            'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
            'RETRY_DELAY': int(os.getenv('RETRY_DELAY', '1')),
            'REQUEST_TIMEOUT_MS': int(os.getenv('REQUEST_TIMEOUT_MS', '30000')),
            'DELIVERY_TIMEOUT_MS': int(os.getenv('DELIVERY_TIMEOUT_MS', '120000')),
        })
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)
    
    def get_kafka_config(self) -> Dict[str, Any]:
        """Get Kafka-specific configuration"""
        return {
            'bootstrap_servers': self.get('KAFKA_BOOTSTRAP_SERVERS'),
            'group_id': self.get('KAFKA_GROUP_ID'),
            'client_id': self.get('KAFKA_CLIENT_ID'),
        }
    
    def get_topic_config(self) -> Dict[str, Any]:
        """Get topic-specific configuration"""
        return {
            'cleanup.policy': self.get('TOPIC_CLEANUP_POLICY'),
            'retention.ms': str(self.get('TOPIC_RETENTION_MS')),
            'segment.ms': str(self.get('TOPIC_SEGMENT_MS')),
            'compression.type': self.get('TOPIC_COMPRESSION_TYPE'),
            'min.insync.replicas': str(self.get('TOPIC_MIN_INSYNC_REPLICAS')),
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration"""
        return {
            'url': self.get('DATABASE_URL'),
            'host': self.get('DATABASE_HOST'),
            'port': self.get('DATABASE_PORT'),
            'name': self.get('DATABASE_NAME'),
            'user': self.get('DATABASE_USER'),
            'password': self.get('DATABASE_PASSWORD'),
        }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application-specific configuration"""
        return {
            'host': self.get('APP_HOST'),
            'port': self.get('APP_PORT'),
            'debug': self.get('APP_DEBUG'),
            'secret_key': self.get('APP_SECRET_KEY'),
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security-specific configuration"""
        return {
            'enabled': self.get('SECURITY_ENABLED'),
            'jwt_secret_key': self.get('JWT_SECRET_KEY'),
            'jwt_expiration_hours': self.get('JWT_EXPIRATION_HOURS'),
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring-specific configuration"""
        return {
            'enabled': self.get('MONITORING_ENABLED'),
            'log_level': self.get('LOG_LEVEL'),
            'alert_email': self.get('ALERT_EMAIL'),
        }
    
    def get_dlq_config(self) -> Dict[str, Any]:
        """Get Dead Letter Queue configuration"""
        return {
            'enabled': self.get('DLQ_ENABLED'),
            'max_retries': self.get('DLQ_MAX_RETRIES'),
            'retry_delay': self.get('DLQ_RETRY_DELAY'),
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance-specific configuration"""
        return {
            'max_retries': self.get('MAX_RETRIES'),
            'retry_delay': self.get('RETRY_DELAY'),
            'request_timeout_ms': self.get('REQUEST_TIMEOUT_MS'),
            'delivery_timeout_ms': self.get('DELIVERY_TIMEOUT_MS'),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting"""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration"""
        return key in self._config

# Global configuration instance
config = Config()

# Convenience functions for common configurations
def get_kafka_bootstrap_servers() -> str:
    """Get Kafka bootstrap servers"""
    return config.get('KAFKA_BOOTSTRAP_SERVERS')

def get_kafka_group_id() -> str:
    """Get Kafka group ID"""
    return config.get('KAFKA_GROUP_ID')

def get_database_url() -> str:
    """Get database URL"""
    return config.get('DATABASE_URL')

def get_app_host() -> str:
    """Get application host"""
    return config.get('APP_HOST')

def get_app_port() -> int:
    """Get application port"""
    return config.get('APP_PORT')

def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return config.get('APP_DEBUG')

def is_security_enabled() -> bool:
    """Check if security is enabled"""
    return config.get('SECURITY_ENABLED')

def is_monitoring_enabled() -> bool:
    """Check if monitoring is enabled"""
    return config.get('MONITORING_ENABLED')

def is_dlq_enabled() -> bool:
    """Check if Dead Letter Queue is enabled"""
    return config.get('DLQ_ENABLED')

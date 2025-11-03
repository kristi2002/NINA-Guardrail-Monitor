#!/usr/bin/env python3
"""
Configuration Helper
Provides centralized configuration access for email, escalation, and other services
"""

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class ConfigHelper:
    """Centralized configuration helper for service configurations"""
    
    @staticmethod
    def get_email_config() -> dict:
        """
        Get email service configuration
        
        Returns:
            Dictionary with email configuration
        """
        return {
            'enabled': os.getenv('EMAIL_ENABLED', 'False').lower() == 'true',
            'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_user': os.getenv('SMTP_USER', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'use_tls': os.getenv('SMTP_USE_TLS', 'True').lower() == 'true',
            'from_address': os.getenv('EMAIL_FROM', 'noreply@ofh-dashboard.local'),
            'from_name': os.getenv('EMAIL_FROM_NAME', 'OFH Dashboard')
        }
    
    @staticmethod
    def get_escalation_config() -> dict:
        """
        Get escalation service configuration
        
        Returns:
            Dictionary with escalation configuration
        """
        # Get supervisor email from environment or use default
        supervisor_email = os.getenv('ESCALATION_SUPERVISOR_EMAIL', 'supervisor@ofh-dashboard.local')
        
        return {
            'enabled': os.getenv('ESCALATION_ENABLED', 'True').lower() == 'true',
            'supervisor_email': supervisor_email,
            'escalation_levels': {
                'low': int(os.getenv('ESCALATION_LEVEL_LOW_MINUTES', '60')),
                'medium': int(os.getenv('ESCALATION_LEVEL_MEDIUM_MINUTES', '30')),
                'high': int(os.getenv('ESCALATION_LEVEL_HIGH_MINUTES', '15')),
                'critical': int(os.getenv('ESCALATION_LEVEL_CRITICAL_MINUTES', '5'))
            },
            'notification_channels': os.getenv('ESCALATION_CHANNELS', 'email').split(','),
            'auto_escalate': os.getenv('ESCALATION_AUTO', 'True').lower() == 'true'
        }
    
    @staticmethod
    def get_notification_config() -> dict:
        """
        Get notification service configuration
        
        Returns:
            Dictionary with notification configuration
        """
        return {
            'enabled': os.getenv('NOTIFICATIONS_ENABLED', 'True').lower() == 'true',
            'storage_type': os.getenv('NOTIFICATION_STORAGE', 'database'),  # database, redis, both
            'retention_days': int(os.getenv('NOTIFICATION_RETENTION_DAYS', '30')),
            'max_unread': int(os.getenv('NOTIFICATION_MAX_UNREAD', '100')),
            'channels': {
                'email': os.getenv('NOTIFICATION_EMAIL_ENABLED', 'True').lower() == 'true',
                'sms': os.getenv('NOTIFICATION_SMS_ENABLED', 'False').lower() == 'true',
                'slack': os.getenv('NOTIFICATION_SLACK_ENABLED', 'False').lower() == 'true',
                'teams': os.getenv('NOTIFICATION_TEAMS_ENABLED', 'False').lower() == 'true'
            }
        }
    
    @staticmethod
    def is_email_configured() -> bool:
        """Check if email service is properly configured"""
        config = ConfigHelper.get_email_config()
        return config['enabled'] and config['smtp_user'] and config['smtp_password']
    
    @staticmethod
    def get_supervisor_email() -> str:
        """Get supervisor email for escalations"""
        return ConfigHelper.get_escalation_config()['supervisor_email']
    
    @staticmethod
    def get_all_config() -> dict:
        """Get all service configurations"""
        return {
            'email': ConfigHelper.get_email_config(),
            'escalation': ConfigHelper.get_escalation_config(),
            'notification': ConfigHelper.get_notification_config()
        }


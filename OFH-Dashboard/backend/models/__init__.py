#!/usr/bin/env python3
"""
Models Package
Contains all SQLAlchemy models for the OFH Dashboard
"""

from .base import Base, BaseModel
from .user import User
from .conversation import ConversationSession
# from .alert import Alert  # OBSOLETE - No longer used
from .guardrail_event import GuardrailEvent
from .chat_message import ChatMessage
from .operator_action import OperatorAction
from .notifications import (
    Notification, NotificationStatus, NotificationChannel, 
    NotificationPriority, NotificationType,
    NotificationPreference,
    NotificationRule, RuleCondition, RuleAction,
    NotificationGroup
)

# Export all models
__all__ = [
    'Base',
    'BaseModel',
    'User',
    'ConversationSession',
    # 'Alert',  # OBSOLETE - No longer used
    'GuardrailEvent',
    'ChatMessage',
    'OperatorAction',
    'Notification',
    'NotificationStatus',
    'NotificationChannel',
    'NotificationPriority',
    'NotificationType',
    'NotificationPreference',
    'NotificationRule',
    'RuleCondition',
    'RuleAction',
    'NotificationGroup'
]

# Model registry for easy access
MODELS = {
    'User': User,
    'ConversationSession': ConversationSession,
    # 'Alert': Alert,  # OBSOLETE - No longer used
    'GuardrailEvent': GuardrailEvent,
    'ChatMessage': ChatMessage,
    'OperatorAction': OperatorAction,
    'Notification': Notification,
    'NotificationPreference': NotificationPreference,
    'NotificationRule': NotificationRule,
    'NotificationGroup': NotificationGroup
}

def get_model(model_name):
    """Get model class by name"""
    return MODELS.get(model_name)

def get_all_models():
    """Get all model classes"""
    return list(MODELS.values())

def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

def drop_all_tables(engine):
    """Drop all database tables"""
    Base.metadata.drop_all(engine)

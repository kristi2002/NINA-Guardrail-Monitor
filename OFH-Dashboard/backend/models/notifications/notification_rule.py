#!/usr/bin/env python3
"""
Notification Rule Model
Defines when and how notifications should be sent based on conditions
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Index, Enum, Text
from sqlalchemy.orm import relationship
from models.base import BaseModel
from datetime import datetime, timezone
import enum

class RuleCondition(enum.Enum):
    """Rule condition types"""
    ALERT_SEVERITY = "alert_severity"
    ALERT_TYPE = "alert_type"
    CONVERSATION_RISK_LEVEL = "conversation_risk_level"
    TIME_OF_DAY = "time_of_day"
    DAY_OF_WEEK = "day_of_week"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    PATTERN_DETECTED = "pattern_detected"
    CUSTOM = "custom"

class RuleAction(enum.Enum):
    """Rule actions"""
    SEND_IMMEDIATELY = "send_immediately"
    SEND_DIGEST = "send_digest"
    ESCALATE = "escalate"
    SUPPRESS = "suppress"
    CUSTOM = "custom"

class NotificationRule(BaseModel):
    """Notification rules for conditional sending"""
    
    __tablename__ = "notification_rules"
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)  # Higher priority rules run first
    
    # Conditions (JSON: {condition_type: {operator: str, value: any}})
    conditions = Column(JSON, nullable=False)
    # Example: {
    #   "alert_severity": {"operator": "in", "values": ["critical", "high"]},
    #   "time_of_day": {"operator": "between", "values": ["09:00", "17:00"]}
    # }
    
    # Actions
    action = Column(Enum(RuleAction), nullable=False, default=RuleAction.SEND_IMMEDIATELY)
    action_config = Column(JSON, nullable=True)  # Additional action configuration
    
    # Channels to use
    channels = Column(JSON, nullable=True, default=['email', 'in_app'])
    # List of channels: ['email', 'sms', 'push', 'slack', 'teams', 'webhook']
    
    # Recipients
    recipients = Column(JSON, nullable=True)  # List of user IDs or roles
    recipient_groups = Column(JSON, nullable=True)  # List of group names
    
    # Rate limiting
    rate_limit_enabled = Column(Boolean, default=True, nullable=False)
    rate_limit_window = Column(Integer, default=60, nullable=False)  # minutes
    rate_limit_count = Column(Integer, default=10, nullable=False)  # max notifications per window
    
    # Time restrictions
    time_restrictions_enabled = Column(Boolean, default=False, nullable=False)
    allowed_hours = Column(JSON, nullable=True)  # [{"start": "09:00", "end": "17:00"}]
    allowed_days = Column(JSON, nullable=True)  # ["monday", "tuesday", ...] or ["weekday", "weekend"]
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(String(100), nullable=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    # No direct foreign keys, but can reference users, groups, etc. via JSON
    
    # Indexes
    __table_args__ = (
        Index('idx_rule_enabled_priority', 'enabled', 'priority'),
        Index('idx_rule_expires', 'expires_at'),
    )
    
    def matches_conditions(self, context: dict) -> bool:
        """Check if rule conditions match the given context"""
        if not self.enabled:
            return False
        
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        
        # Check all conditions
        for condition_type, condition_config in self.conditions.items():
            if not self._check_condition(condition_type, condition_config, context):
                return False
        
        return True
    
    def _check_condition(self, condition_type: str, condition_config: dict, context: dict) -> bool:
        """Check a single condition"""
        operator = condition_config.get('operator', 'equals')
        values = condition_config.get('values', condition_config.get('value'))
        if not isinstance(values, list):
            values = [values]
        
        context_value = context.get(condition_type)
        
        if operator == 'equals':
            return context_value in values
        elif operator == 'not_equals':
            return context_value not in values
        elif operator == 'in':
            return context_value in values
        elif operator == 'not_in':
            return context_value not in values
        elif operator == 'greater_than':
            return context_value > values[0] if values else False
        elif operator == 'less_than':
            return context_value < values[0] if values else False
        elif operator == 'between':
            if len(values) >= 2:
                return values[0] <= context_value <= values[1]
        elif operator == 'contains':
            return any(val in str(context_value) for val in values)
        
        return False
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'priority': self.priority,
            'conditions': self.conditions,
            'action': self.action.value if self.action else None,
            'action_config': self.action_config,
            'channels': self.channels,
            'recipients': self.recipients,
            'recipient_groups': self.recipient_groups,
            'rate_limit_enabled': self.rate_limit_enabled,
            'rate_limit_window': self.rate_limit_window,
            'rate_limit_count': self.rate_limit_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


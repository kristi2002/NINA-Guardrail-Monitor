#!/usr/bin/env python3
"""
Notification Model
Stores all notifications sent to users
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Index, Enum
from sqlalchemy.orm import relationship
from models.base import BaseModel
from datetime import datetime, timezone
import enum

class NotificationStatus(enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"

class NotificationChannel(enum.Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    PHONE = "phone"

class NotificationPriority(enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationType(enum.Enum):
    """Notification types"""
    ALERT = "alert"
    CONVERSATION = "conversation"
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"
    ESCALATION = "escalation"

class Notification(BaseModel):
    """Notification model for storing all notifications"""
    
    __tablename__ = "notifications"
    
    # Basic information
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False, default=NotificationType.SYSTEM, index=True)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL, index=True)
    
    # Channel and delivery
    channel = Column(Enum(NotificationChannel), nullable=False, default=NotificationChannel.IN_APP, index=True)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)
    
    # Delivery tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Retry information
    delivery_attempts = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Related entities
    alert_id = Column(String(100), nullable=True, index=True)  # Reference to guardrail event
    conversation_id = Column(String(100), nullable=True, index=True)  # Reference to conversation
    
    # Metadata (renamed to avoid SQLAlchemy conflict)
    notification_metadata = Column(JSON, nullable=True)  # Additional data (action links, buttons, etc.)
    action_url = Column(String(500), nullable=True)  # URL to related resource
    action_label = Column(String(100), nullable=True)  # Label for action button
    
    # Template and formatting
    template_id = Column(String(100), nullable=True)
    html_content = Column(Text, nullable=True)  # For rich HTML emails
    
    # Grouping and digest
    digest_id = Column(String(100), nullable=True, index=True)  # If part of a digest
    group_id = Column(String(100), nullable=True, index=True)  # Notification group
    
    # User interaction
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_by = Column(String(100), nullable=True)  # User who acknowledged
    
    # Relationships
    user = relationship("User", backref="notifications")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_notification_user_status', 'user_id', 'status'),
        Index('idx_notification_type_priority', 'notification_type', 'priority'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_unread', 'user_id', 'is_read'),
        Index('idx_notification_channel_status', 'channel', 'status'),
        Index('idx_notification_expires', 'expires_at'),
    )
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)
        if self.status == NotificationStatus.DELIVERED:
            self.status = NotificationStatus.READ
    
    def mark_as_acknowledged(self, acknowledged_by: str = None):
        """Mark notification as acknowledged"""
        self.is_acknowledged = True
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = acknowledged_by
        if self.status in [NotificationStatus.READ, NotificationStatus.DELIVERED]:
            self.status = NotificationStatus.ACKNOWLEDGED
    
    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def can_retry(self) -> bool:
        """Check if notification can be retried"""
        return (
            self.status == NotificationStatus.FAILED and
            self.delivery_attempts < self.max_retries
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type.value if self.notification_type else None,
            'priority': self.priority.value if self.priority else None,
            'channel': self.channel.value if self.channel else None,
            'status': self.status.value if self.status else None,
            'is_read': self.is_read,
            'is_acknowledged': self.is_acknowledged,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'action_url': self.action_url,
            'action_label': self.action_label,
            'metadata': self.notification_metadata,
            'alert_id': self.alert_id,
            'conversation_id': self.conversation_id
        }


#!/usr/bin/env python3
"""
Notification Preference Model
Stores user preferences for notifications per channel and type
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from models.base import BaseModel
from datetime import datetime, timezone

class NotificationPreference(BaseModel):
    """Notification preferences for users"""
    
    __tablename__ = "notification_preferences"
    
    # User reference
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Global preferences
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5), default='22:00', nullable=False)  # HH:MM format
    quiet_hours_end = Column(String(5), default='08:00', nullable=False)  # HH:MM format
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # Channel preferences (JSON: {channel: {enabled: bool, critical: bool, high: bool, normal: bool, low: bool}})
    channel_preferences = Column(JSON, nullable=True, default={
        'email': {'enabled': True, 'critical': True, 'high': True, 'normal': True, 'low': False},
        'sms': {'enabled': False, 'critical': True, 'high': False, 'normal': False, 'low': False},
        'push': {'enabled': True, 'critical': True, 'high': True, 'normal': True, 'low': True},
        'slack': {'enabled': False, 'critical': True, 'high': False, 'normal': False, 'low': False},
        'teams': {'enabled': False, 'critical': True, 'high': False, 'normal': False, 'low': False},
        'webhook': {'enabled': False, 'critical': True, 'high': False, 'normal': False, 'low': False},
        'phone': {'enabled': False, 'critical': True, 'high': False, 'normal': False, 'low': False}
    })
    
    # Type preferences (JSON: {type: {enabled: bool}})
    type_preferences = Column(JSON, nullable=True, default={
        'alert': {'enabled': True},
        'conversation': {'enabled': True},
        'system': {'enabled': False},
        'security': {'enabled': True},
        'performance': {'enabled': False},
        'maintenance': {'enabled': True},
        'escalation': {'enabled': True}
    })
    
    # Rate limiting
    max_notifications_per_hour = Column(Integer, default=50, nullable=False)
    max_notifications_per_day = Column(Integer, default=200, nullable=False)
    
    # Digest preferences
    digest_enabled = Column(Boolean, default=False, nullable=False)
    digest_frequency = Column(String(20), default='daily', nullable=False)  # hourly, daily, weekly
    digest_time = Column(String(5), default='09:00', nullable=False)  # When to send digest
    
    # Notification channels contact info
    email_address = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    slack_user_id = Column(String(100), nullable=True)
    teams_user_id = Column(String(100), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", backref="notification_preferences", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_pref_user', 'user_id'),
    )
    
    def is_channel_enabled(self, channel: str, priority: str = None) -> bool:
        """Check if a channel is enabled for a priority level"""
        if not self.notifications_enabled:
            return False
        
        if not self.channel_preferences:
            return False
        
        channel_pref = self.channel_preferences.get(channel, {})
        if not channel_pref.get('enabled', False):
            return False
        
        if priority:
            return channel_pref.get(priority.lower(), False)
        
        return True
    
    def is_type_enabled(self, notification_type: str) -> bool:
        """Check if a notification type is enabled"""
        if not self.notifications_enabled:
            return False
        
        if not self.type_preferences:
            return True  # Default enabled if not specified
        
        type_pref = self.type_preferences.get(notification_type, {})
        return type_pref.get('enabled', True)
    
    def is_quiet_hours(self, current_time: datetime = None) -> bool:
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        if not current_time:
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc)
        
        # TODO: Implement timezone-aware quiet hours check
        # For now, simple time comparison (assumes UTC)
        current_hour_min = current_time.strftime('%H:%M')
        return self._is_time_between(current_hour_min, self.quiet_hours_start, self.quiet_hours_end)
    
    def _is_time_between(self, time: str, start: str, end: str) -> bool:
        """Check if time is between start and end (handles midnight crossing)"""
        time_minutes = self._time_to_minutes(time)
        start_minutes = self._time_to_minutes(start)
        end_minutes = self._time_to_minutes(end)
        
        if start_minutes <= end_minutes:
            # Normal case: start < end (e.g., 09:00 to 17:00)
            return start_minutes <= time_minutes <= end_minutes
        else:
            # Midnight crossing: start > end (e.g., 22:00 to 08:00)
            return time_minutes >= start_minutes or time_minutes <= end_minutes
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM string to minutes since midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except:
            return 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notifications_enabled': self.notifications_enabled,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone,
            'channel_preferences': self.channel_preferences,
            'type_preferences': self.type_preferences,
            'max_notifications_per_hour': self.max_notifications_per_hour,
            'max_notifications_per_day': self.max_notifications_per_day,
            'digest_enabled': self.digest_enabled,
            'digest_frequency': self.digest_frequency,
            'digest_time': self.digest_time,
            'email_address': self.email_address,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


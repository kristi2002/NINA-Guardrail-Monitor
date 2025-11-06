#!/usr/bin/env python3
"""
Notification Group Model
Groups users for team-based notification routing
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Table, Index, Text
from sqlalchemy.orm import relationship
from models.base import BaseModel, Base
from datetime import datetime, timezone

# Association table for many-to-many relationship between groups and users
notification_group_members = Table(
    'notification_group_members',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('notification_groups.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)

class NotificationGroup(BaseModel):
    """Notification groups for team-based routing"""
    
    __tablename__ = "notification_groups"
    
    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # Group type
    group_type = Column(String(50), default='custom', nullable=False)  # 'on_call', 'team', 'role', 'custom'
    
    # Default channels for this group
    default_channels = Column(JSON, nullable=True, default=['email', 'in_app'])
    
    # Default priority threshold (only send notifications of this priority or higher)
    min_priority = Column(String(20), default='normal', nullable=False)  # 'low', 'normal', 'high', 'urgent'
    
    # Rotation settings (for on-call groups)
    rotation_enabled = Column(Boolean, default=False, nullable=False)
    rotation_schedule = Column(JSON, nullable=True)  # Rotation schedule details
    
    # Metadata
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    members = relationship(
        "User",
        secondary=notification_group_members,
        backref="notification_groups"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_group_name', 'name'),
        Index('idx_group_enabled', 'enabled'),
        Index('idx_group_type', 'group_type'),
    )
    
    def get_member_ids(self) -> list:
        """Get list of user IDs in this group"""
        return [user.id for user in self.members if user.is_active and not user.is_deleted]
    
    def add_member(self, user):
        """Add a user to the group"""
        if user not in self.members:
            self.members.append(user)
    
    def remove_member(self, user):
        """Remove a user from the group"""
        if user in self.members:
            self.members.remove(user)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'group_type': self.group_type,
            'default_channels': self.default_channels,
            'min_priority': self.min_priority,
            'rotation_enabled': self.rotation_enabled,
            'member_count': len(self.members),
            'member_ids': self.get_member_ids(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


#!/usr/bin/env python3
"""
Notification Group Repository
Handles database operations for notification groups
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.notifications.notification_group import NotificationGroup
import logging

logger = logging.getLogger(__name__)

class NotificationGroupRepository(BaseRepository):
    """Repository for NotificationGroup model"""
    
    def __init__(self, db: Session):
        super().__init__(db, NotificationGroup)
    
    def get_by_name(self, name: str) -> Optional[NotificationGroup]:
        """Get notification group by name"""
        try:
            return self.db.query(NotificationGroup).filter(
                NotificationGroup.name == name,
                NotificationGroup.enabled == True
            ).first()
        except Exception as e:
            logger.error(f"Error getting notification group by name: {e}")
            raise
    
    def get_active_groups(self) -> List[NotificationGroup]:
        """Get all active notification groups"""
        try:
            return self.db.query(NotificationGroup).filter(
                NotificationGroup.enabled == True
            ).all()
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            raise
    
    def get_groups_by_type(self, group_type: str) -> List[NotificationGroup]:
        """Get groups by type"""
        try:
            return self.db.query(NotificationGroup).filter(
                NotificationGroup.group_type == group_type,
                NotificationGroup.enabled == True
            ).all()
        except Exception as e:
            logger.error(f"Error getting groups by type: {e}")
            raise
    
    def get_user_groups(self, user_id: int) -> List[NotificationGroup]:
        """Get all groups a user belongs to"""
        try:
            return self.db.query(NotificationGroup).filter(
                NotificationGroup.enabled == True,
                NotificationGroup.members.any(id=user_id)
            ).all()
        except Exception as e:
            logger.error(f"Error getting user groups: {e}")
            raise


#!/usr/bin/env python3
"""
Notification Preference Repository
Handles database operations for notification preferences
"""

from typing import Optional
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.notifications.notification_preference import NotificationPreference
import logging

logger = logging.getLogger(__name__)

class NotificationPreferenceRepository(BaseRepository):
    """Repository for NotificationPreference model"""
    
    def __init__(self, db: Session):
        super().__init__(db, NotificationPreference)
    
    def get_by_user_id(self, user_id: int) -> Optional[NotificationPreference]:
        """Get notification preferences for a user"""
        try:
            return self.db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            raise
    
    def get_or_create(self, user_id: int) -> NotificationPreference:
        """Get or create notification preferences for a user"""
        try:
            preference = self.get_by_user_id(user_id)
            if not preference:
                preference = NotificationPreference(user_id=user_id)
                self.db.add(preference)
                self.db.commit()
                self.db.refresh(preference)
            return preference
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting or creating notification preferences: {e}")
            raise
    
    def update_preferences(self, user_id: int, preferences: dict) -> Optional[NotificationPreference]:
        """Update notification preferences for a user"""
        try:
            preference = self.get_or_create(user_id)
            
            # Update fields
            for key, value in preferences.items():
                if hasattr(preference, key):
                    setattr(preference, key, value)
            
            self.db.commit()
            self.db.refresh(preference)
            return preference
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating notification preferences: {e}")
            raise


#!/usr/bin/env python3
"""
Notification Rule Repository
Handles database operations for notification rules
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from repositories.base_repository import BaseRepository
from models.notifications.notification_rule import NotificationRule
import logging

logger = logging.getLogger(__name__)

class NotificationRuleRepository(BaseRepository):
    """Repository for NotificationRule model"""
    
    def __init__(self, db: Session):
        super().__init__(db, NotificationRule)
    
    def get_active_rules(self) -> List[NotificationRule]:
        """Get all active notification rules ordered by priority"""
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            return self.db.query(NotificationRule).filter(
                NotificationRule.enabled == True,
                or_(
                    NotificationRule.expires_at.is_(None),
                    NotificationRule.expires_at > now
                )
            ).order_by(desc(NotificationRule.priority)).all()
        except Exception as e:
            logger.error(f"Error getting active rules: {e}")
            raise
    
    def get_matching_rules(self, context: dict) -> List[NotificationRule]:
        """Get rules that match the given context"""
        try:
            active_rules = self.get_active_rules()
            matching_rules = []
            
            for rule in active_rules:
                if rule.matches_conditions(context):
                    matching_rules.append(rule)
            
            return matching_rules
        except Exception as e:
            logger.error(f"Error getting matching rules: {e}")
            raise
    
    def increment_trigger_count(self, rule_id: int):
        """Increment trigger count for a rule"""
        try:
            rule = self.get_by_id(rule_id)
            if rule:
                rule.trigger_count += 1
                from datetime import datetime, timezone
                rule.last_triggered_at = datetime.now(timezone.utc)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error incrementing trigger count: {e}")
            raise


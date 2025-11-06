#!/usr/bin/env python3
"""
Notification Escalation Service
Handles escalation policies for notifications
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from services.base_service import BaseService
from repositories.notifications.notification_repository import NotificationRepository
from repositories.user_repository import UserRepository
from models.notifications.notification import Notification, NotificationStatus, NotificationPriority
from services.notifications.enhanced_notification_service import EnhancedNotificationService
import logging

logger = logging.getLogger(__name__)


class NotificationEscalationService(BaseService):
    """Service for notification escalation"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.notification_repo = NotificationRepository(self.get_session())
        self.user_repo = UserRepository(self.get_session())
        self.notification_service = EnhancedNotificationService(self.get_session())
    
    def check_and_escalate(
        self,
        notification_id: int,
        escalation_policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if notification needs escalation and escalate if needed"""
        try:
            notification = self.notification_repo.get_by_id(notification_id)
            if not notification:
                return self.format_response(
                    success=False,
                    message="Notification not found"
                )
            
            # Check if already acknowledged
            if notification.is_acknowledged:
                return self.format_response(
                    success=True,
                    message="Notification already acknowledged, no escalation needed"
                )
            
            # Check if escalation is enabled
            if not escalation_policy.get('enabled', False):
                return self.format_response(
                    success=True,
                    message="Escalation disabled"
                )
            
            # Check timeout
            timeout_minutes = escalation_policy.get('timeout_minutes', 15)
            time_since_creation = datetime.now(timezone.utc) - notification.created_at
            
            if time_since_creation.total_seconds() < timeout_minutes * 60:
                return self.format_response(
                    success=True,
                    message=f"Escalation timeout not reached ({timeout_minutes} minutes)"
                )
            
            # Determine escalation target
            escalation_target = self._get_escalation_target(
                notification,
                escalation_policy
            )
            
            if not escalation_target:
                return self.format_response(
                    success=False,
                    message="No escalation target found"
                )
            
            # Create escalation notification
            escalation_message = self._create_escalation_message(
                notification,
                escalation_policy
            )
            
            result = self.notification_service.send_notification(
                user_id=escalation_target,
                title=f"[ESCALATED] {notification.title}",
                message=escalation_message,
                notification_type=notification.notification_type,
                priority=NotificationPriority.URGENT,  # Escalations are always urgent
                channels=['email', 'in_app'],
                metadata={
                    'escalated_from': notification.id,
                    'original_notification_id': notification.id,
                    'escalation_level': escalation_policy.get('level', 1)
                },
                check_preferences=False,  # Escalations bypass preferences
                check_rate_limit=False  # Escalations bypass rate limits
            )
            
            # Update original notification metadata
            if not notification.notification_metadata:
                notification.notification_metadata = {}
            notification.notification_metadata['escalated'] = True
            notification.notification_metadata['escalated_at'] = datetime.now(timezone.utc).isoformat()
            notification.notification_metadata['escalated_to'] = escalation_target
            
            self.notification_repo.db.commit()
            
            return self.format_response(
                success=True,
                data={
                    'escalated': True,
                    'escalation_target': escalation_target,
                    'escalation_notification': result.get('data')
                },
                message="Notification escalated successfully"
            )
            
        except Exception as e:
            self.notification_repo.db.rollback()
            return self.handle_exception(e, 'check_and_escalate')
    
    def _get_escalation_target(
        self,
        notification: Notification,
        escalation_policy: Dict[str, Any]
    ) -> Optional[int]:
        """Get the escalation target user ID"""
        try:
            escalation_type = escalation_policy.get('type', 'supervisor')
            
            if escalation_type == 'supervisor':
                # Get supervisor from user's department or default
                supervisor_email = escalation_policy.get('supervisor_email')
                if supervisor_email:
                    supervisor = self.user_repo.get_by_email(supervisor_email)
                    if supervisor:
                        return supervisor.id
            
            elif escalation_type == 'role':
                # Escalate to users with specific role
                role = escalation_policy.get('target_role', 'admin')
                users = self.user_repo.get_users_by_role(role, limit=1)
                if users:
                    return users[0].id
            
            elif escalation_type == 'group':
                # Escalate to notification group
                group_name = escalation_policy.get('target_group')
                if group_name:
                    from repositories.notifications.notification_group_repository import NotificationGroupRepository
                    group_repo = NotificationGroupRepository(self.get_session())
                    group = group_repo.get_by_name(group_name)
                    if group and group.members:
                        # Return first active member
                        for member in group.members:
                            if member.is_active and not member.is_deleted:
                                return member.id
            
            elif escalation_type == 'round_robin':
                # Round robin escalation
                role = escalation_policy.get('target_role', 'admin')
                users = self.user_repo.get_users_by_role(role, limit=100)
                if users:
                    # Simple round robin based on notification count
                    # In production, use a proper round-robin algorithm
                    return users[0].id
            
            # Default: escalate to first admin
            admins = self.user_repo.get_users_by_role('admin', limit=1)
            if admins:
                return admins[0].id
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting escalation target: {e}")
            return None
    
    def _create_escalation_message(
        self,
        notification: Notification,
        escalation_policy: Dict[str, Any]
    ) -> str:
        """Create escalation message"""
        time_ago = datetime.now(timezone.utc) - notification.created_at
        minutes_ago = int(time_ago.total_seconds() / 60)
        
        message = f"""This notification requires immediate attention.

Original Notification:
Title: {notification.title}
Message: {notification.message}
Priority: {notification.priority.value if notification.priority else 'normal'}
Created: {minutes_ago} minute(s) ago

The original notification has not been acknowledged within the {escalation_policy.get('timeout_minutes', 15)} minute timeout period.

Please review and take appropriate action.
"""
        return message
    
    def process_escalations(self, escalation_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process all pending escalations"""
        try:
            # Get all unacknowledged notifications that are older than escalation timeout
            now = datetime.now(timezone.utc)
            escalated = 0
            failed = 0
            
            for policy in escalation_policies:
                if not policy.get('enabled', False):
                    continue
                
                timeout_minutes = policy.get('timeout_minutes', 15)
                cutoff_time = now - timedelta(minutes=timeout_minutes)
                
                # Get notifications that need escalation
                notifications = self.notification_repo.db.query(Notification).filter(
                    Notification.is_acknowledged == False,
                    Notification.created_at <= cutoff_time,
                    Notification.priority.in_([
                        NotificationPriority.HIGH,
                        NotificationPriority.URGENT
                    ]),
                    ~Notification.notification_metadata.contains({'escalated': True})  # Not already escalated
                ).all()
                
                for notification in notifications:
                    result = self.check_and_escalate(notification.id, policy)
                    if result.get('success'):
                        escalated += 1
                    else:
                        failed += 1
            
            return self.format_response(
                success=True,
                data={
                    'escalated': escalated,
                    'failed': failed
                },
                message=f"Processed escalations: {escalated} successful, {failed} failed"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'process_escalations')


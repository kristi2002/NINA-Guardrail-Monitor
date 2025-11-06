#!/usr/bin/env python3
"""
Enhanced Notification Service
Complete notification system with all features
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from services.base_service import BaseService
from repositories.user_repository import UserRepository
from repositories.notifications.notification_repository import NotificationRepository
from repositories.notifications.notification_preference_repository import NotificationPreferenceRepository
from repositories.notifications.notification_rule_repository import NotificationRuleRepository
from models.notifications.notification import (
    Notification, NotificationStatus, NotificationChannel, 
    NotificationPriority, NotificationType
)
from models.notifications.notification_preference import NotificationPreference
from services.notifications.notification_infrastructure_service import NotificationService as InfrastructureService, NotificationPriority as InfraPriority
import logging
import math
import random

logger = logging.getLogger(__name__)


class EnhancedNotificationService(BaseService):
    """Enhanced notification service with all features"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.user_repo = UserRepository(self.get_session())
        self.notification_repo = NotificationRepository(self.get_session())
        self.preference_repo = NotificationPreferenceRepository(self.get_session())
        self.rule_repo = NotificationRuleRepository(self.get_session())
        self.infrastructure_service = InfrastructureService()
    
    # ============================================
    # Core Notification Methods
    # ============================================
    
    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        alert_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        html_content: Optional[str] = None
    ) -> Notification:
        """Create a new notification in the database"""
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                channel=channel,
                status=NotificationStatus.PENDING,
                alert_id=alert_id,
                conversation_id=conversation_id,
                notification_metadata=metadata or {},
                action_url=action_url,
                action_label=action_label,
                expires_at=expires_at,
                html_content=html_content,
                max_retries=3
            )
            
            self.notification_repo.db.add(notification)
            self.notification_repo.db.commit()
            self.notification_repo.db.refresh(notification)
            
            self.log_operation('notification_created', str(user_id), {
                'notification_id': notification.id,
                'type': notification_type.value,
                'priority': priority.value,
                'channel': channel.value
            })
            
            return notification
        except Exception as e:
            self.notification_repo.db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise
    
    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[str]] = None,
        alert_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        html_content: Optional[str] = None,
        check_preferences: bool = True,
        check_rate_limit: bool = True
    ) -> Dict[str, Any]:
        """Send notification with all checks and delivery"""
        try:
            # Get user preferences
            preference = self.preference_repo.get_or_create(user_id)
            
            # Check if notifications are enabled
            if check_preferences and not preference.notifications_enabled:
                return self.format_response(
                    success=False,
                    message="Notifications are disabled for this user"
                )
            
            # Check quiet hours
            if check_preferences and preference.is_quiet_hours():
                # Store for later delivery unless urgent
                if priority != NotificationPriority.URGENT:
                    return self.format_response(
                        success=False,
                        message="Notification queued due to quiet hours"
                    )
            
            # Determine channels
            if not channels:
                channels = self._determine_channels(preference, priority, notification_type)
            
            if not channels:
                return self.format_response(
                    success=False,
                    message="No enabled channels for this notification"
                )
            
            # Check rate limits
            if check_rate_limit:
                rate_limit_result = self._check_rate_limit(user_id, preference, channels)
                if not rate_limit_result['allowed']:
                    return self.format_response(
                        success=False,
                        message=f"Rate limit exceeded: {rate_limit_result['message']}"
                    )
            
            # Create and send notifications
            notifications_created = []
            for channel_str in channels:
                channel = self._string_to_channel(channel_str)
                if not channel:
                    continue
                
                # Check if channel is enabled for this priority
                if check_preferences and not preference.is_channel_enabled(channel_str, priority.value):
                    continue
                
                # Create notification record
                notification = self.create_notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    channel=channel,
                    alert_id=alert_id,
                    conversation_id=conversation_id,
                    notification_metadata=metadata,
                    action_url=action_url,
                    action_label=action_label,
                    html_content=html_content
                )
                
                # Send via infrastructure
                delivery_result = self._send_via_channel(
                    notification, 
                    preference,
                    title,
                    message,
                    priority,
                    html_content
                )
                
                notifications_created.append({
                    'notification_id': notification.id,
                    'channel': channel_str,
                    'status': delivery_result['status']
                })
            
            return self.format_response(
                success=True,
                data={
                    'notifications_created': notifications_created,
                    'count': len(notifications_created)
                },
                message=f"Notification sent via {len(notifications_created)} channel(s)"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'send_notification')
    
    def _send_via_channel(
        self,
        notification: Notification,
        preference: NotificationPreference,
        title: str,
        message: str,
        priority: NotificationPriority,
        html_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send notification via specific channel"""
        try:
            channel = notification.channel
            
            if channel == NotificationChannel.EMAIL:
                email = preference.email_address or self._get_user_email(notification.user_id)
                if email:
                    success = self.infrastructure_service.send_email(
                        [email],
                        title,
                        message,
                        self._priority_to_infra(priority),
                        html_content
                    )
                    if success:
                        self.notification_repo.update_delivery_status(
                            notification.id,
                            NotificationStatus.SENT
                        )
                        return {'status': 'sent', 'success': True}
                    else:
                        self.notification_repo.update_delivery_status(
                            notification.id,
                            NotificationStatus.FAILED,
                            "Email delivery failed"
                        )
                        return {'status': 'failed', 'success': False}
            
            elif channel == NotificationChannel.SMS:
                phone = preference.phone_number or self._get_user_phone(notification.user_id)
                if phone:
                    success = self.infrastructure_service.send_sms(
                        [phone],
                        message,
                        self._priority_to_infra(priority)
                    )
                    if success:
                        self.notification_repo.update_delivery_status(
                            notification.id,
                            NotificationStatus.SENT
                        )
                        return {'status': 'sent', 'success': True}
            
            elif channel == NotificationChannel.SLACK:
                slack_user_id = preference.slack_user_id
                if slack_user_id:
                    success = self.infrastructure_service.send_slack_message(
                        message,
                        None,
                        self._priority_to_infra(priority)
                    )
                    if success:
                        self.notification_repo.update_delivery_status(
                            notification.id,
                            NotificationStatus.SENT
                        )
                        return {'status': 'sent', 'success': True}
            
            elif channel == NotificationChannel.TEAMS:
                teams_user_id = preference.teams_user_id
                if teams_user_id:
                    success = self.infrastructure_service.send_teams_message(
                        message,
                        self._priority_to_infra(priority)
                    )
                    if success:
                        self.notification_repo.update_delivery_status(
                            notification.id,
                            NotificationStatus.SENT
                        )
                        return {'status': 'sent', 'success': True}
            
            elif channel == NotificationChannel.IN_APP:
                # In-app notifications are automatically available
                self.notification_repo.update_delivery_status(
                    notification.id,
                    NotificationStatus.SENT
                )
                return {'status': 'sent', 'success': True}
            
            # Default: mark as sent for in-app
            self.notification_repo.update_delivery_status(
                notification.id,
                NotificationStatus.SENT
            )
            return {'status': 'sent', 'success': True}
            
        except Exception as e:
            logger.error(f"Error sending notification via channel: {e}")
            self.notification_repo.update_delivery_status(
                notification.id,
                NotificationStatus.FAILED,
                str(e)
            )
            return {'status': 'failed', 'success': False, 'error': str(e)}
    
    # ============================================
    # Rate Limiting
    # ============================================
    
    def _check_rate_limit(
        self,
        user_id: int,
        preference: NotificationPreference,
        channels: List[str]
    ) -> Dict[str, Any]:
        """Check if user has exceeded rate limits"""
        try:
            now = datetime.now(timezone.utc)
            
            # Check hourly limit
            hour_ago = now - timedelta(hours=1)
            hourly_count = self.notification_repo.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.created_at >= hour_ago,
                Notification.channel.in_([self._string_to_channel(c) for c in channels if self._string_to_channel(c)])
            ).count()
            
            if hourly_count >= preference.max_notifications_per_hour:
                return {
                    'allowed': False,
                    'message': f'Hourly limit of {preference.max_notifications_per_hour} exceeded'
                }
            
            # Check daily limit
            day_ago = now - timedelta(days=1)
            daily_count = self.notification_repo.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.created_at >= day_ago
            ).count()
            
            if daily_count >= preference.max_notifications_per_day:
                return {
                    'allowed': False,
                    'message': f'Daily limit of {preference.max_notifications_per_day} exceeded'
                }
            
            return {'allowed': True}
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {'allowed': True}  # Allow on error
    
    # ============================================
    # Retry Logic with Exponential Backoff
    # ============================================
    
    def retry_failed_notifications(self, max_retries: int = 10) -> Dict[str, Any]:
        """Retry failed notifications with exponential backoff"""
        try:
            failed_notifications = self.notification_repo.get_failed_notifications(max_retries)
            
            retried = 0
            successful = 0
            
            for notification in failed_notifications:
                if not notification.can_retry():
                    continue
                
                # Calculate delay based on attempt number (exponential backoff)
                delay_minutes = min(2 ** notification.delivery_attempts, 60)  # Max 60 minutes
                
                # Check if enough time has passed
                if notification.last_retry_at:
                    time_since_last = datetime.now(timezone.utc) - notification.last_retry_at
                    if time_since_last.total_seconds() < delay_minutes * 60:
                        continue  # Not time to retry yet
                
                # Retry sending
                preference = self.preference_repo.get_by_user_id(notification.user_id)
                if not preference:
                    preference = self.preference_repo.get_or_create(notification.user_id)
                
                result = self._send_via_channel(
                    notification,
                    preference,
                    notification.title,
                    notification.message,
                    notification.priority,
                    notification.html_content
                )
                
                retried += 1
                if result.get('success'):
                    successful += 1
            
            return self.format_response(
                success=True,
                data={
                    'retried': retried,
                    'successful': successful,
                    'failed': retried - successful
                },
                message=f"Retried {retried} notifications, {successful} successful"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'retry_failed_notifications')
    
    # ============================================
    # Helper Methods
    # ============================================
    
    def _determine_channels(
        self,
        preference: NotificationPreference,
        priority: NotificationPriority,
        notification_type: NotificationType
    ) -> List[str]:
        """Determine which channels to use based on preferences"""
        channels = []
        
        # Check each channel
        for channel_str in ['email', 'sms', 'push', 'slack', 'teams', 'webhook', 'phone']:
            if preference.is_channel_enabled(channel_str, priority.value):
                channels.append(channel_str)
        
        # Always include in_app if no channels found
        if not channels:
            channels.append('in_app')
        
        return channels
    
    def _string_to_channel(self, channel_str: str) -> Optional[NotificationChannel]:
        """Convert string to NotificationChannel enum"""
        mapping = {
            'email': NotificationChannel.EMAIL,
            'sms': NotificationChannel.SMS,
            'push': NotificationChannel.PUSH,
            'in_app': NotificationChannel.IN_APP,
            'slack': NotificationChannel.SLACK,
            'teams': NotificationChannel.TEAMS,
            'webhook': NotificationChannel.WEBHOOK,
            'phone': NotificationChannel.PHONE
        }
        return mapping.get(channel_str.lower())
    
    def _priority_to_infra(self, priority: NotificationPriority):
        """Convert NotificationPriority to infrastructure priority"""
        mapping = {
            NotificationPriority.LOW: InfraPriority.LOW,
            NotificationPriority.NORMAL: InfraPriority.NORMAL,
            NotificationPriority.HIGH: InfraPriority.HIGH,
            NotificationPriority.URGENT: InfraPriority.URGENT
        }
        return mapping.get(priority, InfraPriority.NORMAL)
    
    def _get_user_email(self, user_id: int) -> Optional[str]:
        """Get user email address"""
        try:
            user = self.user_repo.get_by_id(user_id)
            return user.email if user else None
        except:
            return None
    
    def _get_user_phone(self, user_id: int) -> Optional[str]:
        """Get user phone number"""
        try:
            user = self.user_repo.get_by_id(user_id)
            return user.phone if user else None
        except:
            return None
    
    # ============================================
    # User Notification Methods
    # ============================================
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Get notifications for a user"""
        try:
            notifications = self.notification_repo.get_user_notifications(
                user_id, limit, unread_only
            )
            
            return self.format_response(
                success=True,
                data=[n.to_dict() for n in notifications],
                message=f"Retrieved {len(notifications)} notifications"
            )
        except Exception as e:
            return self.handle_exception(e, 'get_user_notifications')
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            success = self.notification_repo.mark_as_read(notification_id, user_id)
            if success:
                return self.format_response(
                    success=True,
                    message="Notification marked as read"
                )
            else:
                return self.format_response(
                    success=False,
                    message="Notification not found or already read"
                )
        except Exception as e:
            return self.handle_exception(e, 'mark_notification_read')
    
    def mark_all_read(self, user_id: int) -> Dict[str, Any]:
        """Mark all notifications as read"""
        try:
            count = self.notification_repo.mark_all_as_read(user_id)
            return self.format_response(
                success=True,
                data={'count': count},
                message=f"Marked {count} notifications as read"
            )
        except Exception as e:
            return self.handle_exception(e, 'mark_all_read')
    
    def get_unread_count(self, user_id: int) -> Dict[str, Any]:
        """Get unread notification count"""
        try:
            count = self.notification_repo.get_unread_count(user_id)
            return self.format_response(
                success=True,
                data={'count': count},
                message=f"User has {count} unread notifications"
            )
        except Exception as e:
            return self.handle_exception(e, 'get_unread_count')


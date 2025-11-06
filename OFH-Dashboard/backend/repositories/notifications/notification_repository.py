#!/usr/bin/env python3
"""
Notification Repository
Handles database operations for notifications
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta, timezone
from repositories.base_repository import BaseRepository
from models.notifications.notification import (
    Notification, NotificationStatus, NotificationChannel, 
    NotificationPriority, NotificationType
)
import logging

logger = logging.getLogger(__name__)

class NotificationRepository(BaseRepository):
    """Repository for Notification model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Notification)
    
    def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 50, 
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        priority: Optional[NotificationPriority] = None
    ) -> List[Notification]:
        """Get notifications for a user"""
        try:
            query = self.db.query(Notification).filter(Notification.user_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            if notification_type:
                query = query.filter(Notification.notification_type == notification_type)
            
            if priority:
                query = query.filter(Notification.priority == priority)
            
            return query.order_by(desc(Notification.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            raise
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        try:
            return self.db.query(func.count(Notification.id)).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).scalar() or 0
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            raise
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.mark_as_read()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification as read: {e}")
            raise
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        try:
            count = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).update({'is_read': True, 'read_at': datetime.now(timezone.utc)})
            
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking all notifications as read: {e}")
            raise
    
    def mark_as_acknowledged(self, notification_id: int, user_id: int, acknowledged_by: str = None) -> bool:
        """Mark notification as acknowledged"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.mark_as_acknowledged(acknowledged_by)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking notification as acknowledged: {e}")
            raise
    
    def get_pending_notifications(self, limit: int = 100) -> List[Notification]:
        """Get pending notifications that need to be sent"""
        try:
            return self.db.query(Notification).filter(
                Notification.status == NotificationStatus.PENDING,
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.now(timezone.utc)
                )
            ).order_by(asc(Notification.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}")
            raise
    
    def get_failed_notifications(self, limit: int = 100) -> List[Notification]:
        """Get failed notifications that can be retried"""
        try:
            return self.db.query(Notification).filter(
                Notification.status == NotificationStatus.FAILED,
                Notification.delivery_attempts < Notification.max_retries
            ).order_by(asc(Notification.last_retry_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting failed notifications: {e}")
            raise
    
    def update_delivery_status(
        self, 
        notification_id: int, 
        status: NotificationStatus,
        failure_reason: Optional[str] = None
    ) -> bool:
        """Update notification delivery status"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if notification:
                notification.status = status
                notification.delivery_attempts += 1
                notification.last_retry_at = datetime.now(timezone.utc)
                
                if status == NotificationStatus.SENT:
                    notification.sent_at = datetime.now(timezone.utc)
                elif status == NotificationStatus.DELIVERED:
                    notification.delivered_at = datetime.now(timezone.utc)
                elif status == NotificationStatus.FAILED:
                    notification.failure_reason = failure_reason
                
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating delivery status: {e}")
            raise
    
    def get_notification_statistics(
        self, 
        user_id: Optional[int] = None,
        time_range: str = '24h'
    ) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            # Parse time range
            hours = self._parse_time_range_to_hours(time_range)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = self.db.query(Notification).filter(
                Notification.created_at >= cutoff_time
            )
            
            if user_id:
                query = query.filter(Notification.user_id == user_id)
            
            notifications = query.all()
            
            total = len(notifications)
            by_status = {}
            by_channel = {}
            by_type = {}
            by_priority = {}
            
            for notif in notifications:
                # Count by status
                status = notif.status.value if notif.status else 'unknown'
                by_status[status] = by_status.get(status, 0) + 1
                
                # Count by channel
                channel = notif.channel.value if notif.channel else 'unknown'
                by_channel[channel] = by_channel.get(channel, 0) + 1
                
                # Count by type
                n_type = notif.notification_type.value if notif.notification_type else 'unknown'
                by_type[n_type] = by_type.get(n_type, 0) + 1
                
                # Count by priority
                priority = notif.priority.value if notif.priority else 'unknown'
                by_priority[priority] = by_priority.get(priority, 0) + 1
            
            sent = by_status.get('sent', 0) + by_status.get('delivered', 0) + by_status.get('read', 0)
            failed = by_status.get('failed', 0)
            success_rate = (sent / total * 100) if total > 0 else 0
            
            return {
                'total_notifications': total,
                'by_status': by_status,
                'by_channel': by_channel,
                'by_type': by_type,
                'by_priority': by_priority,
                'success_rate': round(success_rate, 2),
                'sent_count': sent,
                'failed_count': failed,
                'time_range': time_range
            }
        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            raise
    
    def get_notifications_by_alert(self, alert_id: str) -> List[Notification]:
        """Get all notifications related to an alert"""
        try:
            return self.db.query(Notification).filter(
                Notification.alert_id == alert_id
            ).order_by(desc(Notification.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting notifications by alert: {e}")
            raise
    
    def get_notifications_by_conversation(self, conversation_id: str) -> List[Notification]:
        """Get all notifications related to a conversation"""
        try:
            return self.db.query(Notification).filter(
                Notification.conversation_id == conversation_id
            ).order_by(desc(Notification.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting notifications by conversation: {e}")
            raise
    
    def delete_old_notifications(self, days: int = 90) -> int:
        """Delete notifications older than specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            count = self.db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting old notifications: {e}")
            raise
    
    def _parse_time_range_to_hours(self, time_range: str) -> int:
        """Parse time range string to hours"""
        if time_range == '1h':
            return 1
        elif time_range in ['24h', '1d']:
            return 24
        elif time_range == '7d':
            return 24 * 7
        elif time_range == '30d':
            return 24 * 30
        elif time_range == '90d':
            return 24 * 90
        else:
            return 24  # Default to 24 hours


#!/usr/bin/env python3
"""
Notification Digest Service
Batches multiple notifications into digest notifications
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from services.base_service import BaseService
from repositories.notifications.notification_repository import NotificationRepository
from repositories.notifications.notification_preference_repository import NotificationPreferenceRepository
from repositories.user_repository import UserRepository
from models.notifications.notification import Notification, NotificationStatus, NotificationChannel, NotificationPriority, NotificationType
from models.notifications.notification_preference import NotificationPreference
from services.notifications.enhanced_notification_service import EnhancedNotificationService
import logging
import uuid

logger = logging.getLogger(__name__)


class NotificationDigestService(BaseService):
    """Service for digest notifications"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.notification_repo = NotificationRepository(self.get_session())
        self.preference_repo = NotificationPreferenceRepository(self.get_session())
        self.user_repo = UserRepository(self.get_session())
        self.notification_service = EnhancedNotificationService(self.get_session())
    
    def create_digest_notification(
        self,
        user_id: int,
        notification_ids: List[int],
        digest_frequency: str = 'daily'
    ) -> Dict[str, Any]:
        """Create a digest notification from multiple notifications"""
        try:
            # Get all notifications
            notifications = []
            for notif_id in notification_ids:
                notif = self.notification_repo.get_by_id(notif_id)
                if notif and notif.user_id == user_id:
                    notifications.append(notif)
            
            if not notifications:
                return self.format_response(
                    success=False,
                    message="No notifications found for digest"
                )
            
            # Group by type and priority
            grouped = self._group_notifications(notifications)
            
            # Create digest content
            digest_id = str(uuid.uuid4())
            title, message, html_content = self._format_digest(grouped, digest_frequency)
            
            # Determine priority (highest priority from notifications)
            max_priority = max(
                (n.priority for n in notifications if n.priority),
                key=lambda p: ['low', 'normal', 'high', 'urgent'].index(p.value) if p else 0
            ) if notifications else NotificationPriority.NORMAL
            
            # Create digest notification
            digest_notification = self.notification_service.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=NotificationType.SYSTEM,
                priority=max_priority,
                channel=NotificationChannel.EMAIL,  # Digests are typically email
                notification_metadata={
                    'digest_id': digest_id,
                    'digest_frequency': digest_frequency,
                    'notification_count': len(notifications),
                    'notification_ids': notification_ids,
                    'grouped_data': grouped
                },
                html_content=html_content
            )
            
            # Mark original notifications as part of digest
            for notif in notifications:
                notif.digest_id = digest_id
                notif.status = NotificationStatus.SENT  # Mark as sent via digest
            
            self.notification_repo.db.commit()
            
            # Send the digest
            preference = self.preference_repo.get_or_create(user_id)
            send_result = self.notification_service._send_via_channel(
                digest_notification,
                preference,
                title,
                message,
                max_priority,
                html_content
            )
            
            return self.format_response(
                success=True,
                data={
                    'digest_id': digest_id,
                    'digest_notification_id': digest_notification.id,
                    'notification_count': len(notifications),
                    'send_status': send_result.get('status')
                },
                message=f"Digest created with {len(notifications)} notifications"
            )
            
        except Exception as e:
            self.notification_repo.db.rollback()
            return self.handle_exception(e, 'create_digest_notification')
    
    def process_digest_queue(self) -> Dict[str, Any]:
        """Process all users with digest enabled and create digests"""
        try:
            # Get all users with digest enabled
            session = self.get_session()
            from models.user import User
            from models.notifications.notification_preference import NotificationPreference
            
            users_with_digest = session.query(User).join(
                NotificationPreference
            ).filter(
                NotificationPreference.digest_enabled == True,
                User.is_active == True,
                User.is_deleted.is_(False)
            ).all()
            
            processed = 0
            created = 0
            
            for user in users_with_digest:
                preference = self.preference_repo.get_by_user_id(user.id)
                if not preference or not preference.digest_enabled:
                    continue
                
                # Get pending notifications for digest
                pending_notifications = self._get_pending_digest_notifications(
                    user.id,
                    preference
                )
                
                if pending_notifications:
                    result = self.create_digest_notification(
                        user.id,
                        [n.id for n in pending_notifications],
                        preference.digest_frequency
                    )
                    
                    processed += 1
                    if result.get('success'):
                        created += 1
            
            return self.format_response(
                success=True,
                data={
                    'users_processed': processed,
                    'digests_created': created
                },
                message=f"Processed {processed} users, created {created} digests"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'process_digest_queue')
    
    def _get_pending_digest_notifications(
        self,
        user_id: int,
        preference: NotificationPreference
    ) -> List[Notification]:
        """Get notifications that should be included in digest"""
        try:
            # Determine time window based on frequency
            now = datetime.now(timezone.utc)
            
            if preference.digest_frequency == 'hourly':
                window_start = now - timedelta(hours=1)
            elif preference.digest_frequency == 'daily':
                window_start = now - timedelta(days=1)
            elif preference.digest_frequency == 'weekly':
                window_start = now - timedelta(days=7)
            else:
                window_start = now - timedelta(days=1)  # Default to daily
            
            # Get notifications that:
            # - Are for this user
            # - Are not already in a digest
            # - Are not urgent (urgent notifications are sent immediately)
            # - Were created in the time window
            notifications = self.notification_repo.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.digest_id.is_(None),
                Notification.priority != NotificationPriority.URGENT,
                Notification.created_at >= window_start,
                Notification.status == NotificationStatus.PENDING
            ).order_by(Notification.created_at).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting pending digest notifications: {e}")
            return []
    
    def _group_notifications(self, notifications: List[Notification]) -> Dict[str, Any]:
        """Group notifications by type and priority"""
        grouped = {}
        
        for notif in notifications:
            n_type = notif.notification_type.value if notif.notification_type else 'unknown'
            priority = notif.priority.value if notif.priority else 'normal'
            
            if n_type not in grouped:
                grouped[n_type] = {}
            
            if priority not in grouped[n_type]:
                grouped[n_type][priority] = []
            
            grouped[n_type][priority].append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'created_at': notif.created_at.isoformat() if notif.created_at else None
            })
        
        return grouped
    
    def _format_digest(self, grouped: Dict[str, Any], frequency: str) -> tuple:
        """Format digest into title, message, and HTML"""
        total_count = sum(
            len(notifs)
            for type_group in grouped.values()
            for notifs in type_group.values()
        )
        
        title = f"Notification Digest - {total_count} notification(s)"
        
        # Create text message
        message_lines = [f"You have {total_count} notification(s) in your digest:\n"]
        
        for n_type, priorities in grouped.items():
            message_lines.append(f"\n{n_type.upper()}:")
            for priority, notifs in priorities.items():
                message_lines.append(f"  {priority.upper()}: {len(notifs)} notification(s)")
                for notif in notifs[:5]:  # Show first 5
                    message_lines.append(f"    - {notif['title']}")
                if len(notifs) > 5:
                    message_lines.append(f"    ... and {len(notifs) - 5} more")
        
        message = "\n".join(message_lines)
        
        # Create HTML content
        html_content = self._format_html_digest(grouped, total_count, frequency)
        
        return title, message, html_content
    
    def _format_html_digest(
        self,
        grouped: Dict[str, Any],
        total_count: int,
        frequency: str
    ) -> str:
        """Format digest as HTML email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .notification-group {{ margin-bottom: 20px; border-left: 4px solid #3b82f6; padding-left: 15px; }}
                .notification-item {{ background-color: #f9fafb; padding: 10px; margin: 5px 0; border-radius: 4px; }}
                .priority-high {{ border-left-color: #ef4444; }}
                .priority-normal {{ border-left-color: #3b82f6; }}
                .priority-low {{ border-left-color: #10b981; }}
                .footer {{ text-align: center; color: #6b7280; padding: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Notification Digest</h1>
                <p>{total_count} notification(s)</p>
            </div>
            <div class="content">
        """
        
        for n_type, priorities in grouped.items():
            html += f'<div class="notification-group"><h2>{n_type.upper()}</h2>'
            
            for priority, notifs in priorities.items():
                priority_class = f"priority-{priority}"
                html += f'<div class="{priority_class}"><h3>{priority.upper()} ({len(notifs)})</h3>'
                
                for notif in notifs:
                    html += f"""
                    <div class="notification-item">
                        <strong>{notif['title']}</strong>
                        <p>{notif['message']}</p>
                        <small>{notif['created_at']}</small>
                    </div>
                    """
                
                html += '</div>'
            
            html += '</div>'
        
        html += """
            </div>
            <div class="footer">
                <p>This is an automated digest notification from NINA Guardrail Monitor</p>
            </div>
        </body>
        </html>
        """
        
        return html


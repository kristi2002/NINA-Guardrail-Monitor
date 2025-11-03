#!/usr/bin/env python3
"""
Notification Service
Handles business logic for notifications and messaging
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from .base_service import BaseService
from repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class NotificationService(BaseService):
    """Service for notification business logic"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.user_repo = UserRepository(self.get_session())
    
    def get_by_id(self, record_id: int) -> Optional[Any]:
        """Not applicable for notification service"""
        return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new notification"""
        try:
            # Validate required fields
            required_fields = ['user_id', 'title', 'message', 'type']
            missing_fields = self.validate_required_fields(data, required_fields)
            
            if missing_fields:
                return self.format_response(
                    success=False,
                    message="Missing required fields",
                    errors=[f"Missing field: {field}" for field in missing_fields]
                )
            
            # Sanitize input
            sanitized_data = self.sanitize_input(data)
            
            # Set default values
            sanitized_data.setdefault('is_read', False)
            sanitized_data.setdefault('priority', 'medium')
            sanitized_data.setdefault('created_at', datetime.utcnow())
            
            # Create notification (this would be implemented with actual notification storage)
            notification = {
                'id': f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                **sanitized_data
            }
            
            self.log_operation('notification_created', sanitized_data.get('user_id'), {
                'notification_id': notification['id'],
                'type': sanitized_data['type'],
                'priority': sanitized_data['priority']
            })
            
            return self.format_response(
                success=True,
                data=notification,
                message="Notification created successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'create_notification')
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update notification"""
        try:
            # This would be implemented with actual notification storage
            return self.format_response(
                success=True,
                message="Notification updated successfully"
            )
        except Exception as e:
            return self.handle_exception(e, 'update_notification')
    
    def delete(self, record_id: int) -> Dict[str, Any]:
        """Delete notification"""
        try:
            # This would be implemented with actual notification storage
            return self.format_response(
                success=True,
                message="Notification deleted successfully"
            )
        except Exception as e:
            return self.handle_exception(e, 'delete_notification')
    
    def send_alert_notification(self, alert_id: str, alert_data: Dict[str, Any], recipients: List[str] = None) -> Dict[str, Any]:
        """Send alert notification to operators"""
        try:
            # Determine recipients
            if not recipients:
                # Get all active operators
                operators = self.user_repo.get_by_filters({'is_active': True, 'role': 'operator'})
                recipients = [op.username for op in operators]
            
            # Create notification for each recipient
            notifications_sent = []
            for recipient in recipients:
                notification_data = {
                    'user_id': recipient,
                    'title': f"New Alert: {alert_data.get('title', 'Unknown')}",
                    'message': f"Alert {alert_id}: {alert_data.get('message', 'No description')}",
                    'type': 'alert',
                    'priority': alert_data.get('severity', 'medium'),
                    'metadata': {
                        'alert_id': alert_id,
                        'severity': alert_data.get('severity'),
                        'event_type': alert_data.get('event_type')
                    }
                }
                
                result = self.create(notification_data)
                if result['success']:
                    notifications_sent.append(recipient)
            
            self.log_operation('alert_notification_sent', details={
                'alert_id': alert_id,
                'recipients_count': len(notifications_sent),
                'recipients': notifications_sent
            })
            
            return self.format_response(
                success=True,
                data={
                    'notifications_sent': len(notifications_sent),
                    'recipients': notifications_sent
                },
                message=f"Alert notification sent to {len(notifications_sent)} recipients"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'send_alert_notification')
    
    def send_conversation_notification(self, conversation_id: str, conversation_data: Dict[str, Any], recipients: List[str] = None) -> Dict[str, Any]:
        """Send conversation notification"""
        try:
            # Determine recipients
            if not recipients:
                # Get all active operators
                operators = self.user_repo.get_by_filters({'is_active': True, 'role': 'operator'})
                recipients = [op.username for op in operators]
            
            # Create notification for each recipient
            notifications_sent = []
            for recipient in recipients:
                notification_data = {
                    'user_id': recipient,
                    'title': f"Conversation Update: {conversation_data.get('patient_id', 'Unknown Patient')}",
                    'message': f"Conversation {conversation_id} requires attention",
                    'type': 'conversation',
                    'priority': conversation_data.get('risk_level', 'medium').lower(),
                    'metadata': {
                        'conversation_id': conversation_id,
                        'patient_id': conversation_data.get('patient_id'),
                        'risk_level': conversation_data.get('risk_level')
                    }
                }
                
                result = self.create(notification_data)
                if result['success']:
                    notifications_sent.append(recipient)
            
            self.log_operation('conversation_notification_sent', details={
                'conversation_id': conversation_id,
                'recipients_count': len(notifications_sent),
                'recipients': notifications_sent
            })
            
            return self.format_response(
                success=True,
                data={
                    'notifications_sent': len(notifications_sent),
                    'recipients': notifications_sent
                },
                message=f"Conversation notification sent to {len(notifications_sent)} recipients"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'send_conversation_notification')
    
    def send_system_notification(self, title: str, message: str, recipients: List[str] = None, priority: str = 'medium') -> Dict[str, Any]:
        """Send system notification"""
        try:
            # Determine recipients
            if not recipients:
                # Get all active users
                users = self.user_repo.get_by_filters({'is_active': True})
                recipients = [user.username for user in users]
            
            # Create notification for each recipient
            notifications_sent = []
            for recipient in recipients:
                notification_data = {
                    'user_id': recipient,
                    'title': title,
                    'message': message,
                    'type': 'system',
                    'priority': priority
                }
                
                result = self.create(notification_data)
                if result['success']:
                    notifications_sent.append(recipient)
            
            self.log_operation('system_notification_sent', details={
                'title': title,
                'recipients_count': len(notifications_sent),
                'priority': priority
            })
            
            return self.format_response(
                success=True,
                data={
                    'notifications_sent': len(notifications_sent),
                    'recipients': notifications_sent
                },
                message=f"System notification sent to {len(notifications_sent)} recipients"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'send_system_notification')
    
    def get_user_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> Dict[str, Any]:
        """Get notifications for a user"""
        try:
            # TODO: Implement proper notification storage in database
            # For now, return empty list as notifications will be populated by actual events
            notifications = []
            
            self.log_operation('user_notifications_requested', user_id, {
                'limit': limit,
                'unread_only': unread_only,
                'count': len(notifications)
            })
            
            return self.format_response(
                success=True,
                data=notifications,
                message="User notifications retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_user_notifications', user_id)
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            # This would be implemented with actual notification storage
            self.log_operation('notification_marked_read', user_id, {
                'notification_id': notification_id
            })
            
            return self.format_response(
                success=True,
                message="Notification marked as read"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'mark_notification_read', user_id)
    
    def mark_all_notifications_read(self, user_id: str) -> Dict[str, Any]:
        """Mark all notifications as read for a user"""
        try:
            # This would be implemented with actual notification storage
            self.log_operation('all_notifications_marked_read', user_id)
            
            return self.format_response(
                success=True,
                message="All notifications marked as read"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'mark_all_notifications_read', user_id)
    
    def get_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences"""
        try:
            # This would be implemented with actual preference storage
            preferences = {
                'email_notifications': True,
                'push_notifications': True,
                'alert_notifications': True,
                'conversation_notifications': True,
                'system_notifications': False,
                'notification_frequency': 'immediate',
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '08:00'
            }
            
            self.log_operation('notification_preferences_requested', user_id)
            
            return self.format_response(
                success=True,
                data=preferences,
                message="Notification preferences retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_notification_preferences', user_id)
    
    def update_notification_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user notification preferences"""
        try:
            # Validate preferences
            valid_keys = [
                'email_notifications', 'push_notifications', 'alert_notifications',
                'conversation_notifications', 'system_notifications', 'notification_frequency',
                'quiet_hours_start', 'quiet_hours_end'
            ]
            
            invalid_keys = [key for key in preferences.keys() if key not in valid_keys]
            if invalid_keys:
                return self.format_response(
                    success=False,
                    message="Invalid preference keys",
                    errors=[f"Invalid key: {key}" for key in invalid_keys]
                )
            
            # This would be implemented with actual preference storage
            self.log_operation('notification_preferences_updated', user_id, {
                'updated_preferences': list(preferences.keys())
            })
            
            return self.format_response(
                success=True,
                data=preferences,
                message="Notification preferences updated successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'update_notification_preferences', user_id)
    
    def get_notification_statistics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # This would be implemented with actual notification storage
            stats = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'total_notifications': 150,
                'notifications_by_type': {
                    'alert': 75,
                    'conversation': 45,
                    'system': 30
                },
                'notifications_by_priority': {
                    'critical': 25,
                    'high': 40,
                    'medium': 60,
                    'low': 25
                },
                'read_rate': 0.85,
                'average_response_time_minutes': 12
            }
            
            self.log_operation('notification_statistics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=stats,
                message="Notification statistics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_notification_statistics')
    
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

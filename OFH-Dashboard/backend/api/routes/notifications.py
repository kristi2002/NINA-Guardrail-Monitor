#!/usr/bin/env python3
"""
Notifications Routes
Handles notification statistics and management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from api.middleware.auth_middleware import token_required, get_current_user
from services.notification_infrastructure_service import NotificationService, NotificationPriority, NotificationType
from core.config_helper import ConfigHelper

logger = logging.getLogger(__name__)

# Create Blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/stats', methods=['GET'])
@token_required
def get_notification_stats():
    """Get notification statistics"""
    try:
        time_range = request.args.get('range', '24h')
        current_user = get_current_user()
        
        logger.info(f"Notification stats requested by {current_user} for range: {time_range}")
        
        # Mock notification stats data
        stats_data = {
            'total_notifications': 342,
            'by_type': {
                'email': 156,
                'sms': 89,
                'push': 97
            },
            'by_status': {
                'sent': 298,
                'failed': 12,
                'pending': 32
            },
            'success_rate': 87.1,
            'trends': [
                {'hour': '00:00', 'email': 5, 'sms': 2, 'push': 3},
                {'hour': '01:00', 'email': 3, 'sms': 1, 'push': 2},
                {'hour': '02:00', 'email': 2, 'sms': 0, 'push': 1},
                {'hour': '03:00', 'email': 1, 'sms': 1, 'push': 1},
                {'hour': '04:00', 'email': 2, 'sms': 0, 'push': 1},
                {'hour': '05:00', 'email': 3, 'sms': 1, 'push': 2},
                {'hour': '06:00', 'email': 8, 'sms': 3, 'push': 4},
                {'hour': '07:00', 'email': 12, 'sms': 5, 'push': 6},
                {'hour': '08:00', 'email': 18, 'sms': 8, 'push': 9},
                {'hour': '09:00', 'email': 22, 'sms': 10, 'push': 12},
                {'hour': '10:00', 'email': 20, 'sms': 9, 'push': 11},
                {'hour': '11:00', 'email': 18, 'sms': 8, 'push': 10},
                {'hour': '12:00', 'email': 15, 'sms': 6, 'push': 8},
                {'hour': '13:00', 'email': 16, 'sms': 7, 'push': 9},
                {'hour': '14:00', 'email': 19, 'sms': 8, 'push': 10},
                {'hour': '15:00', 'email': 21, 'sms': 9, 'push': 11},
                {'hour': '16:00', 'email': 20, 'sms': 8, 'push': 10},
                {'hour': '17:00', 'email': 18, 'sms': 7, 'push': 9},
                {'hour': '18:00', 'email': 15, 'sms': 6, 'push': 8},
                {'hour': '19:00', 'email': 12, 'sms': 5, 'push': 6},
                {'hour': '20:00', 'email': 8, 'sms': 3, 'push': 4},
                {'hour': '21:00', 'email': 6, 'sms': 2, 'push': 3},
                {'hour': '22:00', 'email': 4, 'sms': 1, 'push': 2},
                {'hour': '23:00', 'email': 3, 'sms': 1, 'push': 2}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': stats_data
        })
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get notification stats',
            'message': str(e)
        }), 500

@notifications_bp.route('/preferences', methods=['GET'])
@token_required
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Notification preferences requested by {current_user}")
        
        # Mock notification preferences data
        preferences_data = {
            'email_notifications': True,
            'push_notifications': True,
            'alert_notifications': True,
            'conversation_notifications': True,
            'system_notifications': False,
            'notification_frequency': 'immediate',  # immediate, hourly, daily
            'quiet_hours': {
                'enabled': True,
                'start': '22:00',
                'end': '08:00'
            },
            'channels': {
                'email': {
                    'enabled': True,
                    'address': 'user@example.com'
                },
                'sms': {
                    'enabled': False,
                    'number': '+1234567890'
                },
                'push': {
                    'enabled': True,
                    'device_token': 'device_token_123'
                }
            },
            'alert_types': {
                'critical_alerts': True,
                'warning_alerts': True,
                'info_alerts': False,
                'security_alerts': True,
                'system_alerts': False
            },
            'escalation_notifications': True,
            'digest_notifications': False,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': preferences_data
        })
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get notification preferences',
            'message': str(e)
        }), 500

@notifications_bp.route('/preferences', methods=['PUT'])
@token_required
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        logger.info(f"Notification preferences updated by {current_user}")
        
        # In a real application, you would save these preferences to a database
        # For now, we'll just return a success response
        
        return jsonify({
            'success': True,
            'message': 'Notification preferences updated successfully',
            'data': {
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update notification preferences',
            'message': str(e)
        }), 500

@notifications_bp.route('/email', methods=['POST'])
@token_required
def send_email_notification():
    """Send email notification"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        logger.info(f"Email notification requested by {current_user}")
        
        # Check if email is configured
        if not ConfigHelper.is_email_configured():
            return jsonify({
                'success': False,
                'error': 'Email service not configured',
                'message': 'Please configure EMAIL_ENABLED and SMTP credentials in .env file'
            }), 400
        
        # Get email parameters
        to_emails = data.get('to', [])
        if isinstance(to_emails, str):
            to_emails = [to_emails]
        
        subject = data.get('subject', 'OFH Dashboard Notification')
        body = data.get('body', '')
        html_body = data.get('html_body')
        priority_str = data.get('priority', 'normal').upper()
        
        # Map priority string to enum
        priority_map = {
            'LOW': NotificationPriority.LOW,
            'NORMAL': NotificationPriority.NORMAL,
            'HIGH': NotificationPriority.HIGH,
            'URGENT': NotificationPriority.URGENT
        }
        priority = priority_map.get(priority_str, NotificationPriority.NORMAL)
        
        # Send email
        notification_service = NotificationService()
        success = notification_service.send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            priority=priority,
            html_body=html_body
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email notification sent successfully',
                'data': {
                    'message_id': f'email_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'recipients': to_emails,
                    'sent_at': datetime.now().isoformat(),
                    'priority': priority_str
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send email notification',
                'message': 'Check server logs for details'
            }), 500
        
    except Exception as e:
        logger.error(f"Error sending email notification: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to send email notification',
            'message': str(e)
        }), 500

@notifications_bp.route('/sms', methods=['POST'])
@token_required
def send_sms_notification():
    """Send SMS notification"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        logger.info(f"SMS notification requested by {current_user}")
        
        # Mock SMS sending
        return jsonify({
            'success': True,
            'message': 'SMS notification sent successfully',
            'data': {
                'message_id': f'sms_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'recipient': data.get('to', 'unknown'),
                'sent_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending SMS notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send SMS notification',
            'message': str(e)
        }), 500

@notifications_bp.route('/webhook', methods=['POST'])
@token_required
def send_webhook_notification():
    """Send webhook notification"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        logger.info(f"Webhook notification requested by {current_user}")
        
        # Mock webhook sending
        return jsonify({
            'success': True,
            'message': 'Webhook notification sent successfully',
            'data': {
                'message_id': f'webhook_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'url': data.get('url', 'unknown'),
                'sent_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending webhook notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send webhook notification',
            'message': str(e)
        }), 500

@notifications_bp.route('/status/<message_id>', methods=['GET'])
@token_required
def get_notification_status(message_id):
    """Get notification delivery status"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Notification status requested by {current_user} for message {message_id}")
        
        # Mock status data
        status_data = {
            'message_id': message_id,
            'status': 'delivered',
            'delivered_at': datetime.now().isoformat(),
            'delivery_attempts': 1,
            'error_message': None
        }
        
        return jsonify({
            'success': True,
            'data': status_data
        })
        
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get notification status',
            'message': str(e)
        }), 500

@notifications_bp.route('/templates', methods=['GET'])
@token_required
def get_notification_templates():
    """Get notification templates"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Notification templates requested by {current_user}")
        
        # Mock templates data
        templates_data = [
            {
                'id': 'template_1',
                'name': 'Alert Notification',
                'type': 'email',
                'subject': 'Security Alert: {alert_type}',
                'body': 'A {severity} security alert has been detected: {description}',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'template_2',
                'name': 'Escalation Notice',
                'type': 'sms',
                'subject': None,
                'body': 'Alert escalated: {alert_id} requires immediate attention',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        return jsonify({
            'success': True,
            'data': templates_data
        })
        
    except Exception as e:
        logger.error(f"Error getting notification templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get notification templates',
            'message': str(e)
        }), 500

@notifications_bp.route('/templates', methods=['POST'])
@token_required
def create_notification_template():
    """Create notification template"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        logger.info(f"Notification template creation requested by {current_user}")
        
        # Mock template creation
        template_data = {
            'id': f'template_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'name': data.get('name', 'New Template'),
            'type': data.get('type', 'email'),
            'subject': data.get('subject'),
            'body': data.get('body', ''),
            'created_at': datetime.now().isoformat(),
            'created_by': current_user
        }
        
        return jsonify({
            'success': True,
            'message': 'Template created successfully',
            'data': template_data
        })
        
    except Exception as e:
        logger.error(f"Error creating notification template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create notification template',
            'message': str(e)
        }), 500

@notifications_bp.route('/templates/<template_id>', methods=['PUT'])
@token_required
def update_notification_template(template_id):
    """Update notification template"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        logger.info(f"Notification template update requested by {current_user} for template {template_id}")
        
        # Mock template update
        return jsonify({
            'success': True,
            'message': 'Template updated successfully',
            'data': {
                'template_id': template_id,
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating notification template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update notification template',
            'message': str(e)
        }), 500

@notifications_bp.route('/templates/<template_id>', methods=['DELETE'])
@token_required
def delete_notification_template(template_id):
    """Delete notification template"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Notification template deletion requested by {current_user} for template {template_id}")
        
        # Mock template deletion
        return jsonify({
            'success': True,
            'message': 'Template deleted successfully',
            'data': {
                'template_id': template_id,
                'deleted_at': datetime.now().isoformat(),
                'deleted_by': current_user
            }
        })
        
    except Exception as e:
        logger.error(f"Error deleting notification template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete notification template',
            'message': str(e)
        }), 500

@notifications_bp.route('/test', methods=['POST'])
@token_required
def test_notification():
    """Test notification delivery"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        logger.info(f"Test notification requested by {current_user}")
        
        # Mock test notification
        return jsonify({
            'success': True,
            'message': 'Test notification sent successfully',
            'data': {
                'test_id': f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'type': data.get('type', 'email'),
                'sent_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send test notification',
            'message': str(e)
        }), 500

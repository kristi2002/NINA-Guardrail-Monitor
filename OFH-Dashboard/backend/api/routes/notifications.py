#!/usr/bin/env python3
"""
Notifications Routes
Handles notification statistics and management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional
from api.middleware.auth_middleware import (
    token_required,
    get_current_user,
    admin_required,
    get_current_user_id,
)
from services.notifications.notification_infrastructure_service import NotificationService, NotificationPriority, NotificationType
from services.notifications.enhanced_notification_service import EnhancedNotificationService
from services.notifications.notification_orchestrator import NotificationOrchestrator
from services.notifications.notification_digest_service import NotificationDigestService
from services.notifications.notification_escalation_service import NotificationEscalationService
from services.notifications.notification_template_service import NotificationTemplateService
from repositories.notifications.notification_repository import NotificationRepository
from repositories.notifications.notification_preference_repository import NotificationPreferenceRepository
from repositories.notifications.notification_group_repository import NotificationGroupRepository
from models.notifications.notification import NotificationStatus, NotificationChannel, NotificationPriority as NotifPriority, NotificationType as NotifType
from core.config_helper import ConfigHelper
from core.database import get_session_context

logger = logging.getLogger(__name__)


def _coerce_bool(value: Any, default: bool = False) -> bool:
    """Best-effort conversion of arbitrary input to bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _coerce_int(value: Any, default: int) -> int:
    """Safely parse int values, falling back to default."""
    try:
        if isinstance(value, bool):
            return int(value)
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _sanitize_frequency(value: Optional[str], default: str = "daily") -> str:
    allowed = {"hourly", "daily", "weekly"}
    if value and value.lower() in allowed:
        return value.lower()
    return default


def _get_flag(pref_dict: Dict[str, Any], *keys: str, default: bool = False) -> bool:
    """Helper to extract boolean flags from channel/type preference dictionaries."""
    if not isinstance(pref_dict, dict):
        return default
    for key in keys:
        if key in pref_dict:
            return _coerce_bool(pref_dict.get(key), default)
    return default


def _serialize_notification_preferences(preference) -> Dict[str, Any]:
    """Convert NotificationPreference model into frontend-friendly structure."""
    channel_prefs = preference.channel_preferences or {}
    type_prefs = preference.type_preferences or {}

    email_pref = channel_prefs.get("email", {})
    sms_pref = channel_prefs.get("sms", {})
    push_pref = channel_prefs.get("push", {})
    webhook_pref = channel_prefs.get("webhook", {})
    escalation_pref = type_prefs.get("escalation", {})

    return {
        "notificationsEnabled": bool(preference.notifications_enabled),
        "email": {
            "enabled": _get_flag(email_pref, "enabled", default=True),
            "critical": _get_flag(email_pref, "critical", default=True),
            "warning": _get_flag(email_pref, "warning", "high", default=True),
            "info": _get_flag(email_pref, "info", "normal", default=False),
            "digest": bool(preference.digest_enabled),
            "digestFrequency": preference.digest_frequency or "daily",
            "address": preference.email_address or email_pref.get("address", ""),
        },
        "sms": {
            "enabled": _get_flag(sms_pref, "enabled", default=False),
            "critical": _get_flag(sms_pref, "critical", default=True),
            "warning": _get_flag(sms_pref, "warning", "high", default=False),
            "info": _get_flag(sms_pref, "info", "normal", default=False),
            "number": preference.phone_number or sms_pref.get("number", ""),
        },
        "push": {
            "enabled": _get_flag(push_pref, "enabled", default=True),
            "critical": _get_flag(push_pref, "critical", default=True),
            "warning": _get_flag(push_pref, "warning", "high", default=True),
            "info": _get_flag(push_pref, "info", "normal", default=True),
            "deviceToken": push_pref.get("device_token", ""),
        },
        "webhook": {
            "enabled": _get_flag(webhook_pref, "enabled", default=False),
            "url": preference.webhook_url or webhook_pref.get("url", ""),
            "critical": _get_flag(webhook_pref, "critical", default=True),
            "warning": _get_flag(webhook_pref, "warning", "high", default=False),
            "info": _get_flag(webhook_pref, "info", "normal", default=False),
            "headers": webhook_pref.get("headers", {}),
        },
        "escalation": {
            "enabled": _coerce_bool(escalation_pref.get("enabled"), default=True),
            "autoEscalate": _coerce_bool(escalation_pref.get("auto_escalate"), default=False),
            "escalationDelay": _coerce_int(escalation_pref.get("delay_minutes"), 15),
            "maxEscalations": _coerce_int(escalation_pref.get("max_escalations"), 3),
        },
        "quietHours": {
            "enabled": bool(preference.quiet_hours_enabled),
            "start": preference.quiet_hours_start or "22:00",
            "end": preference.quiet_hours_end or "08:00",
            "timezone": preference.timezone or "UTC",
        },
        "meta": {
            "updatedAt": preference.updated_at.isoformat() if preference.updated_at else None,
            "createdAt": preference.created_at.isoformat() if preference.created_at else None,
        },
    }


def _build_update_payload(preference, incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Translate frontend payload into model fields for persistence."""
    existing_channels = dict(preference.channel_preferences or {})
    existing_types = dict(preference.type_preferences or {})

    email_in = incoming.get("email", {}) or {}
    sms_in = incoming.get("sms", {}) or {}
    push_in = incoming.get("push", {}) or {}
    webhook_in = incoming.get("webhook", {}) or {}
    escalation_in = incoming.get("escalation", {}) or {}
    quiet_in = incoming.get("quietHours", {}) or {}

    channel_email = dict(existing_channels.get("email", {}))
    channel_email.update(
        {
            "enabled": _coerce_bool(email_in.get("enabled"), channel_email.get("enabled", True)),
            "critical": _coerce_bool(email_in.get("critical"), channel_email.get("critical", True)),
            "high": _coerce_bool(email_in.get("warning"), channel_email.get("high", True)),
            "normal": _coerce_bool(email_in.get("info"), channel_email.get("normal", False)),
            "low": _coerce_bool(email_in.get("low"), channel_email.get("low", False)),
            "address": (email_in.get("address") or "").strip(),
        }
    )

    channel_sms = dict(existing_channels.get("sms", {}))
    channel_sms.update(
        {
            "enabled": _coerce_bool(sms_in.get("enabled"), channel_sms.get("enabled", False)),
            "critical": _coerce_bool(sms_in.get("critical"), channel_sms.get("critical", True)),
            "high": _coerce_bool(sms_in.get("warning"), channel_sms.get("high", False)),
            "normal": _coerce_bool(sms_in.get("info"), channel_sms.get("normal", False)),
            "number": (sms_in.get("number") or "").strip(),
        }
    )

    channel_push = dict(existing_channels.get("push", {}))
    channel_push.update(
        {
            "enabled": _coerce_bool(push_in.get("enabled"), channel_push.get("enabled", True)),
            "critical": _coerce_bool(push_in.get("critical"), channel_push.get("critical", True)),
            "high": _coerce_bool(push_in.get("warning"), channel_push.get("high", True)),
            "normal": _coerce_bool(push_in.get("info"), channel_push.get("normal", True)),
            "device_token": (push_in.get("deviceToken") or "").strip(),
        }
    )

    channel_webhook = dict(existing_channels.get("webhook", {}))
    channel_webhook.update(
        {
            "enabled": _coerce_bool(webhook_in.get("enabled"), channel_webhook.get("enabled", False)),
            "critical": _coerce_bool(webhook_in.get("critical"), channel_webhook.get("critical", True)),
            "high": _coerce_bool(webhook_in.get("warning"), channel_webhook.get("high", False)),
            "normal": _coerce_bool(webhook_in.get("info"), channel_webhook.get("normal", False)),
            "url": (webhook_in.get("url") or "").strip(),
            "headers": webhook_in.get("headers", channel_webhook.get("headers", {})) or {},
        }
    )

    existing_channels["email"] = channel_email
    existing_channels["sms"] = channel_sms
    existing_channels["push"] = channel_push
    existing_channels["webhook"] = channel_webhook

    type_escalation = dict(existing_types.get("escalation", {}))
    type_escalation.update(
        {
            "enabled": _coerce_bool(escalation_in.get("enabled"), type_escalation.get("enabled", True)),
            "auto_escalate": _coerce_bool(
                escalation_in.get("autoEscalate"), type_escalation.get("auto_escalate", False)
            ),
            "delay_minutes": _coerce_int(escalation_in.get("escalationDelay"), type_escalation.get("delay_minutes", 15)),
            "max_escalations": _coerce_int(
                escalation_in.get("maxEscalations"), type_escalation.get("max_escalations", 3)
            ),
        }
    )
    existing_types["escalation"] = type_escalation

    email_address = (email_in.get("address") or "").strip()
    phone_number = (sms_in.get("number") or "").strip()
    webhook_url = (webhook_in.get("url") or "").strip()

    update_dict: Dict[str, Any] = {
        "notifications_enabled": _coerce_bool(
            incoming.get("notificationsEnabled"), getattr(preference, "notifications_enabled", True)
        ),
        "channel_preferences": existing_channels,
        "type_preferences": existing_types,
        "digest_enabled": _coerce_bool(email_in.get("digest"), preference.digest_enabled),
        "digest_frequency": _sanitize_frequency(email_in.get("digestFrequency"), preference.digest_frequency or "daily"),
        "email_address": email_address or None,
        "phone_number": phone_number or None,
        "webhook_url": webhook_url or None,
        "quiet_hours_enabled": _coerce_bool(quiet_in.get("enabled"), preference.quiet_hours_enabled),
        "quiet_hours_start": (quiet_in.get("start") or preference.quiet_hours_start or "22:00")[:5],
        "quiet_hours_end": (quiet_in.get("end") or preference.quiet_hours_end or "08:00")[:5],
        "timezone": (quiet_in.get("timezone") or preference.timezone or "UTC"),
    }

    return update_dict

# Create Blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/history', methods=['GET'])
@token_required
def get_notification_history():
    """Get notification history from guardrail events (alerts)"""
    try:
        current_user = get_current_user()
        limit = request.args.get('limit', 50, type=int)
        
        logger.info(f"Notification history requested by {current_user}, limit: {limit}")
        
        # Get alerts (guardrail events) which serve as notifications
        from services.alert_service import AlertService
        from core.database import get_database_manager
        
        db_manager = get_database_manager()
        session = db_manager.SessionLocal()
        
        try:
            alert_service = AlertService(session)
            alerts = alert_service.get_recent_alerts(hours=168, limit=limit)  # Last 7 days
            
            # Convert GuardrailEvent objects to notification format
            notifications = []
            for alert in alerts:
                # Get attributes from GuardrailEvent model
                event_type = (alert.event_type or 'system_alert').lower()
                severity = (alert.severity or 'info').lower()
                
                # Map severity to priority for frontend
                severity_to_priority = {
                    'critical': 'critical',
                    'high': 'warning',
                    'medium': 'info',
                    'low': 'info',
                    'info': 'info'
                }
                priority = severity_to_priority.get(severity, 'info')
                
                # Map event types to notification types
                notification_type_map = {
                    'alarm_triggered': 'alert',
                    'warning_triggered': 'warning',
                    'privacy_violation_prevented': 'security',
                    'medication_warning': 'warning',
                    'inappropriate_content': 'alert',
                    'emergency_protocol': 'critical',
                    'false_alarm_reported': 'info',
                    'operator_intervention': 'info',
                    'system_alert': 'system',
                    'compliance_check': 'compliance',
                    'context_violation': 'alert',
                    'conversation_started': 'info',
                    'conversation_ended': 'info'
                }
                
                notification_type = notification_type_map.get(event_type, 'system')
                
                # Get message content
                message_content = alert.message_content or alert.description or alert.detected_text or 'A guardrail event occurred'
                
                # Create notification title based on event type
                title_map = {
                    'alarm_triggered': '🚨 Alarm Triggered',
                    'warning_triggered': '⚠️ Warning',
                    'privacy_violation_prevented': '🔒 Privacy Violation Prevented',
                    'medication_warning': '💊 Medication Warning',
                    'inappropriate_content': '🚫 Inappropriate Content',
                    'emergency_protocol': '🚨 Emergency Protocol',
                    'false_alarm_reported': 'ℹ️ False Alarm Reported',
                    'operator_intervention': '👤 Operator Intervention',
                    'system_alert': '📢 System Alert',
                    'compliance_check': '✅ Compliance Check',
                    'context_violation': '⚠️ Context Violation'
                }
                title = title_map.get(event_type, '📢 Guardrail Event')
                
                # Create notification object
                status = (alert.status or '').upper()
                acknowledged = bool(getattr(alert, 'acknowledged_at', None))
                resolved = bool(getattr(alert, 'resolved_at', None))
                is_read = acknowledged or resolved or status in {'ACKNOWLEDGED', 'RESOLVED', 'CLOSED', 'COMPLETED'}

                notification = {
                    'id': f"notif_{alert.id}",
                    'title': title,
                    'message': message_content[:200],  # Truncate long messages
                    'type': notification_type,
                    'priority': priority,  # Frontend expects 'priority', not 'severity'
                    'severity': severity,  # Keep for reference
                    'timestamp': alert.created_at.isoformat() if alert.created_at else datetime.now(timezone.utc).isoformat(),
                    'read': is_read,
                    'acknowledged': acknowledged,
                    'resolved': resolved,
                    'status': status,
                    'conversation_id': alert.conversation_id or alert.session_id,
                    'event_id': alert.event_id,
                    'metadata': {
                        'event_type': event_type,
                        'violations': alert.violations if hasattr(alert, 'violations') and alert.violations else [],
                        'guardrail_rules': alert.guardrail_rules if hasattr(alert, 'guardrail_rules') and alert.guardrail_rules else []
                    }
                }
                notifications.append(notification)
            
            return jsonify({
                'success': True,
                'notifications': notifications,
                'total': len(notifications)
            })
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error getting notification history: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get notification history',
            'message': str(e)
        }), 500

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
        user_id = get_current_user_id()

        if not user_id:
            logger.warning("Notification preferences requested without user context.")
            return jsonify({
                'success': False,
                'error': 'User context missing',
                'message': 'Unable to determine user for notification preferences'
            }), 400
        
        logger.info(f"Notification preferences requested by {current_user} (user_id={user_id})")

        with get_session_context() as session:
            repo = NotificationPreferenceRepository(session)
            preference = repo.get_or_create(user_id)
            preferences_data = _serialize_notification_preferences(preference)
        
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
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not user_id:
            logger.warning("Notification preferences update attempted without user context.")
            return jsonify({
                'success': False,
                'error': 'User context missing',
                'message': 'Unable to determine user for notification preferences'
            }), 400
        
        if not data or not isinstance(data, dict):
            return jsonify({
                'success': False,
                'error': 'Invalid data',
                'message': 'Notification preferences payload is required'
            }), 400
        
        logger.info(f"Notification preferences update requested by {current_user} (user_id={user_id})")
        
        with get_session_context() as session:
            repo = NotificationPreferenceRepository(session)
            preference = repo.get_or_create(user_id)
            update_payload = _build_update_payload(preference, data)
            updated_preference = repo.update_preferences(user_id, update_payload)
            response_data = _serialize_notification_preferences(updated_preference)
        
        return jsonify({
            'success': True,
            'message': 'Notification preferences updated successfully',
            'data': response_data
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

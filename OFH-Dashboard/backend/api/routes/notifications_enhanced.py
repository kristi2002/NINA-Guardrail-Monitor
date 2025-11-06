#!/usr/bin/env python3
"""
Enhanced Notifications Routes
Complete notification API with all features
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
import logging
from api.middleware.auth_middleware import token_required, get_current_user, admin_required
from services.notifications.enhanced_notification_service import EnhancedNotificationService
from services.notifications.notification_orchestrator import NotificationOrchestrator
from services.notifications.notification_digest_service import NotificationDigestService
from services.notifications.notification_escalation_service import NotificationEscalationService
from services.notifications.notification_template_service import NotificationTemplateService
from repositories.notifications.notification_repository import NotificationRepository
from repositories.notifications.notification_preference_repository import NotificationPreferenceRepository
from repositories.notifications.notification_group_repository import NotificationGroupRepository
from repositories.user_repository import UserRepository
from models.notifications.notification import NotificationStatus, NotificationChannel, NotificationPriority, NotificationType
from core.database import get_session_context

logger = logging.getLogger(__name__)

# Create Blueprint
notifications_enhanced_bp = Blueprint('notifications_enhanced', __name__, url_prefix='/api/notifications/v2')

@notifications_enhanced_bp.route('/user/notifications', methods=['GET'])
@token_required
def get_user_notifications():
    """Get user's notifications"""
    try:
        current_user = get_current_user()
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Get user ID from current user
        with get_session_context() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(current_user)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            if user_id and user_id != user.id and not user.is_admin:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            target_user_id = user_id if user_id and user.is_admin else user.id
            
            notification_service = EnhancedNotificationService(session)
            result = notification_service.get_user_notifications(target_user_id, limit, unread_only)
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/user/unread-count', methods=['GET'])
@token_required
def get_unread_count():
    """Get unread notification count"""
    try:
        current_user = get_current_user()
        
        with get_session_context() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(current_user)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            notification_service = EnhancedNotificationService(session)
            result = notification_service.get_unread_count(user.id)
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error getting unread count: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/user/notifications/<int:notification_id>/read', methods=['POST'])
@token_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        current_user = get_current_user()
        
        with get_session_context() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(current_user)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            notification_service = EnhancedNotificationService(session)
            result = notification_service.mark_notification_read(notification_id, user.id)
            
            return jsonify(result), 200 if result.get('success') else 400
            
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/user/notifications/read-all', methods=['POST'])
@token_required
def mark_all_read():
    """Mark all notifications as read"""
    try:
        current_user = get_current_user()
        
        with get_session_context() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(current_user)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            notification_service = EnhancedNotificationService(session)
            result = notification_service.mark_all_read(user.id)
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/preferences', methods=['GET'])
@token_required
def get_preferences():
    """Get user notification preferences"""
    try:
        current_user = get_current_user()
        
        with get_session_context() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(current_user)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            preference_repo = NotificationPreferenceRepository(session)
            preference = preference_repo.get_or_create(user.id)
            
            return jsonify({
                'success': True,
                'data': preference.to_dict()
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting preferences: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/preferences', methods=['PUT'])
@token_required
def update_preferences():
    """Update user notification preferences"""
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        
        with get_session_context() as session:
            user_repo = UserRepository(session)
            user = user_repo.get_by_username(current_user)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            preference_repo = NotificationPreferenceRepository(session)
            preference = preference_repo.update_preferences(user.id, data)
            
            return jsonify({
                'success': True,
                'data': preference.to_dict(),
                'message': 'Preferences updated successfully'
            }), 200
            
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/send', methods=['POST'])
@token_required
@admin_required
def send_notification():
    """Send a notification (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        title = data.get('title')
        message = data.get('message')
        
        if not user_id or not title or not message:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        with get_session_context() as session:
            notification_service = EnhancedNotificationService(session)
            
            priority = NotificationPriority(data.get('priority', 'normal'))
            notification_type = NotificationType(data.get('type', 'system'))
            channels = data.get('channels', ['in_app'])
            
            result = notification_service.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                channels=channels,
                html_content=data.get('html_content'),
                check_preferences=data.get('check_preferences', True),
                check_rate_limit=data.get('check_rate_limit', True)
            )
            
            return jsonify(result), 200 if result.get('success') else 400
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/stats', methods=['GET'])
@token_required
def get_notification_stats():
    """Get notification statistics"""
    try:
        time_range = request.args.get('range', '24h')
        user_id = request.args.get('user_id', type=int)
        
        with get_session_context() as session:
            notification_repo = NotificationRepository(session)
            stats = notification_repo.get_notification_statistics(user_id, time_range)
            
            return jsonify({
                'success': True,
                'data': stats
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/digest/process', methods=['POST'])
@token_required
@admin_required
def process_digests():
    """Process pending digest notifications (admin only)"""
    try:
        with get_session_context() as session:
            digest_service = NotificationDigestService(session)
            result = digest_service.process_digest_queue()
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error processing digests: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/retry-failed', methods=['POST'])
@token_required
@admin_required
def retry_failed():
    """Retry failed notifications (admin only)"""
    try:
        max_retries = request.json.get('max_retries', 10) if request.json else 10
        
        with get_session_context() as session:
            notification_service = EnhancedNotificationService(session)
            result = notification_service.retry_failed_notifications(max_retries)
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error retrying failed notifications: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/templates', methods=['GET'])
@token_required
def get_templates():
    """Get available notification templates"""
    try:
        template_service = NotificationTemplateService()
        templates = template_service.list_templates()
        
        return jsonify({
            'success': True,
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/templates/<template_name>', methods=['GET'])
@token_required
def get_template(template_name):
    """Get a specific template"""
    try:
        template_service = NotificationTemplateService()
        template = template_service.get_template(template_name)
        
        if template:
            return jsonify({
                'success': True,
                'data': template
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Template not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/groups', methods=['GET'])
@token_required
def get_groups():
    """Get notification groups"""
    try:
        with get_session_context() as session:
            group_repo = NotificationGroupRepository(session)
            groups = group_repo.get_active_groups()
            
            return jsonify({
                'success': True,
                'data': [g.to_dict() for g in groups]
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting groups: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@notifications_enhanced_bp.route('/groups', methods=['POST'])
@token_required
@admin_required
def create_group():
    """Create notification group (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        with get_session_context() as session:
            from models.notifications.notification_group import NotificationGroup
            
            group = NotificationGroup(
                name=data.get('name'),
                description=data.get('description'),
                group_type=data.get('group_type', 'custom'),
                default_channels=data.get('default_channels', ['email', 'in_app']),
                min_priority=data.get('min_priority', 'normal')
            )
            
            session.add(group)
            session.commit()
            session.refresh(group)
            
            # Add members if provided
            if data.get('member_ids'):
                user_repo = UserRepository(session)
                for user_id in data.get('member_ids', []):
                    user = user_repo.get_by_id(user_id)
                    if user:
                        group.add_member(user)
                
                session.commit()
            
            return jsonify({
                'success': True,
                'data': group.to_dict(),
                'message': 'Group created successfully'
            }), 201
            
    except Exception as e:
        logger.error(f"Error creating group: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


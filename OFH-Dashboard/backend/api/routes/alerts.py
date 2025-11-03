#!/usr/bin/env python3
"""
Alert Routes
Handles alert management, acknowledgment, and retrieval
"""

from flask import Blueprint, request, jsonify, current_app # type: ignore
from datetime import datetime, timedelta
import logging
from api.middleware.auth_middleware import token_required, get_current_user
from services.alert_service import AlertService  # Use AlertService instead of AlertRepository
from repositories.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)

# Create Blueprint
alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

def get_repositories():
    """Get database repositories and services from Flask app context"""
    try:
        from core.database import get_database_manager
        db_manager = get_database_manager()
        # Use a single session for all repositories to avoid transaction conflicts
        session = db_manager.SessionLocal()
        return {
            'alert_service': AlertService(session),  # Use AlertService instead of AlertRepository
            'conversation_repo': ConversationRepository(session),
            'session': session  # Return session for cleanup
        }
    except Exception as e:
        logger.error(f"Error getting repositories: {e}")
        return None

@alerts_bp.route('', methods=['GET'])
@token_required
def get_alerts():
    """Get recent alerts for the dashboard from database"""
    try:
        # Get repositories
        repos = get_repositories()
        if not repos:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 500
        
        alert_service = repos['alert_service']  # Fixed: Use AlertService instead of AlertRepository
        conversation_repo = repos['conversation_repo']
        session = repos['session']
        
        # Get time range from query parameters
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status')
        severity = request.args.get('severity')
        
        # Get alerts from database using AlertService
        if status and severity:
            # Filter by status first, then filter results by severity
            alerts_by_status = alert_service.get_alerts_by_status(status, limit * 2)  # Get more to filter
            alerts = [a for a in alerts_by_status if a.severity.upper() == severity.upper()][:limit]
        elif status:
            alerts = alert_service.get_alerts_by_status(status, limit)
        elif severity:
            alerts = alert_service.get_alerts_by_severity(severity, limit)
        else:
            alerts = alert_service.get_recent_alerts(hours=hours, limit=limit)
        
        # Transform alerts to API format
        alerts_data = []
        for alert in alerts:
            # Get conversation info if available
            conversation = None
            if alert.conversation_id:
                conversation = conversation_repo.get_by_session_id(alert.conversation_id)
            
            # Calculate response and resolution times
            response_time = 0
            resolution_time = None
            
            if alert.acknowledged_at and alert.created_at:
                response_delta = alert.acknowledged_at - alert.created_at
                response_time = int(response_delta.total_seconds() / 60)
            
            if alert.resolved_at and alert.created_at:
                resolution_delta = alert.resolved_at - alert.created_at
                resolution_time = int(resolution_delta.total_seconds() / 60)
            
            # Get patient info from conversation
            patient_info = {
                'name': 'Unknown Patient',
                'age': None,
                'gender': None
            }
            
            if conversation:
                patient_info = {
                    'name': conversation.patient_name or 'Unknown Patient',
                    'age': conversation.patient_age,
                    'gender': conversation.patient_gender
                }
            
            alert_data = {
                'id': str(alert.id),
                'conversation_id': alert.conversation_id or 'unknown',
                'event_type': alert.event_type or 'unknown',  # Fixed: was alert.alert_type
                'severity': alert.severity or 'low',
                'message': alert.message_content or 'No description',  # Fixed: was alert.description
                'status': alert.status or 'unknown',
                'priority': alert.priority or 'low',
                'created_at': alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat(),
                'assigned_to': getattr(alert, 'acknowledged_by', None) or getattr(alert, 'resolved_by', None) or 'Unassigned',  # Fixed: was alert.assigned_to
                'escalated': alert.status == 'ESCALATED',  # Fixed: derive from status
                'escalation_level': 1 if alert.status == 'ESCALATED' else 0,  # Fixed: derive from status
                'patient_info': patient_info,
                'tags': alert.tags.split(',') if alert.tags else [],  # Fixed: tags is a string, need to parse
                'response_time': response_time,
                'resolution_time': resolution_time
            }
            alerts_data.append(alert_data)
        
        logger.info(f"Retrieved {len(alerts_data)} alerts for user {get_current_user()}")
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'total': len(alerts_data),
            'critical_count': len([a for a in alerts_data if a.get('severity', '').upper() in ['CRITICAL', 'critical']]),
            'active_count': len([a for a in alerts_data if a.get('status') == 'PENDING']),  # Fixed: use PENDING instead of active
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve alerts',
            'message': str(e)
        }), 500
    finally:
        # Clean up session
        if 'session' in locals():
            session.close()

@alerts_bp.route('/<alert_id>/acknowledge', methods=['POST'])
@token_required
def acknowledge_alert(alert_id):
    """Acknowledge a specific alert"""
    repos = None
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        operator_id = data.get('operator_id', current_user)
        
        logger.info(f"Alert {alert_id} acknowledgment requested by {current_user}")
        
        # Get repositories
        repos = get_repositories()
        if not repos:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 500
        
        alert_service = repos['alert_service']
        
        # Try to parse alert_id as integer (database ID), otherwise treat as string event_id
        try:
            event_id_int = int(alert_id)
            # Use database ID
            result = alert_service.acknowledge_alert(event_id_int, operator_id)
        except ValueError:
            # Try as string event_id
            event = alert_service.get_by_event_id_str(alert_id)
            if not event:
                return jsonify({
                    'success': False,
                    'error': 'Alert not found',
                    'message': f'No alert found with ID: {alert_id}'
                }), 404
            result = alert_service.acknowledge_alert(event.id, operator_id)
        
        repos['session'].close()
        
        if not result.get('success'):
            return jsonify(result), 404
        
        logger.info(f"Alert {alert_id} acknowledged by {operator_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}", exc_info=True)
        if repos and 'session' in repos:
            repos['session'].close()
        return jsonify({
            'success': False,
            'error': 'Failed to acknowledge alert',
            'message': str(e)
        }), 500

@alerts_bp.route('/<alert_id>', methods=['GET'])
@token_required
def get_alert_details(alert_id):
    """Get detailed information about a specific alert"""
    repos = None
    try:
        repos = get_repositories()
        if not repos:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 500
        
        alert_service = repos['alert_service']
        conversation_repo = repos['conversation_repo']
        session = repos['session']
        
        # Try to parse alert_id as integer (database ID), otherwise treat as string event_id
        try:
            event_id_int = int(alert_id)
            alert = alert_service.get_by_id(event_id_int)
        except ValueError:
            # Try as string event_id
            alert = alert_service.get_by_event_id_str(alert_id)
        
        if not alert:
            repos['session'].close()
            return jsonify({
                'success': False,
                'error': 'Alert not found',
                'message': f'No alert found with ID: {alert_id}'
            }), 404
        
        # Get conversation info if available
        conversation = None
        if alert.conversation_id:
            conversation = conversation_repo.get_by_session_id(alert.conversation_id)
        
        # Calculate response and resolution times
        response_time = 0
        resolution_time = None
        
        if alert.acknowledged_at and alert.created_at:
            response_delta = alert.acknowledged_at - alert.created_at
            response_time = int(response_delta.total_seconds() / 60)
        
        if alert.resolved_at and alert.created_at:
            resolution_delta = alert.resolved_at - alert.created_at
            resolution_time = int(resolution_delta.total_seconds() / 60)
        
        # Get patient info from conversation
        patient_info = {
            'name': 'Unknown Patient',
            'age': None,
            'gender': None
        }
        
        if conversation:
            patient_info = {
                'name': conversation.patient_name or 'Unknown Patient',
                'age': conversation.patient_age,
                'gender': conversation.patient_gender
            }
        
        alert_details = {
            'id': str(alert.id),
            'event_id': alert.event_id,
            'conversation_id': alert.conversation_id or 'unknown',
            'event_type': alert.event_type or 'unknown',
            'severity': alert.severity or 'low',
            'message': alert.message_content or 'No description',
            'status': alert.status or 'unknown',
            'priority': alert.priority or 'low',
            'created_at': alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat(),
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'acknowledged_by': alert.acknowledged_by or None,
            'resolved_by': alert.resolved_by or None,
            'assigned_to': alert.acknowledged_by or alert.resolved_by or 'Unassigned',
            'escalated': alert.status == 'ESCALATED',
            'escalation_level': 1 if alert.status == 'ESCALATED' else 0,
            'patient_info': patient_info,
            'tags': alert.tags.split(',') if alert.tags else [],
            'response_time': response_time,
            'resolution_time': resolution_time,
            'confidence_score': getattr(alert, 'confidence_score', None),
            'action_taken': getattr(alert, 'action_taken', None),
            'action_notes': getattr(alert, 'action_notes', None),
            'resolution_notes': getattr(alert, 'resolution_notes', None),
            'details': alert.details if hasattr(alert, 'details') else None
        }
        
        repos['session'].close()
        
        logger.info(f"Retrieved details for alert {alert_id}")
        
        return jsonify({
            'success': True,
            'alert': alert_details
        })
        
    except Exception as e:
        logger.error(f"Error retrieving alert details for {alert_id}: {e}", exc_info=True)
        if repos and 'session' in repos:
            repos['session'].close()
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve alert details',
            'message': str(e)
        }), 500

@alerts_bp.route('/<alert_id>/resolve', methods=['POST'])
@token_required
def resolve_alert(alert_id):
    """Resolve a specific alert"""
    repos = None
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes', '')
        action = data.get('action', None)
        
        logger.info(f"Alert {alert_id} resolution requested by {current_user}")
        
        # Get repositories
        repos = get_repositories()
        if not repos:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 500
        
        alert_service = repos['alert_service']
        
        # Try to parse alert_id as integer (database ID), otherwise treat as string event_id
        try:
            event_id_int = int(alert_id)
            # Use database ID
            result = alert_service.resolve_alert(event_id_int, current_user, notes=resolution_notes, action=action)
        except ValueError:
            # Try as string event_id
            event = alert_service.get_by_event_id_str(alert_id)
            if not event:
                repos['session'].close()
                return jsonify({
                    'success': False,
                    'error': 'Alert not found',
                    'message': f'No alert found with ID: {alert_id}'
                }), 404
            result = alert_service.resolve_alert(event.id, current_user, notes=resolution_notes, action=action)
        
        repos['session'].close()
        
        if not result.get('success'):
            return jsonify(result), 404
        
        logger.info(f"Alert {alert_id} resolved by {current_user}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}", exc_info=True)
        if repos and 'session' in repos:
            repos['session'].close()
        return jsonify({
            'success': False,
            'error': 'Failed to resolve alert',
            'message': str(e)
        }), 500

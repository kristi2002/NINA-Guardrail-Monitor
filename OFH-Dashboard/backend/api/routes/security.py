#!/usr/bin/env python3
"""
Security Routes
Handles security monitoring, threat detection, and access control
"""

from flask import Blueprint, request, jsonify # type: ignore
from datetime import datetime, timedelta
import logging
from api.middleware.auth_middleware import token_required, admin_required, get_current_user
from repositories.conversation_repository import ConversationRepository
from repositories.guardrail_event_repository import GuardrailEventRepository
from repositories.user_repository import UserRepository
from models.guardrail_event import GuardrailEvent
from core.database import get_session_context
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Create Blueprint
security_bp = Blueprint('security', __name__, url_prefix='/api/security')

@security_bp.route('/overview', methods=['GET'])
@token_required
def get_security_overview():
    """Get security overview data from database"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Security overview requested by {current_user}")
        
        # Use database session to query real data
        with get_session_context() as session:
            guardrail_repo = GuardrailEventRepository(session)  # Fixed: Use GuardrailEventRepository instead of AlertRepository
            user_repo = UserRepository(session)
            
            # Get statistics from last 24 hours
            hours = 24
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get guardrail events (security threats)
            event_stats = guardrail_repo.get_event_statistics(hours)
            total_events = event_stats.get('total_events', 0)
            
            # Active threats (events with status 'PENDING' or 'ACKNOWLEDGED')
            active_threats = session.query(GuardrailEvent).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.status.in_(['PENDING', 'ACKNOWLEDGED']),  # Fixed: use correct status values
                GuardrailEvent.is_deleted.is_(False)
            ).count()
            
            # Get event statistics (alerts are now GuardrailEvents)
            total_alerts = event_stats.get('total_events', 0)
            critical_alerts = event_stats.get('severity_distribution', {}).get('CRITICAL', 0)            
            # Get user statistics
            user_stats = user_repo.get_user_statistics()
            total_users = user_stats.get('total_users', 0)
            
            # Active sessions = users who logged in recently (last 24 hours)
            active_sessions = user_stats.get('recent_logins_24h', 0)
            
            # Failed logins from user activity
            user_activity = user_repo.get_user_activity_metrics(hours)
            failed_logins = user_activity.get('failed_login_attempts', 0)
            
            # Calculate security score (higher is better)
            # Lower threats and failed logins = higher score
            # If there's truly no data, show 100% (no threats = perfect security)
            threat_score = max(0, 100 - (total_events * 2))
            auth_score = max(0, 100 - (failed_logins * 5))
            security_score = (threat_score + auth_score) / 2
            
            # Recent incidents (critical guardrail events)
            recent_incidents = []
            
            # Get recent critical guardrail events (alerts are now GuardrailEvents)
            critical_events = guardrail_repo.get_by_severity('critical', limit=5)
            for event in critical_events[:3]:
                recent_incidents.append({
                    'id': event.event_id,  # Fixed: was alert.alert_id
                    'type': event.event_type or 'security_alert',  # Fixed: was alert.alert_type
                    'severity': (event.severity or 'low').lower(),
                    'timestamp': event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),  # Fixed: was alert.detected_at
                    'status': event.status,
                    'description': event.message_content or 'Security alert detected'  # Fixed: was alert.title
                })
            
            # Get recent high severity guardrail events
            high_severity_events = guardrail_repo.get_by_severity('high', limit=2)
            for event in high_severity_events:
                if len(recent_incidents) < 5:  # Limit total incidents
                    recent_incidents.append({
                        'id': event.event_id,
                        'type': event.event_type,
                        'severity': (event.severity or 'low').lower(),
                        'timestamp': event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
                        'status': event.status,
                        'description': event.message_content or 'Guardrail event detected'  # Fixed: was event.title or event.description
                    })
            
            security_data = {
                'summary': {
                    'total_threats': total_events,
                    'active_threats': active_threats,
                    'resolved_threats': total_events - active_threats,
                    'security_score': round(security_score, 1),
                    'last_scan': datetime.utcnow().isoformat()
                },
                'threat_distribution': event_stats.get('type_distribution', {}),
                'access_control': {
                    'total_users': total_users,
                    'active_sessions': active_sessions,  # Users who logged in within last 24 hours
                    'failed_logins': failed_logins,
                    'privileged_users': user_stats.get('role_distribution', {}).get('admin', 0)
                },
                'compliance': {
                    'gdpr_compliance': max(0, 100 - (total_events * 3)),  # Placeholder calculation
                    'hipaa_compliance': max(0, 100 - (critical_alerts * 5)),
                    'pci_compliance': max(0, 100 - (failed_logins * 2)),
                    'last_audit': (datetime.utcnow() - timedelta(days=7)).isoformat()
                },
                'recent_incidents': recent_incidents[:5],  # Limit to 5 most recent
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return jsonify({
            'success': True,
            'data': security_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving security overview: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve security overview',
            'message': str(e)
        }), 500

@security_bp.route('/threats', methods=['GET'])
@token_required
def get_security_threats():
    """Get security threats data from alerts"""
    try:
        current_user = get_current_user()
        severity = request.args.get('severity', 'all')
        hours = int(request.args.get('hours', 24))
        
        logger.info(f"Security threats requested by {current_user} with severity: {severity}")
        
        # Use database session to query real guardrail events as security threats
        with get_session_context() as session:
            guardrail_repo = GuardrailEventRepository(session)  # Fixed: Use GuardrailEventRepository instead of AlertRepository
            
            # Get recent guardrail events (alerts are now GuardrailEvents)
            recent_events = guardrail_repo.get_recent_events(hours, 100)
            
            # Filter by severity if specified
            if severity != 'all':
                recent_events = [e for e in recent_events if e.severity.upper() == severity.upper()]
            
            # Map guardrail events to threats
            threats = []
            for event in recent_events:
                threat = {
                    'id': event.event_id,  # Fixed: was alert.alert_id
                    'type': event.event_type,  # Use event_type as threat type
                    'severity': (event.severity or 'low').lower(),
                    'conversation_id': event.conversation_id,
                    'detected_at': event.created_at.isoformat() if event.created_at else datetime.now().isoformat(),  # Fixed: was alert.detected_at
                    'status': event.status,
                    'description': event.message_content,  # Fixed: was alert.title
                    'mitigation': event.action_taken or event.action_notes or 'Action pending',  # Fixed: was alert.resolution_action
                    'assigned_to': event.acknowledged_by or event.resolved_by or 'Unassigned',  # Fixed: was alert.assigned_to
                    'escalated': event.status == 'ESCALATED'  # Fixed: derive from status
                }
                threats.append(threat)
            
            # Calculate summary statistics
            total = len(threats)
            active = len([t for t in threats if t['status'] in ['PENDING', 'ACKNOWLEDGED']])  # Fixed: use correct status values
            resolved = len([t for t in threats if t['status'] == 'RESOLVED'])  # Fixed: use correct status value
            
            # Count by severity
            by_severity = {}
            for threat in threats:
                sev = threat['severity']
                by_severity[sev] = by_severity.get(sev, 0) + 1
            
            threats_data = {
                'threats': threats,
                'summary': {
                    'total': total,
                    'active': active,
                    'resolved': resolved,
                    'by_severity': by_severity
                },
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'data': threats_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving security threats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve security threats',
            'message': str(e)
        }), 500

@security_bp.route('/access', methods=['GET'])
@token_required
def get_security_access():
    """Get access control data from database"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Security access data requested by {current_user}")
        
        # Use database session to query real user data
        with get_session_context() as session:
            user_repo = UserRepository(session)
            
            # Get all active users
            all_users = user_repo.get_all()
            
            # Map users to access data
            users_data = []
            for user in all_users:
                # Determine permissions based on role
                permissions = ['read']
                if user.role in ['operator', 'admin']:
                    permissions.append('write')
                if user.role == 'admin':
                    permissions.extend(['admin', 'security'])
                
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'status': 'active' if user.is_active and not user.is_locked() else 'inactive',
                    'permissions': permissions,
                    'locked': user.is_locked(),
                    'login_attempts': user.login_attempts
                }
                users_data.append(user_info)
            
            # Get recent logins (last 24 hours)
            recent_users = user_repo.get_recent_logins(24, 50)
            
            # Create sessions from recent logins
            sessions = []
            for user in recent_users:
                session_info = {
                    'user_id': user.id,
                    'username': user.username,
                    'login_time': user.last_login.isoformat() if user.last_login else datetime.now().isoformat(),
                    'status': 'active' if user.is_active and not user.is_locked() else 'inactive',
                    'role': user.role
                }
                sessions.append(session_info)
            
            # Get locked users (failed logins)
            locked_users = user_repo.get_locked_users(100)
            failed_logins = []
            for user in locked_users:
                failed_info = {
                    'username': user.username,
                    'attempts': user.login_attempts,
                    'last_attempt': user.locked_until.isoformat() if user.locked_until else None,
                    'blocked': True,
                    'locked_until': user.locked_until.isoformat() if user.locked_until else None
                }
                failed_logins.append(failed_info)
            
            # Calculate summary
            total_users = len(all_users)
            active_sessions = len([s for s in sessions if s['status'] == 'active'])
            active_users = len([u for u in users_data if u['status'] == 'active'])
            
            access_data = {
                'users': users_data,
                'sessions': sessions,
                'failed_logins': failed_logins,
                'summary': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'active_sessions': active_sessions,
                    'locked_users': len(locked_users),
                    'failed_login_attempts': sum([f['attempts'] for f in failed_logins])
                },
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'data': access_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving security access data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve security access data',
            'message': str(e)
        }), 500

@security_bp.route('/compliance', methods=['GET'])
@token_required
def get_security_compliance():
    """Get compliance data"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Security compliance data requested by {current_user}")
        
        # Mock compliance data
        compliance_data = {
            'overall_score': 88,
            'standards': {
                'gdpr': {
                    'score': 92,
                    'status': 'compliant',
                    'last_audit': (datetime.now() - timedelta(days=30)).isoformat(),
                    'issues': [
                        {
                            'id': 'gdpr_001',
                            'description': 'Data retention policy needs update',
                            'severity': 'medium',
                            'status': 'in_progress'
                        }
                    ]
                },
                'hipaa': {
                    'score': 88,
                    'status': 'mostly_compliant',
                    'last_audit': (datetime.now() - timedelta(days=45)).isoformat(),
                    'issues': [
                        {
                            'id': 'hipaa_001',
                            'description': 'Encryption key rotation schedule needs implementation',
                            'severity': 'high',
                            'status': 'pending'
                        }
                    ]
                },
                'pci': {
                    'score': 95,
                    'status': 'compliant',
                    'last_audit': (datetime.now() - timedelta(days=15)).isoformat(),
                    'issues': []
                }
            },
            'recommendations': [
                'Implement automated encryption key rotation',
                'Update data retention policies',
                'Conduct quarterly security training',
                'Implement multi-factor authentication for all users'
            ],
            'next_audit': (datetime.now() + timedelta(days=30)).isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': compliance_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving security compliance data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve security compliance data',
            'message': str(e)
        }), 500

@security_bp.route('/incidents', methods=['GET'])
@token_required
def get_security_incidents():
    """Get security incidents data"""
    try:
        current_user = get_current_user()
        status = request.args.get('status', 'all')
        
        logger.info(f"Security incidents requested by {current_user} with status: {status}")
        
        # Mock incidents data
        incidents_data = {
            'incidents': [
                {
                    'id': 'incident_001',
                    'type': 'unauthorized_access',
                    'severity': 'high',
                    'status': 'investigating',
                    'description': 'Multiple failed login attempts from suspicious IP',
                    'detected_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'assigned_to': 'Security Team',
                    'resolution': None,
                    'resolved_at': None
                },
                {
                    'id': 'incident_002',
                    'type': 'data_breach',
                    'severity': 'critical',
                    'status': 'resolved',
                    'description': 'Suspicious data access pattern detected and contained',
                    'detected_at': (datetime.now() - timedelta(days=1)).isoformat(),
                    'assigned_to': 'Security Team',
                    'resolution': 'Access revoked, data encrypted, incident contained',
                    'resolved_at': (datetime.now() - timedelta(hours=12)).isoformat()
                },
                {
                    'id': 'incident_003',
                    'type': 'malware',
                    'severity': 'medium',
                    'status': 'resolved',
                    'description': 'Malicious file uploaded and quarantined',
                    'detected_at': (datetime.now() - timedelta(days=2)).isoformat(),
                    'assigned_to': 'IT Team',
                    'resolution': 'File quarantined, system cleaned',
                    'resolved_at': (datetime.now() - timedelta(days=1)).isoformat()
                }
            ],
            'summary': {
                'total': 3,
                'active': 1,
                'resolved': 2,
                'by_severity': {
                    'critical': 1,
                    'high': 1,
                    'medium': 1,
                    'low': 0
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': incidents_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving security incidents: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve security incidents',
            'message': str(e)
        }), 500

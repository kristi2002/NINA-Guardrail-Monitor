#!/usr/bin/env python3
"""
Conversation Routes
Handles conversation management, monitoring, and reporting
"""

from flask import Blueprint, request, jsonify, current_app # type: ignore
from datetime import datetime, timedelta
import logging
from api.middleware.auth_middleware import token_required, get_current_user
from repositories.conversation_repository import ConversationRepository
# from repositories.alert_repository import AlertRepository  # OBSOLETE - No longer used
from repositories.guardrail_event_repository import GuardrailEventRepository
from repositories.operator_action_repository import OperatorActionRepository

logger = logging.getLogger(__name__)

# Create Blueprint
conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')

def get_repositories():
    """Get database repositories from Flask app context"""
    try:
        from core.database import get_database_manager
        db_manager = get_database_manager()
        # Use a single session for all repositories to avoid transaction conflicts
        session = db_manager.SessionLocal()
        return {
            'conversation_repo': ConversationRepository(session),
            # 'alert_repo': AlertRepository(session),  # OBSOLETE - No longer used
            'guardrail_repo': GuardrailEventRepository(session),
            'operator_action_repo': OperatorActionRepository(session),
            'session': session  # Return session for cleanup
        }
    except Exception as e:
        logger.error(f"Error getting repositories: {e}", exc_info=True)
        return None

@conversations_bp.route('', methods=['GET'])
@token_required
def get_conversations():
    """Get all conversations with enhanced data from database"""
    try:
        # Get repositories
        repos = get_repositories()
        if not repos:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 500
        
        conversation_repo = repos['conversation_repo']
        guardrail_repo = repos['guardrail_repo']  # Fixed: Use GuardrailEventRepository instead of AlertRepository
        session = repos['session']
        
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Get conversations from database
        if status:
            conversations = conversation_repo.get_by_status(status, limit)
        else:
            conversations = conversation_repo.get_all(skip=offset, limit=limit)
        
        # Transform conversations to API format
        conversations_data = []
        for conv in conversations:
            try:
                # Get related guardrail events (alerts are now GuardrailEvents)
                guardrail_events = guardrail_repo.get_by_conversation_id(conv.id) if guardrail_repo else []
                
                # Calculate statistics
                events_by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
                for event in guardrail_events:
                    severity = (event.severity.lower() if event.severity else 'low').strip()
                    if severity in events_by_severity:
                        events_by_severity[severity] += 1
                
                # Calculate session duration
                session_duration = 0
                try:
                    def normalize_datetime(dt):
                        """Convert datetime to timezone-aware if it's naive"""
                        if dt is None:
                            return None
                        if dt.tzinfo is None:
                            # Assume naive datetime is UTC
                            from datetime import timezone
                            return dt.replace(tzinfo=timezone.utc)
                        return dt
                    
                    if conv.session_start and conv.session_end:
                        start = normalize_datetime(conv.session_start)
                        end = normalize_datetime(conv.session_end)
                        duration = end - start
                        session_duration = int(duration.total_seconds() / 60)
                    elif conv.session_start:
                        from datetime import timezone
                        start = normalize_datetime(conv.session_start)
                        now = datetime.now(timezone.utc)
                        duration = now - start
                        session_duration = int(duration.total_seconds() / 60)
                except Exception as e:
                    logger.warning(f"Error calculating session duration for {conv.id}: {e}")
                    session_duration = 0
                
                # Get patient info safely
                patient_info = {}
                if hasattr(conv, 'patient_info') and isinstance(conv.patient_info, dict):
                    patient_info = conv.patient_info
                elif hasattr(conv, 'patient_info') and conv.patient_info:
                    try:
                        import json
                        if isinstance(conv.patient_info, str):
                            patient_info = json.loads(conv.patient_info)
                        else:
                            patient_info = conv.patient_info
                    except:
                        patient_info = {}
                
                # Use properties if available, otherwise use patient_info dict
                patient_name = None
                patient_age = 0
                patient_gender = 'U'
                patient_pathology = 'Unknown'
                
                try:
                    if hasattr(conv, 'patient_name') and callable(conv.patient_name):
                        patient_name = conv.patient_name
                    else:
                        patient_name = patient_info.get('name', f'Patient {conv.id}')
                except:
                    patient_name = patient_info.get('name', f'Patient {conv.id}')
                
                try:
                    if hasattr(conv, 'patient_age') and callable(conv.patient_age):
                        patient_age = conv.patient_age
                    else:
                        patient_age = patient_info.get('age', 0)
                except:
                    patient_age = patient_info.get('age', 0)
                
                try:
                    if hasattr(conv, 'patient_gender') and callable(conv.patient_gender):
                        patient_gender = conv.patient_gender
                    else:
                        patient_gender = patient_info.get('gender', 'U')
                except:
                    patient_gender = patient_info.get('gender', 'U')
                
                try:
                    if hasattr(conv, 'patient_pathology') and callable(conv.patient_pathology):
                        patient_pathology = conv.patient_pathology
                    else:
                        patient_pathology = patient_info.get('pathology', 'Unknown')
                except:
                    patient_pathology = patient_info.get('pathology', 'Unknown')
                
                # Map backend status to frontend expected status
                # Backend uses: ACTIVE, COMPLETED, TERMINATED, ESCALATED
                # Frontend expects: IN_PROGRESS, COMPLETED, etc.
                backend_status = (conv.status or 'UNKNOWN').upper()
                frontend_status = backend_status
                if backend_status == 'ACTIVE':
                    frontend_status = 'IN_PROGRESS'  # Map ACTIVE to IN_PROGRESS for frontend
                
                conversation_data = {
                    'id': conv.id or 'unknown',
                    'patient_id': conv.patient_id or f'patient_{conv.id}',
                    'patientInfo': {
                        'name': patient_name or f'Patient {conv.id}',
                        'age': patient_age or 0,
                        'gender': patient_gender or 'U',
                        'pathology': patient_pathology or 'Unknown'
                    },
                    'status': frontend_status,
                    'situation': conv.situation or 'No description',
                    'situationLevel': (conv.risk_level or 'low').lower(),
                    'created_at': conv.created_at.isoformat() if conv.created_at else datetime.utcnow().isoformat(),
                    'updated_at': conv.updated_at.isoformat() if conv.updated_at else (conv.created_at.isoformat() if conv.created_at else datetime.utcnow().isoformat()),
                    'session_start': conv.session_start.isoformat() if conv.session_start else None,
                    'session_end': conv.session_end.isoformat() if conv.session_end else None,
                    'session_duration_minutes': session_duration,
                    'total_messages': conv.total_messages or 0,
                    'guardrail_violations': len(guardrail_events),
                    'statistics': {
                        'total_events': len(guardrail_events),
                        'events_by_severity': events_by_severity,
                        'guardrail_violations': len(guardrail_events)
                    }
                }
                conversations_data.append(conversation_data)
            except Exception as e:
                logger.error(f"Error processing conversation {conv.id}: {e}", exc_info=True)
                # Continue with other conversations even if one fails
                continue
        
        logger.info(f"Retrieved {len(conversations_data)} conversations for user {get_current_user()}")
        
        return jsonify({
            'success': True,
            'conversations': conversations_data,
            'total': len(conversations_data)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving conversations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve conversations',
            'message': str(e)
        }), 500
    finally:
        # Clean up session
        if 'session' in locals():
            session.close()

@conversations_bp.route('/<conversation_id>', methods=['GET'])
@token_required
def get_conversation_details(conversation_id):
    """Get detailed information about a specific conversation from database"""
    session = None  # Define session here to use in finally block
    try:
        # Get repositories
        repos = get_repositories()
        if not repos:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 500
        
        session = repos['session']  # Get session for cleanup
        conversation_repo = repos['conversation_repo']
        guardrail_repo = repos['guardrail_repo']
        operator_action_repo = repos['operator_action_repo']  # Get the new repo
        
        # Get conversation from database
        conversation = conversation_repo.get_by_session_id(conversation_id)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found',
                'message': f'No conversation found with ID: {conversation_id}'
            }), 404
        
        # Get related guardrail events (alerts are now GuardrailEvents)
        guardrail_events = guardrail_repo.get_by_conversation_id(conversation_id)
        
        # Get related operator actions
        operator_actions = operator_action_repo.get_by_conversation_id(conversation_id)
        
        # Calculate statistics
        events_by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for event in guardrail_events:
            severity = event.severity.lower() if event.severity else 'low'
            if severity in events_by_severity:
                events_by_severity[severity] += 1
        
        # Calculate session duration
        session_duration = 0
        if conversation.session_start and conversation.session_end:
            duration = conversation.session_end - conversation.session_start
            session_duration = int(duration.total_seconds() / 60)
        elif conversation.session_start:
            # Use timezone-aware datetime for subtraction
            from datetime import timezone
            duration = datetime.now(timezone.utc) - conversation.session_start
            session_duration = int(duration.total_seconds() / 60)
        
        # Get recent events (last 10)
        recent_events = []
        for event in guardrail_events[:10]:  # Loop over events
            recent_events.append({
                'id': event.id,
                'type': event.event_type or 'guardrail_violation',
                'event_type': event.event_type or 'guardrail_violation',
                'severity': (event.severity or 'low').lower(),
                'message': event.message_content or 'No message',  # Correct column
                'description': event.message_content or 'No message',
                'timestamp': event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
                'confidence': getattr(event, 'confidence_score', 0.0) or 0.0
            })
        
        # Get recent actions (last 10)
        recent_actions = []
        for action in operator_actions[:10]:  # Loop over ACTIONS, not events
            recent_actions.append({
                'id': action.id,
                'type': action.action_type or 'action',
                'operator': action.operator_id or 'Unknown',
                'timestamp': action.action_timestamp.isoformat() if action.action_timestamp else datetime.utcnow().isoformat(),
                'description': action.description or 'No description'
            })
        
        # Map backend status to frontend expected status
        backend_status = (conversation.status or 'UNKNOWN').upper()
        frontend_status = backend_status
        if backend_status == 'ACTIVE':
            frontend_status = 'IN_PROGRESS'  # Map ACTIVE to IN_PROGRESS for frontend
        
        conversation_details = {
            'id': conversation.id,
            'patient_id': conversation.patient_id or 'unknown',
            'patientInfo': {
                'name': conversation.patient_name or 'Unknown Patient',
                'age': conversation.patient_age or 0,
                'gender': conversation.patient_gender or 'U',
                'pathology': conversation.patient_pathology or 'Unknown'
            },
            'status': frontend_status,
            'situation': conversation.situation or 'No description',
            'situationLevel': conversation.risk_level or 'low',
            'created_at': conversation.created_at.isoformat() if conversation.created_at else datetime.utcnow().isoformat(),
            'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else conversation.created_at.isoformat() if conversation.created_at else datetime.utcnow().isoformat(),
            'session_start': conversation.session_start.isoformat() if conversation.session_start else None,
            'session_end': conversation.session_end.isoformat() if conversation.session_end else None,
            'session_duration_minutes': session_duration,
            'total_messages': conversation.total_messages or 0,
            'guardrail_violations': len(guardrail_events),
            'statistics': {
                'total_events': len(guardrail_events),
                'events_by_severity': events_by_severity,
                'guardrail_violations': len(guardrail_events)
            },
            'recent_events': recent_events,
            'recent_actions': recent_actions
        }
        
        logger.info(f"Retrieved details for conversation {conversation_id}")
        
        return jsonify({
            'success': True,
            'conversation': conversation_details,
            'statistics': conversation_details['statistics'],
            'events': conversation_details['recent_events'],
            'actions': conversation_details['recent_actions']  # Now correctly populated
        })
        
    except Exception as e:
        logger.error(f"Error retrieving conversation details for {conversation_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve conversation details',
            'message': str(e)
        }), 500
    finally:
        if session:
            session.close()

@conversations_bp.route('/<conversation_id>/start', methods=['POST'])
@token_required
def start_conversation_monitoring(conversation_id):
    """Start monitoring a conversation using Kafka"""
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        
        logger.info(f"Starting monitoring for conversation {conversation_id} by {current_user}")
        
        # Get Kafka service from Flask app context
        from flask import current_app # type: ignore
        kafka_service = getattr(current_app, 'kafka_service', None)
        
        if not kafka_service:
            logger.error("Kafka service not available for starting conversation monitoring")
            return jsonify({
                'success': False,
                'error': 'Kafka service not available',
                'message': 'Cannot start conversation monitoring'
            }), 503
        
        # Start conversation monitoring via Kafka
        try:
            success = kafka_service.start_conversation_monitoring(conversation_id)
            
            if success:
                logger.info(f"Conversation monitoring started for {conversation_id}")
                
                response = {
                    'success': True,
                    'message': f'Conversation {conversation_id} monitoring started',
                    'conversation_id': conversation_id,
                    'started_by': current_user,
                    'started_at': datetime.now().isoformat(),
                    'status': 'monitoring_active',
                    'kafka_topics_created': True
                }
            else:
                logger.error(f"Failed to start conversation monitoring for {conversation_id}")
                response = {
                    'success': False,
                    'error': 'Failed to start conversation monitoring',
                    'message': 'Could not create Kafka topics for conversation'
                }
                
        except Exception as kafka_error:
            logger.error(f"Kafka error when starting conversation monitoring {conversation_id}: {kafka_error}")
            response = {
                'success': False,
                'error': 'Failed to start conversation monitoring via Kafka',
                'message': str(kafka_error)
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error starting monitoring for conversation {conversation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start conversation monitoring',
            'message': str(e)
        }), 500

@conversations_bp.route('/<conversation_id>/stop', methods=['POST'])
@token_required
def stop_conversation_monitoring(conversation_id):
    """Stop monitoring a conversation and send stop command to guardrail via Kafka"""
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        
        # Extract operator message and reason from request
        operator_message = data.get('message', 'Conversation stopped by operator')
        stop_reason = data.get('reason', 'operator_intervention')
        final_message = data.get('final_message', 'This conversation has been terminated by an operator.')
        
        logger.info(f"Stopping monitoring for conversation {conversation_id} by {current_user}")
        
        # Get Kafka service from Flask app context
        from flask import current_app
        kafka_service = getattr(current_app, 'kafka_service', None)
        
        if not kafka_service:
            logger.error("Kafka service not available for sending stop command")
            return jsonify({
                'success': False,
                'error': 'Kafka service not available',
                'message': 'Cannot send stop command to guardrail'
            }), 503
        
        # Send operator action via Kafka to guardrail
        try:
            # Create operator action message for guardrail
            operator_action = {
                'action_type': 'stop_conversation',
                'conversation_id': conversation_id,
                'operator_id': current_user,
                'message': operator_message,
                'stop_reason': stop_reason,
                'timestamp': datetime.now().isoformat(),
                'command': {
                    'type': 'STOP',
                    'reason': stop_reason,
                    'final_message': final_message
                }
            }
            
            # Send via Kafka producer
            success = kafka_service.send_operator_action(
                conversation_id=conversation_id,
                action_type='stop_conversation',
                message=operator_message,
                reason=stop_reason,
                operator_id=current_user
            )
            
            if success:
                logger.info(f"Stop command sent to guardrail for conversation {conversation_id}")
                
                # Stop monitoring in our system
                kafka_service.stop_conversation_monitoring(conversation_id)
                
                response = {
                    'success': True,
                    'message': f'Conversation {conversation_id} stopped and command sent to guardrail',
                    'conversation_id': conversation_id,
                    'stopped_by': current_user,
                    'stopped_at': datetime.now().isoformat(),
                    'status': 'conversation_stopped',
                    'kafka_message_sent': True
                }
            else:
                logger.error(f"Failed to send stop command to guardrail for conversation {conversation_id}")
                response = {
                    'success': False,
                    'error': 'Failed to send stop command to guardrail',
                    'message': 'Conversation monitoring stopped locally but guardrail may not be notified'
                }
                
        except Exception as kafka_error:
            logger.error(f"Kafka error when stopping conversation {conversation_id}: {kafka_error}")
            response = {
                'success': False,
                'error': 'Failed to send stop command via Kafka',
                'message': str(kafka_error)
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error stopping monitoring for conversation {conversation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to stop conversation monitoring',
            'message': str(e)
        }), 500

@conversations_bp.route('/<conversation_id>/report', methods=['GET'])
@token_required
def generate_conversation_report(conversation_id):
    """Generate a report for a conversation"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Generating report for conversation {conversation_id} by {current_user}")
        
        # Mock report data
        report_data = {
            'conversation_id': conversation_id,
            'patient_id': f'patient_{conversation_id.split("_")[1]}',
            'patientInfo': {
                'name': f'Paziente {conversation_id.split("_")[1]}',
                'age': 28,
                'gender': 'F',
                'pathology': 'Disturbo depressivo maggiore'
            },
            'session_duration': 60,
            'total_messages': 45,
            'guardrail_violations': 2,
            'risk_level': 'high',
            'summary': 'Conversation showed signs of self-harm ideation requiring immediate attention',
            'recommendations': [
                'Immediate psychiatric evaluation recommended',
                'Consider hospitalization for safety',
                'Follow up with patient within 24 hours'
            ],
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user
        }
        
        logger.info(f"Report generated for conversation {conversation_id}")
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Error generating report for conversation {conversation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate conversation report',
            'message': str(e)
        }), 500

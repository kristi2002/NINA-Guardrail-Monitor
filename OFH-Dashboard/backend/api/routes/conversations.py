#!/usr/bin/env python3
"""
Conversation Routes
Handles conversation management, monitoring, and reporting
"""

from flask import Blueprint, request, jsonify, current_app # type: ignore
from datetime import datetime, timedelta, timezone
import logging
import uuid
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
        
        session = repos['session']  # Get session for status updates
        conversation_repo = repos['conversation_repo']
        guardrail_repo = repos['guardrail_repo']  # Fixed: Use GuardrailEventRepository instead of AlertRepository
        
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
                
                # If conversation has session_end but status is still ACTIVE, mark as COMPLETED
                if backend_status == 'ACTIVE' and conv.session_end is not None:
                    frontend_status = 'COMPLETED'
                    # Update the database status to reflect reality
                    try:
                        conv.status = 'COMPLETED'
                        session.commit()
                    except:
                        session.rollback()
                        pass
                elif backend_status == 'ACTIVE':
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
        
        # If conversation has session_end but status is still ACTIVE, mark as COMPLETED
        if backend_status == 'ACTIVE' and conversation.session_end is not None:
            frontend_status = 'COMPLETED'
            # Update the database status to reflect reality
            try:
                conversation.status = 'COMPLETED'
                session.commit()
            except:
                session.rollback()
                pass
        elif backend_status == 'ACTIVE':
            frontend_status = 'IN_PROGRESS'  # Map ACTIVE to IN_PROGRESS for frontend
        
        # Build patientInfo from patient_info JSON if available, otherwise use defaults
        patient_info = conversation.patient_info if conversation.patient_info else {}
        patient_info_dict = patient_info if isinstance(patient_info, dict) else {}
        
        conversation_details = {
            'id': conversation.id,
            'patient_id': conversation.patient_id or 'unknown',
            'patientInfo': {
                'name': patient_info_dict.get('name') or conversation.patient_name or 'Unknown Patient',
                'age': patient_info_dict.get('age') if patient_info_dict.get('age') is not None and patient_info_dict.get('age') != 0 else None,
                'gender': patient_info_dict.get('gender') if patient_info_dict.get('gender') and patient_info_dict.get('gender') != 'U' else None,
                'pathology': patient_info_dict.get('pathology') if patient_info_dict.get('pathology') and patient_info_dict.get('pathology') != 'Unknown' else None
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
    repos = None
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        
        # Extract admin message and reason from request
        operator_message = data.get('message', 'Conversation stopped by admin')
        stop_reason = data.get('reason', 'admin_intervention')
        final_message = data.get('final_message', 'This conversation has been terminated by an admin.')
        
        logger.info(f"Stopping monitoring for conversation {conversation_id} by {current_user}")
        
        # Always update database first, regardless of Kafka status
        repos = get_repositories()
        if not repos:
            logger.error("Database repositories not available")
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 503
        
        # Update conversation status in database
        try:
            conversation = repos['conversation_repo'].get_by_session_id(conversation_id)
            if conversation:
                conversation.status = 'STOPPED'
                from datetime import timezone
                # Ensure timezone-aware datetime for session_end
                conversation.session_end = datetime.now(timezone.utc)
                if conversation.session_start:
                    # Normalize both datetimes to timezone-aware before subtracting
                    def normalize_datetime(dt):
                        """Convert datetime to timezone-aware if it's naive"""
                        if dt is None:
                            return None
                        if dt.tzinfo is None:
                            # Assume naive datetime is UTC
                            return dt.replace(tzinfo=timezone.utc)
                        return dt
                    
                    start = normalize_datetime(conversation.session_start)
                    end = normalize_datetime(conversation.session_end)
                    duration = end - start
                    conversation.session_duration_minutes = int(duration.total_seconds() / 60)
                
                # Record operator action in database
                try:
                    import uuid
                    from datetime import timezone
                    repos['operator_action_repo'].create(
                        action_id=str(uuid.uuid4()),
                        conversation_id=conversation_id,
                        action_type='stop_conversation',
                        action_category='conversation',
                        operator_id=current_user,
                        title='Conversazione fermata e segnalata',
                        description=operator_message,
                        action_timestamp=datetime.now(timezone.utc),
                        status='completed',
                        result='success',
                        action_data={
                            'reason': stop_reason,
                            'final_message': final_message,
                            'stopped_by': current_user
                        }
                    )
                    logger.info(f"Recorded operator action for stopping conversation {conversation_id}")
                except Exception as action_error:
                    logger.warning(f"Failed to record operator action: {action_error}", exc_info=True)
                    # Continue even if action recording fails
                
                repos['session'].commit()
                logger.info(f"Updated conversation {conversation_id} status to STOPPED in database")
            else:
                logger.warning(f"Conversation {conversation_id} not found in database")
                return jsonify({
                    'success': False,
                    'error': 'Conversation not found',
                    'message': f'No conversation found with ID: {conversation_id}'
                }), 404
        except Exception as db_error:
            logger.error(f"Error updating conversation in database: {db_error}")
            repos['session'].rollback()
            raise  # Re-raise to be caught by outer try-except
        
        # Try to send via Kafka (but don't fail if it doesn't work)
        kafka_message_sent = False
        kafka_warning = None
        
        # Get Kafka service from Flask app context
        from flask import current_app
        kafka_service = getattr(current_app, 'kafka_service', None)
        
        if kafka_service:
            try:
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
                    kafka_message_sent = True
                    # Stop monitoring in our system
                    kafka_service.stop_conversation_monitoring(conversation_id)
                else:
                    logger.warning(f"Failed to send stop command to guardrail for conversation {conversation_id}")
                    kafka_warning = 'Failed to send stop command to guardrail via Kafka'
                    
            except Exception as kafka_error:
                logger.error(f"Kafka error when stopping conversation {conversation_id}: {kafka_error}")
                kafka_warning = f'Kafka error: {str(kafka_error)}'
        else:
            logger.warning("Kafka service not available for sending stop command")
            kafka_warning = 'Kafka service not available - conversation stopped locally but guardrail may not be notified'
        
        # Always return success since database was updated
        response = {
            'success': True,
            'message': f'Conversation {conversation_id} stopped successfully',
            'conversation_id': conversation_id,
            'stopped_by': current_user,
            'stopped_at': datetime.now().isoformat(),
            'status': 'STOPPED',
            'kafka_message_sent': kafka_message_sent
        }
        
        if kafka_warning:
            response['warning'] = kafka_warning
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error stopping monitoring for conversation {conversation_id}: {e}", exc_info=True)
        if repos and repos.get('session'):
            repos['session'].rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to stop conversation monitoring',
            'message': str(e)
        }), 500
    finally:
        # Clean up database session
        if repos and repos.get('session'):
            repos['session'].close()

@conversations_bp.route('/<conversation_id>/complete', methods=['POST'])
@token_required
def complete_conversation(conversation_id):
    """
    Mark a conversation as COMPLETED (naturally ended)
    This is different from STOPPED which indicates operator intervention
    """
    repos = None
    try:
        current_user = get_current_user()
        
        logger.info(f"Completing conversation {conversation_id} by {current_user}")
        
        # Get repositories
        repos = get_repositories()
        if not repos:
            logger.error("Database repositories not available")
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 503
        
        # Get conversation from database
        conversation = repos['conversation_repo'].get_by_session_id(conversation_id)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found',
                'message': f'No conversation found with ID: {conversation_id}'
            }), 404
        
        # Update conversation status to COMPLETED
        from datetime import timezone
        conversation.status = 'COMPLETED'
        if not conversation.session_end:
            conversation.session_end = datetime.now(timezone.utc)
        
        # Calculate duration if not already set
        if conversation.session_start and conversation.session_end:
            def normalize_datetime(dt):
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            
            start = normalize_datetime(conversation.session_start)
            end = normalize_datetime(conversation.session_end)
            duration = end - start
            conversation.session_duration_minutes = int(duration.total_seconds() / 60)
        
        # Record operator action in database
        try:
            repos['operator_action_repo'].create(
                action_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                action_type='complete_conversation',
                action_category='conversation',
                operator_id=current_user,
                title='Conversazione completata',
                description=f'Conversazione marcata come completata dall\'amministratore',
                action_timestamp=datetime.now(timezone.utc),
                status='completed',
                result='success',
                action_data={
                    'previous_status': conversation.status,
                    'new_status': 'COMPLETED',
                    'reason': 'admin_manual_completion'
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record operator action for completion: {e}")
        
        # Commit changes
        repos['session'].commit()
        
        # Send notification about conversation completion
        try:
            from services.notifications.notification_orchestrator import NotificationOrchestrator
            with repos['session']:
                orchestrator = NotificationOrchestrator(repos['session'])
                orchestrator.send_conversation_notification(
                    conversation_id=conversation_id,
                    conversation_data={
                        'patient_id': conversation.patient_id,
                        'status': 'COMPLETED',
                        'risk_level': conversation.risk_level or 'normal',
                        'message': f'Conversation {conversation_id} has been completed'
                    }
                )
        except Exception as notif_error:
            logger.warning(f"Failed to send completion notification: {notif_error}")
        
        logger.info(f"Conversation {conversation_id} marked as COMPLETED by {current_user}")
        
        return jsonify({
            'success': True,
            'message': 'Conversation marked as completed',
            'conversation_id': conversation_id,
            'status': 'COMPLETED'
        })
        
    except Exception as e:
        logger.error(f"Error completing conversation {conversation_id}: {e}", exc_info=True)
        if repos and repos.get('session'):
            repos['session'].rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to complete conversation',
            'message': str(e)
        }), 500
    finally:
        # Clean up database session
        if repos and repos.get('session'):
            repos['session'].close()

@conversations_bp.route('/<conversation_id>/cancel', methods=['POST'])
@token_required
def cancel_conversation(conversation_id):
    """
    Cancel a conversation (mark as CANCELLED)
    This is different from STOPPED which indicates operator intervention during active session
    and COMPLETED which indicates natural completion
    """
    repos = None
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        
        # Extract cancellation reason from request
        cancel_reason = data.get('reason', 'admin_cancelled')
        operator_message = data.get('message', 'Conversation cancelled by admin')
        
        logger.info(f"Cancelling conversation {conversation_id} by {current_user}")
        
        # Get repositories
        repos = get_repositories()
        if not repos:
            logger.error("Database repositories not available")
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 503
        
        # Get conversation from database
        conversation = repos['conversation_repo'].get_by_session_id(conversation_id)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found',
                'message': f'No conversation found with ID: {conversation_id}'
            }), 404
        
        # Update conversation status to CANCELLED
        from datetime import timezone
        old_status = conversation.status
        conversation.status = 'CANCELLED'
        if not conversation.session_end:
            conversation.session_end = datetime.now(timezone.utc)
        
        # Calculate duration if not already set
        if conversation.session_start and conversation.session_end:
            def normalize_datetime(dt):
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            
            start = normalize_datetime(conversation.session_start)
            end = normalize_datetime(conversation.session_end)
            duration = end - start
            conversation.session_duration_minutes = int(duration.total_seconds() / 60)
        
        # Record operator action in database
        try:
            import uuid
            repos['operator_action_repo'].create(
                action_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                action_type='cancel_conversation',
                action_category='conversation',
                operator_id=current_user,
                title='Conversazione annullata',
                description=operator_message,
                action_timestamp=datetime.now(timezone.utc),
                status='completed',
                result='success',
                action_data={
                    'previous_status': old_status,
                    'new_status': 'CANCELLED',
                    'reason': cancel_reason,
                    'cancelled_by': current_user
                }
            )
            logger.info(f"Recorded operator action for cancelling conversation {conversation_id}")
        except Exception as e:
            logger.warning(f"Failed to record operator action for cancellation: {e}")
        
        # Commit changes
        repos['session'].commit()
        
        logger.info(f"Conversation {conversation_id} marked as CANCELLED by {current_user}")
        
        return jsonify({
            'success': True,
            'message': 'Conversation marked as cancelled',
            'conversation_id': conversation_id,
            'status': 'CANCELLED'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling conversation {conversation_id}: {e}", exc_info=True)
        if repos and repos.get('session'):
            repos['session'].rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to cancel conversation',
            'message': str(e)
        }), 500
    finally:
        # Clean up database session
        if repos and repos.get('session'):
            repos['session'].close()

@conversations_bp.route('/<conversation_id>/situation', methods=['PUT'])
@token_required
def update_conversation_situation(conversation_id):
    """Update conversation situation and risk level (e.g., mark alarm as unreliable/false alarm)"""
    repos = None
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        
        # Extract situation and level from request
        situation = data.get('situation', 'Regolare')
        level = data.get('level', 'low').upper()
        
        # Map level to risk_level
        level_mapping = {
            'LOW': 'LOW',
            'MEDIUM': 'MEDIUM',
            'HIGH': 'HIGH',
            'CRITICAL': 'CRITICAL'
        }
        risk_level = level_mapping.get(level, 'LOW')
        
        logger.info(f"Updating situation for conversation {conversation_id} by {current_user}: situation={situation}, level={risk_level}")
        
        # Get repositories
        repos = get_repositories()
        if not repos:
            logger.error("Database repositories not available")
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 503
        
        # Get conversation from database
        conversation = repos['conversation_repo'].get_by_session_id(conversation_id)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found',
                'message': f'No conversation found with ID: {conversation_id}'
            }), 404
        
        # Store old values for logging
        old_situation = conversation.situation
        old_risk_level = conversation.risk_level
        
        # Update conversation
        from datetime import timezone
        conversation.situation = situation
        conversation.risk_level = risk_level
        conversation.requires_attention = risk_level in ['HIGH', 'CRITICAL']
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Record operator action (false alarm)
        try:
            import uuid
            repos['operator_action_repo'].create(
                action_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                action_type='false_alarm',
                action_category='alert',
                operator_id=current_user,
                title='Allarme marcato come non attendibile',
                description=f'Amministratore ha marcato l\'allarme come non attendibile. Situazione aggiornata a: {situation}',
                action_timestamp=datetime.now(timezone.utc),
                status='completed',
                result='success',
                action_data={
                    'old_situation': old_situation,
                    'new_situation': situation,
                    'old_risk_level': old_risk_level,
                    'new_risk_level': risk_level,
                    'reason': 'admin_judgment'
                }
            )
            logger.info(f"Created operator action for false alarm on conversation {conversation_id}")
        except Exception as action_error:
            logger.warning(f"Failed to create operator action: {action_error}", exc_info=True)
            # Continue even if action recording fails
        
        # Commit database changes
        repos['session'].commit()
        logger.info(f"Updated conversation {conversation_id} situation to '{situation}' with risk level '{risk_level}'")
        
        # Try to send feedback via Kafka (optional - don't fail if Kafka is unavailable)
        kafka_warning = None
        from flask import current_app
        kafka_service = getattr(current_app, 'kafka_service', None)
        
        if kafka_service:
            try:
                # Send false alarm feedback
                success = kafka_service.send_false_alarm_feedback(
                    conversation_id=conversation_id,
                    original_event_id=None,  # Could be enhanced to track specific event
                    feedback=f"Admin marked alarm as unreliable. Situation: {situation}, Level: {risk_level}"
                )
                if not success:
                    kafka_warning = 'Failed to send feedback to guardrail service via Kafka'
            except Exception as kafka_error:
                logger.warning(f"Kafka error when sending false alarm feedback: {kafka_error}")
                kafka_warning = f'Kafka error: {str(kafka_error)}'
        else:
            kafka_warning = 'Kafka service not available - feedback not sent to guardrail service'
        
        response = {
            'success': True,
            'message': f'Conversation situation updated successfully',
            'conversation_id': conversation_id,
            'updated_by': current_user,
            'updated_at': datetime.now().isoformat(),
            'situation': situation,
            'risk_level': risk_level,
            'requires_attention': conversation.requires_attention
        }
        
        if kafka_warning:
            response['warning'] = kafka_warning
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error updating conversation situation for {conversation_id}: {e}", exc_info=True)
        if repos and repos.get('session'):
            repos['session'].rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update conversation situation',
            'message': str(e)
        }), 500
    finally:
        # Clean up database session
        if repos and repos.get('session'):
            repos['session'].close()

@conversations_bp.route('/<conversation_id>/report', methods=['GET'])
@token_required
def generate_conversation_report(conversation_id):
    """Generate a report for a conversation using real database data"""
    repos = None
    try:
        current_user = get_current_user()
        
        logger.info(f"Generating report for conversation {conversation_id} by {current_user}")
        
        # Get repositories
        repos = get_repositories()
        if not repos:
            logger.error("Database repositories not available")
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'message': 'Unable to connect to database'
            }), 503
        
        # Get conversation from database
        conversation = repos['conversation_repo'].get_by_session_id(conversation_id)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found',
                'message': f'No conversation found with ID: {conversation_id}'
            }), 404
        
        # Get guardrail events for this conversation
        guardrail_events = repos['guardrail_repo'].get_by_conversation_id(conversation_id)
        
        # Calculate session duration
        session_duration = 0
        if conversation.session_start and conversation.session_end:
            duration = conversation.session_end - conversation.session_start
            session_duration = int(duration.total_seconds() / 60)
        elif conversation.session_start:
            from datetime import timezone
            duration = datetime.now(timezone.utc) - conversation.session_start
            session_duration = int(duration.total_seconds() / 60)
        
        # Build patientInfo from patient_info JSON if available
        patient_info = conversation.patient_info if conversation.patient_info else {}
        patient_info_dict = patient_info if isinstance(patient_info, dict) else {}
        
        # Format dates (use Italian locale if available)
        created_date = conversation.session_start if conversation.session_start else conversation.created_at
        if created_date:
            try:
                import locale
                locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
                conversation_date = created_date.strftime('%d %B %Y')
            except:
                # Fallback to English if Italian locale not available
                conversation_date = created_date.strftime('%d %B %Y')
            conversation_time = created_date.strftime('%H:%M')
        else:
            conversation_date = 'N/A'
            conversation_time = 'N/A'
        
        # Count events by type and severity (matching frontend mapEventTypeToDisplay logic)
        def categorize_event(event):
            """Categorize event as WARNING, ALERT, or INFO based on event_type and severity"""
            event_type = (event.event_type or '').lower()
            severity = (event.severity or '').lower()
            
            # Info level events
            info_types = ['conversation_started', 'conversation_ended', 'validation_passed']
            # Warning level events
            warning_types = ['warning_triggered', 'inappropriate_content', 'compliance_check']
            # Alert level events
            alert_types = ['alarm_triggered', 'privacy_violation_prevented', 'medication_warning', 
                          'emergency_protocol', 'operator_intervention', 'system_alert', 'validation_failed']
            
            if event_type in info_types:
                return 'INFO'
            elif event_type in warning_types:
                return 'WARNING'
            elif event_type in alert_types:
                return 'ALERT'
            else:
                # Fallback to severity-based categorization
                if severity in ['critical', 'high']:
                    return 'ALERT'
                elif severity in ['medium', 'warning']:
                    return 'WARNING'
                else:
                    return 'INFO'
        
        warning_events = sum(1 for e in guardrail_events if categorize_event(e) == 'WARNING')
        alert_events = sum(1 for e in guardrail_events if categorize_event(e) == 'ALERT')
        
        # Build report data from real database data
        report_data = {
            'id': conversation.id,
            'conversation_id': conversation_id,
            'patient_id': conversation.patient_id or conversation_id,
            'patientId': conversation.patient_id or conversation_id,
            'patientInfo': {
                'name': patient_info_dict.get('name') or conversation.patient_name or f'Paziente {conversation.patient_id or conversation_id}',
                'age': patient_info_dict.get('age') if patient_info_dict.get('age') is not None and patient_info_dict.get('age') != 0 else None,
                'gender': patient_info_dict.get('gender') if patient_info_dict.get('gender') and patient_info_dict.get('gender') != 'U' else None,
                'pathology': patient_info_dict.get('pathology') if patient_info_dict.get('pathology') and patient_info_dict.get('pathology') != 'Unknown' else None
            },
            'conversationDate': conversation_date,
            'conversationTime': conversation_time,
            'duration': session_duration,
            'status': conversation.status or 'UNKNOWN',
            'situation': conversation.situation or 'Normale',
            'situationLevel': conversation.risk_level.lower() if conversation.risk_level else 'low',
            'risk_level': conversation.risk_level or 'low',
            'events': [
                {
                    'type': e.event_type or 'guardrail_violation',
                    'event_type': e.event_type or 'guardrail_violation',
                    'timestamp': e.created_at.isoformat() if e.created_at else datetime.utcnow().isoformat(),
                    'description': e.message_content or e.description or 'No description',
                    'details': e.details if hasattr(e, 'details') and e.details else None,
                    'severity': e.severity or 'low'
                }
                for e in guardrail_events
            ],
            'summary': {
                'totalEvents': len(guardrail_events),
                'warningEvents': warning_events,
                'alertEvents': alert_events,
                'riskLevel': conversation.risk_level.lower() if conversation.risk_level else 'low'
            },
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'generatedAt': datetime.now(timezone.utc).isoformat(),  # Also send camelCase for frontend compatibility
            'generated_by': current_user
        }
        
        logger.info(f"Report generated for conversation {conversation_id} with {len(guardrail_events)} events")
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Error generating report for conversation {conversation_id}: {e}", exc_info=True)
        if repos and repos.get('session'):
            repos['session'].rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to generate conversation report',
            'message': str(e)
        }), 500
    finally:
        # Clean up database session
        if repos and repos.get('session'):
            repos['session'].close()

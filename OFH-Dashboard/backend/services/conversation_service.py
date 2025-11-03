#!/usr/bin/env python3
"""
Conversation Service
Handles business logic for conversation management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime, timedelta
from .base_service import BaseService
from repositories.conversation_repository import ConversationRepository
from models.conversation import ConversationSession
import logging

logger = logging.getLogger(__name__)

class ConversationService(BaseService):
    """Service for conversation business logic"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.conversation_repo = ConversationRepository(self.get_session())
    
    def get_by_id(self, conversation_id: int) -> Optional[ConversationSession]:
        """Get conversation by ID"""
        try:
            return self.conversation_repo.get_by_id(conversation_id)
        except Exception as e:
            self.logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    def get_by_session_id(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation by session ID"""
        try:
            return self.conversation_repo.get_by_session_id(session_id)
        except Exception as e:
            self.logger.error(f"Error getting conversation {session_id}: {e}")
            return None
    
    def get_active_conversations(self, limit: int = 100) -> List[ConversationSession]:
        """Get all active conversations"""
        try:
            return self.conversation_repo.get_by_status('ACTIVE', limit)
        except Exception as e:
            self.logger.error(f"Error getting active conversations: {e}")
            return []
    
    def get_conversations_by_patient(self, patient_id: str, limit: int = 100) -> List[ConversationSession]:
        """Get conversations by patient ID"""
        try:
            return self.conversation_repo.get_by_patient_id(patient_id, limit)
        except Exception as e:
            self.logger.error(f"Error getting conversations for patient {patient_id}: {e}")
            return []
    
    def get_high_risk_conversations(self, limit: int = 100) -> List[ConversationSession]:
        """Get high-risk conversations"""
        try:
            return self.conversation_repo.get_by_risk_level(['HIGH', 'CRITICAL'], limit)
        except Exception as e:
            self.logger.error(f"Error getting high-risk conversations: {e}")
            return []
    
    def get_conversations_needing_attention(self, limit: int = 100) -> List[ConversationSession]:
        """Get conversations needing attention"""
        try:
            return self.conversation_repo.get_conversations_needing_attention(limit)
        except Exception as e:
            self.logger.error(f"Error getting conversations needing attention: {e}")
            return []
    
    def get_recent_conversations(self, hours: int = 24, limit: int = 100) -> List[ConversationSession]:
        """Get recent conversations"""
        try:
            return self.conversation_repo.get_recent_conversations(hours, limit)
        except Exception as e:
            self.logger.error(f"Error getting recent conversations: {e}")
            return []
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new conversation session"""
        try:
            # Validate required fields
            required_fields = ['session_id', 'patient_id', 'session_start']
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
            sanitized_data.setdefault('status', 'ACTIVE')
            sanitized_data.setdefault('risk_level', 'LOW')
            sanitized_data.setdefault('is_monitored', True)
            sanitized_data.setdefault('requires_attention', False)
            sanitized_data.setdefault('escalated', False)
            sanitized_data.setdefault('total_messages', 0)
            sanitized_data.setdefault('guardrail_violations', 0)
            
            # Create conversation
            conversation = self.conversation_repo.create(**sanitized_data)
            
            self.log_operation('conversation_created', details={
                'session_id': conversation.session_id,
                'patient_id': conversation.patient_id,
                'risk_level': conversation.risk_level
            })
            
            return self.format_response(
                success=True,
                data=conversation.to_dict_with_patient(),
                message="Conversation created successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'create_conversation')
    
    def update(self, conversation_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation"""
        try:
            # Sanitize input
            sanitized_data = self.sanitize_input(data)
            
            # Update conversation
            conversation = self.conversation_repo.update(conversation_id, **sanitized_data)
            
            if not conversation:
                return self.format_response(
                    success=False,
                    message="Conversation not found"
                )
            
            self.log_operation('conversation_updated', details={
                'session_id': conversation.session_id,
                'updated_fields': list(sanitized_data.keys())
            })
            
            return self.format_response(
                success=True,
                data=conversation.to_dict_with_patient(),
                message="Conversation updated successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'update_conversation')
    
    def delete(self, conversation_id: int) -> Dict[str, Any]:
        """Delete conversation (soft delete)"""
        try:
            success = self.conversation_repo.soft_delete(conversation_id)
            
            if not success:
                return self.format_response(
                    success=False,
                    message="Conversation not found"
                )
            
            self.log_operation('conversation_deleted', details={'conversation_id': conversation_id})
            
            return self.format_response(
                success=True,
                message="Conversation deleted successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'delete_conversation')
    
    def start_conversation(self, patient_id: str, patient_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a new conversation session"""
        try:
            # Generate session ID
            session_id = f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{patient_id}"
            
            # Prepare conversation data
            conversation_data = {
                'session_id': session_id,
                'patient_id': patient_id,
                'patient_info': patient_info or {},
                'session_start': datetime.utcnow(),
                'status': 'ACTIVE',
                'risk_level': 'LOW',
                'is_monitored': True
            }
            
            return self.create(conversation_data)
            
        except Exception as e:
            return self.handle_exception(e, 'start_conversation')
    
    def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End a conversation session"""
        try:
            conversation = self.conversation_repo.get_by_session_id(session_id)
            
            if not conversation:
                return self.format_response(
                    success=False,
                    message="Conversation not found"
                )
            
            # Update conversation
            update_data = {
                'status': 'COMPLETED',
                'session_end': datetime.utcnow()
            }
            
            # Calculate duration
            if conversation.session_start:
                duration = datetime.utcnow() - conversation.session_start
                update_data['session_duration_minutes'] = int(duration.total_seconds() / 60)
            
            result = self.update(conversation.id, update_data)
            
            if result['success']:
                self.log_operation('conversation_ended', details={
                    'session_id': session_id,
                    'duration_minutes': update_data.get('session_duration_minutes', 0)
                })
            
            return result
            
        except Exception as e:
            return self.handle_exception(e, 'end_conversation')
    
    def update_risk_level(self, session_id: str, risk_level: str, situation: str = None) -> Dict[str, Any]:
        """Update conversation risk level"""
        try:
            conversation = self.conversation_repo.get_by_session_id(session_id)
            
            if not conversation:
                return self.format_response(
                    success=False,
                    message="Conversation not found"
                )
            
            # Validate risk level
            valid_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            if risk_level not in valid_levels:
                return self.format_response(
                    success=False,
                    message="Invalid risk level",
                    errors=[f"Risk level must be one of: {', '.join(valid_levels)}"]
                )
            
            # Update risk level
            update_data = {
                'risk_level': risk_level,
                'requires_attention': risk_level in ['HIGH', 'CRITICAL']
            }
            
            if situation:
                update_data['situation'] = situation
            
            result = self.update(conversation.id, update_data)
            
            if result['success']:
                self.log_operation('risk_level_updated', details={
                    'session_id': session_id,
                    'old_risk_level': conversation.risk_level,
                    'new_risk_level': risk_level,
                    'situation': situation
                })
            
            return result
            
        except Exception as e:
            return self.handle_exception(e, 'update_risk_level')
    
    def escalate_conversation(self, session_id: str, operator_id: str, reason: str = None) -> Dict[str, Any]:
        """Escalate a conversation"""
        try:
            conversation = self.conversation_repo.get_by_session_id(session_id)
            
            if not conversation:
                return self.format_response(
                    success=False,
                    message="Conversation not found"
                )
            
            # Update conversation
            update_data = {
                'escalated': True,
                'requires_attention': True,
                'notes': f"Escalated by {operator_id}" + (f": {reason}" if reason else "")
            }
            
            result = self.update(conversation.id, update_data)
            
            if result['success']:
                self.log_operation('conversation_escalated', operator_id, {
                    'session_id': session_id,
                    'reason': reason
                })
            
            return result
            
        except Exception as e:
            return self.handle_exception(e, 'escalate_conversation', operator_id)
    
    def get_conversation_statistics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            stats = self.conversation_repo.get_conversation_statistics(hours)
            
            self.log_operation('conversation_statistics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=stats,
                message="Conversation statistics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_conversation_statistics')
    
    def get_conversation_metrics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Get conversation metrics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            metrics = self.conversation_repo.get_conversation_metrics(hours)
            
            self.log_operation('conversation_metrics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=metrics,
                message="Conversation metrics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_conversation_metrics')
    
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

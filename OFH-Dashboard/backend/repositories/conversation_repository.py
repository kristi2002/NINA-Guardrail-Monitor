#!/usr/bin/env python3
"""
Conversation Repository
Handles conversation-specific database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from models.conversation import ConversationSession
import logging

logger = logging.getLogger(__name__)

class ConversationRepository(BaseRepository):
    """Repository for ConversationSession model with conversation-specific operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, ConversationSession)
    
    def get_by_session_id(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation by session_id (maps to id field in database)"""
        return self.get_by_field('id', session_id)
    
    def get_by_patient_id(self, patient_id: str, limit: int = 100) -> List[ConversationSession]:
        """Get conversations by patient ID"""
        try:
            return self.db.query(ConversationSession).filter(
                ConversationSession.patient_id == patient_id,
                ConversationSession.is_deleted.is_(False)
            ).order_by(desc(ConversationSession.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting conversations for patient {patient_id}: {e}")
            raise
    
    def get_by_status(self, status: str, limit: int = 100) -> List[ConversationSession]:
        """Get conversations by status"""
        try:
            return self.db.query(ConversationSession).filter(
                ConversationSession.status == status,
                ConversationSession.is_deleted.is_(False)
            ).order_by(desc(ConversationSession.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting conversations by status {status}: {e}")
            raise
    
    def get_by_risk_level(self, risk_levels: List[str], limit: int = 100) -> List[ConversationSession]:
        """Get conversations by risk level (NOW QUERIES THE DB COLUMN)"""
        try:
            # --- FIX: Query the real database column ---
            return self.db.query(ConversationSession).filter(
                ConversationSession.risk_level.in_(risk_levels),
                ConversationSession.is_deleted.is_(False)
            ).order_by(desc(ConversationSession.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting conversations by risk level {risk_levels}: {e}")
            raise
    
    def get_conversations_needing_attention(self, limit: int = 100) -> List[ConversationSession]:
        """Get conversations needing attention (NOW QUERIES THE DB COLUMN)"""
        try:
            # --- FIX: Query the real database column ---
            return self.db.query(ConversationSession).filter(
                ConversationSession.is_deleted.is_(False),
                or_(
                    ConversationSession.requires_attention == True,
                    ConversationSession.risk_level.in_(['HIGH', 'CRITICAL'])
                )
            ).order_by(desc(ConversationSession.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting conversations needing attention: {e}")
            raise
    
    def get_recent_conversations(self, hours: int = 24, limit: int = 100) -> List[ConversationSession]:
        """Get recent conversations"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(ConversationSession).filter(
                ConversationSession.session_start >= cutoff_time,
                ConversationSession.is_deleted.is_(False)
            ).order_by(desc(ConversationSession.session_start)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            raise
    
    def get_conversation_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get conversation statistics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_query = self.db.query(ConversationSession).filter(
                ConversationSession.session_start >= cutoff_time,
                ConversationSession.is_deleted.is_(False)
            )
            
            total_conversations = base_query.count()
            
            active_conversations = base_query.filter(
                ConversationSession.status == 'ACTIVE'
            ).count()
            
            # --- FIX: Query the real database column ---
            high_risk_conversations = base_query.filter(
                ConversationSession.risk_level.in_(['HIGH', 'CRITICAL'])
            ).count()
            
            # --- FIX: Query the real database column ---
            risk_stats = base_query.with_entities(
                ConversationSession.risk_level,
                func.count(ConversationSession.id).label('count')
            ).group_by(ConversationSession.risk_level).all()
            
            status_stats = base_query.with_entities(
                ConversationSession.status,
                func.count(ConversationSession.id).label('count')
            ).group_by(ConversationSession.status).all()
            
            avg_duration = base_query.filter(
                ConversationSession.session_duration_minutes.isnot(None)
            ).with_entities(func.avg(ConversationSession.session_duration_minutes)).scalar()
            
            # --- FIX: Query the real database column ---
            escalated_conversations = base_query.filter(
                ConversationSession.escalated == True
            ).count()
            
            escalation_rate = (escalated_conversations / total_conversations) if total_conversations > 0 else 0
            
            return {
                'total_conversations': total_conversations,
                'active_conversations': active_conversations,
                'high_risk_conversations': high_risk_conversations,
                'average_duration_minutes': float(avg_duration) if avg_duration else 0,
                'escalation_rate': escalation_rate,
                'risk_distribution': {stat.risk_level: stat.count for stat in risk_stats},
                'status_distribution': {stat.status: stat.count for stat in status_stats},
                'time_range_hours': hours,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting conversation statistics: {e}")
            raise
    
    def get_conversation_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get conversation metrics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_query = self.db.query(ConversationSession).filter(
                ConversationSession.session_start >= cutoff_time,
                ConversationSession.is_deleted.is_(False)
            )

            # --- FIX: Query the real database columns ---
            avg_sentiment = base_query.filter(
                ConversationSession.sentiment_score.isnot(None)
            ).with_entities(func.avg(ConversationSession.sentiment_score)).scalar()
            
            avg_engagement = base_query.filter(
                ConversationSession.engagement_score.isnot(None)
            ).with_entities(func.avg(ConversationSession.engagement_score)).scalar()

            avg_satisfaction = base_query.filter(
                ConversationSession.satisfaction_score.isnot(None)
            ).with_entities(func.avg(ConversationSession.satisfaction_score)).scalar()

            total_violations = base_query.with_entities(
                func.sum(ConversationSession.guardrail_violations)
            ).scalar()

            high_risk_count = base_query.filter(
                ConversationSession.risk_level.in_(['HIGH', 'CRITICAL'])
            ).count()
            
            total_conversations = base_query.count()
            
            high_risk_rate = (high_risk_count / total_conversations) if total_conversations > 0 else 0
            
            return {
                'average_sentiment_score': float(avg_sentiment) if avg_sentiment else 0,
                'average_engagement_score': float(avg_engagement) if avg_engagement else 0,
                'average_satisfaction_score': float(avg_satisfaction) if avg_satisfaction else 0,
                'total_guardrail_violations': int(total_violations) if total_violations else 0,
                'high_risk_rate': high_risk_rate,
                'time_range_hours': hours,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting conversation metrics: {e}")
            raise

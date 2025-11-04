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
            try:
                self.db.rollback()
            except Exception:
                pass
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
            try:
                self.db.rollback()
            except Exception:
                pass
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
            try:
                self.db.rollback()
            except Exception:
                pass
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
            try:
                self.db.rollback()
            except Exception:
                pass
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
            try:
                self.db.rollback()
            except Exception:
                pass
            raise
    
    def get_conversation_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get conversation statistics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_filter = and_(
                ConversationSession.session_start >= cutoff_time,
                ConversationSession.is_deleted.is_(False)
            )
            
            # Use func.count() to avoid loading all columns (including patient_info which might not exist)
            total_conversations = self.db.query(func.count(ConversationSession.id)).filter(base_filter).scalar() or 0
            
            active_conversations = self.db.query(func.count(ConversationSession.id)).filter(
                base_filter,
                ConversationSession.status == 'ACTIVE'
            ).scalar() or 0
            
            # --- FIX: Query the real database column ---
            high_risk_conversations = self.db.query(func.count(ConversationSession.id)).filter(
                base_filter,
                ConversationSession.risk_level.in_(['HIGH', 'CRITICAL'])
            ).scalar() or 0
            
            # --- FIX: Query the real database column ---
            risk_stats = self.db.query(
                ConversationSession.risk_level,
                func.count(ConversationSession.id).label('count')
            ).filter(base_filter).group_by(ConversationSession.risk_level).all()
            
            status_stats = self.db.query(
                ConversationSession.status,
                func.count(ConversationSession.id).label('count')
            ).filter(base_filter).group_by(ConversationSession.status).all()
            
            avg_duration = self.db.query(func.avg(ConversationSession.session_duration_minutes)).filter(
                base_filter,
                ConversationSession.session_duration_minutes.isnot(None)
            ).scalar()
            
            # --- FIX: Query the real database column ---
            escalated_conversations = self.db.query(func.count(ConversationSession.id)).filter(
                base_filter,
                ConversationSession.escalated == True
            ).scalar() or 0
            
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
            try:
                self.db.rollback()
            except Exception:
                pass
            raise
    
    def get_conversation_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get conversation metrics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_filter = and_(
                ConversationSession.session_start >= cutoff_time,
                ConversationSession.is_deleted.is_(False)
            )

            # --- FIX: Query the real database columns ---
            avg_sentiment = self.db.query(func.avg(ConversationSession.sentiment_score)).filter(
                base_filter,
                ConversationSession.sentiment_score.isnot(None)
            ).scalar()
            
            avg_engagement = self.db.query(func.avg(ConversationSession.engagement_score)).filter(
                base_filter,
                ConversationSession.engagement_score.isnot(None)
            ).scalar()

            avg_satisfaction = self.db.query(func.avg(ConversationSession.satisfaction_score)).filter(
                base_filter,
                ConversationSession.satisfaction_score.isnot(None)
            ).scalar()

            total_violations = self.db.query(func.sum(ConversationSession.guardrail_violations)).filter(
                base_filter
            ).scalar()

            high_risk_count = self.db.query(func.count(ConversationSession.id)).filter(
                base_filter,
                ConversationSession.risk_level.in_(['HIGH', 'CRITICAL'])
            ).scalar() or 0
            
            total_conversations = self.db.query(func.count(ConversationSession.id)).filter(base_filter).scalar() or 0
            
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
            try:
                self.db.rollback()
            except Exception:
                pass
            raise

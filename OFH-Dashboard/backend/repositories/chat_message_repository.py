#!/usr/bin/env python3
"""
Chat Message Repository
Handles chat message-specific database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from models.chat_message import ChatMessage
import logging

logger = logging.getLogger(__name__)

class ChatMessageRepository(BaseRepository):
    """Repository for ChatMessage model with message-specific operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, ChatMessage)
    
    def get_by_message_id(self, message_id: str) -> Optional[ChatMessage]:
        """Get message by message_id"""
        return self.get_by_field('message_id', message_id)
    
    def get_by_conversation_id(self, conversation_id: str, limit: int = 100) -> List[ChatMessage]:
        """Get messages by conversation ID"""
        try:
            return self.db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.is_deleted.is_(False)
            ).order_by(asc(ChatMessage.sequence_number)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            raise
    
    def get_by_sender_type(self, sender_type: str, limit: int = 100) -> List[ChatMessage]:
        """Get messages by sender type"""
        try:
            return self.db.query(ChatMessage).filter(
                ChatMessage.sender_type == sender_type,
                ChatMessage.is_deleted.is_(False)
            ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting messages by sender type {sender_type}: {e}")
            raise
    
    def get_high_risk_messages(self, risk_threshold: float = 0.7, limit: int = 100) -> List[ChatMessage]:
        """Get high-risk messages"""
        try:
            return self.db.query(ChatMessage).filter(
                ChatMessage.risk_score >= risk_threshold,
                ChatMessage.is_deleted.is_(False)
            ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting high-risk messages: {e}")
            raise
    
    def get_sensitive_messages(self, limit: int = 100) -> List[ChatMessage]:
        """Get messages with sensitive content"""
        try:
            return self.db.query(ChatMessage).filter(
                ChatMessage.contains_sensitive_content == True,
                ChatMessage.is_deleted.is_(False)
            ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting sensitive messages: {e}")
            raise
    
    def get_unmoderated_messages(self, limit: int = 100) -> List[ChatMessage]:
        """Get unmoderated messages"""
        try:
            return self.db.query(ChatMessage).filter(
                ChatMessage.is_moderated == False,
                ChatMessage.is_deleted.is_(False)
            ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting unmoderated messages: {e}")
            raise
    
    def get_recent_messages(self, hours: int = 24, limit: int = 100) -> List[ChatMessage]:
        """Get recent messages"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(ChatMessage).filter(
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False)
            ).order_by(desc(ChatMessage.timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            raise
    
    def moderate_message(self, message_id: str, user_id: str, notes: str = None) -> Optional[ChatMessage]:
        """Moderate a message"""
        try:
            message = self.get_by_message_id(message_id)
            if not message:
                return None
            
            message.moderate(user_id, notes)
            self.db.commit()
            self.db.refresh(message)
            
            logger.info(f"Message {message_id} moderated by {user_id}")
            return message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error moderating message {message_id}: {e}")
            raise
    
    def get_message_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get message statistics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Total messages
            total_messages = self.db.query(ChatMessage).filter(
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False)
            ).count()
            
            # Messages by sender type
            sender_stats = self.db.query(
                ChatMessage.sender_type,
                func.count(ChatMessage.id).label('count')
            ).filter(
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False)
            ).group_by(ChatMessage.sender_type).all()
            
            # High-risk messages
            high_risk_messages = self.db.query(ChatMessage).filter(
                ChatMessage.risk_score >= 0.7,
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False)
            ).count()
            
            # Sensitive messages
            sensitive_messages = self.db.query(ChatMessage).filter(
                ChatMessage.contains_sensitive_content == True,
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False)
            ).count()
            
            # Average sentiment score
            avg_sentiment = self.db.query(
                func.avg(ChatMessage.sentiment_score)
            ).filter(
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False),
                ChatMessage.sentiment_score.isnot(None)
            ).scalar()
            
            # Average risk score
            avg_risk = self.db.query(
                func.avg(ChatMessage.risk_score)
            ).filter(
                ChatMessage.timestamp >= cutoff_time,
                ChatMessage.is_deleted.is_(False),
                ChatMessage.risk_score.isnot(None)
            ).scalar()
            
            return {
                'total_messages': total_messages,
                'high_risk_messages': high_risk_messages,
                'sensitive_messages': sensitive_messages,
                'average_sentiment_score': float(avg_sentiment) if avg_sentiment else 0,
                'average_risk_score': float(avg_risk) if avg_risk else 0,
                'sender_distribution': {stat.sender_type: stat.count for stat in sender_stats},
                'time_range_hours': hours,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting message statistics: {e}")
            raise

#!/usr/bin/env python3
"""
Chat Message Model
Handles individual chat messages in conversations
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime

class ChatMessage(BaseModel):
    """Chat message model for conversation messages"""
    __tablename__ = 'chat_messages'
    
    # Basic message information
    message_id = Column(String(50), unique=True, nullable=False, index=True)
    conversation_id = Column(String(50), ForeignKey('conversation_sessions.id'), nullable=False, index=True)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default='text', nullable=False)  # text, image, file, system
    sender_type = Column(String(20), nullable=False, index=True)  # user, bot, system, operator
    
    # Sender information
    sender_id = Column(String(50), nullable=True, index=True)
    sender_name = Column(String(100), nullable=True)
    
    # Message timing
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)  # Order in conversation
    
    # Message analysis
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    emotion = Column(String(30), nullable=True)  # happy, sad, angry, neutral, etc.
    language = Column(String(10), default='it', nullable=False)
    
    # Safety analysis
    risk_score = Column(Float, nullable=True)  # 0.0 to 1.0
    contains_sensitive_content = Column(Boolean, default=False, nullable=False)
    flagged_keywords = Column(JSON, nullable=True)  # List of flagged keywords
    
    # Response information (for bot messages)
    response_time_ms = Column(Integer, nullable=True)
    model_version = Column(String(20), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Message metadata
    message_metadata = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)  # File attachments info
    
    # Moderation
    is_moderated = Column(Boolean, default=False, nullable=False)
    moderation_notes = Column(Text, nullable=True)
    moderated_by = Column(String(50), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    conversation = relationship("ConversationSession", back_populates="messages")
    # events = relationship("GuardrailEvent", back_populates="message")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_sender', 'sender_type'),
        Index('idx_message_timestamp', 'timestamp'),
        Index('idx_message_sequence', 'conversation_id', 'sequence_number'),
        Index('idx_message_risk', 'risk_score'),
        Index('idx_message_sensitive', 'contains_sensitive_content'),
        Index('idx_message_moderated', 'is_moderated'),
        Index('idx_message_sender_type', 'sender_type', 'conversation_id'),
    )
    
    def is_user_message(self):
        """Check if message is from user"""
        return self.sender_type == 'user'
    
    def is_bot_message(self):
        """Check if message is from bot"""
        return self.sender_type == 'bot'
    
    def is_system_message(self):
        """Check if message is from system"""
        return self.sender_type == 'system'
    
    def is_operator_message(self):
        """Check if message is from operator"""
        return self.sender_type == 'operator'
    
    def is_high_risk(self):
        """Check if message has high risk score"""
        return self.risk_score and self.risk_score >= 0.7
    
    def is_sensitive(self):
        """Check if message contains sensitive content"""
        return self.contains_sensitive_content
    
    def get_sentiment_label(self):
        """Get sentiment label from score"""
        if self.sentiment_score is None:
            return 'unknown'
        elif self.sentiment_score >= 0.3:
            return 'positive'
        elif self.sentiment_score <= -0.3:
            return 'negative'
        else:
            return 'neutral'
    
    def get_risk_level(self):
        """Get risk level from score"""
        if self.risk_score is None:
            return 'unknown'
        elif self.risk_score >= 0.8:
            return 'critical'
        elif self.risk_score >= 0.6:
            return 'high'
        elif self.risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def moderate(self, user_id, notes=None):
        """Mark message as moderated"""
        self.is_moderated = True
        self.moderated_by = user_id
        self.moderated_at = datetime.utcnow()
        if notes:
            self.moderation_notes = notes
    
    def to_dict_with_analysis(self):
        """Convert to dictionary with analysis results"""
        data = self.to_dict_serialized()
        
        # Add analysis results
        data['sentiment_label'] = self.get_sentiment_label()
        data['risk_level'] = self.get_risk_level()
        data['is_high_risk'] = self.is_high_risk()
        data['is_sensitive'] = self.is_sensitive()
        
        return data
    
    def __repr__(self):
        return f"<ChatMessage(id='{self.message_id}', type='{self.sender_type}', content='{self.content[:50]}...')>"

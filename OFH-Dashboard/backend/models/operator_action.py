#!/usr/bin/env python3
"""
Operator Action Model
Handles operator actions and interventions
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime

class OperatorAction(BaseModel):
    """Operator action model for tracking interventions and responses"""
    __tablename__ = 'operator_actions'
    
    # Basic action information
    action_id = Column(String(50), unique=True, nullable=False, index=True)
    conversation_id = Column(String(50), ForeignKey('conversation_sessions.id'), nullable=True, index=True)
    alert_id = Column(String(50), nullable=True, index=True)
    
    # Action details
    action_type = Column(String(50), nullable=False, index=True)  # escalate, acknowledge, resolve, intervene, etc.
    action_category = Column(String(30), nullable=False, index=True)  # alert, conversation, system, maintenance
    
    # Action content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    action_notes = Column(Text, nullable=True)
    
    # Operator information
    operator_id = Column(String(50), nullable=False, index=True)
    operator_name = Column(String(100), nullable=True)
    operator_role = Column(String(20), nullable=True)
    
    # Action timing
    action_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    response_time_minutes = Column(Integer, nullable=True)
    
    # Action status
    status = Column(String(20), default='pending', nullable=False, index=True)  # pending, in_progress, completed, failed, cancelled
    priority = Column(String(20), default='medium', nullable=False, index=True)  # low, medium, high, urgent
    
    # Action results
    result = Column(String(100), nullable=True)  # success, partial_success, failed, cancelled
    result_notes = Column(Text, nullable=True)
    completion_time = Column(DateTime(timezone=True), nullable=True)
    
    # Impact assessment
    impact_level = Column(String(20), nullable=True)  # low, medium, high, critical
    affected_users = Column(Integer, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)
    
    # Action metadata
    action_data = Column(JSON, nullable=True)  # Additional action-specific data
    system_changes = Column(JSON, nullable=True)  # System changes made
    notifications_sent = Column(JSON, nullable=True)  # Notifications sent as part of action
    
    # Follow-up information
    requires_followup = Column(Boolean, default=False, nullable=False)
    followup_notes = Column(Text, nullable=True)
    followup_due_date = Column(DateTime(timezone=True), nullable=True)
    followup_completed = Column(Boolean, default=False, nullable=False)
    
    # Quality metrics
    effectiveness_score = Column(Float, nullable=True)  # 0.0 to 1.0
    user_satisfaction = Column(Float, nullable=True)  # 0.0 to 1.0
    feedback_notes = Column(Text, nullable=True)
    
    # Relationships
    conversation = relationship("ConversationSession", back_populates="actions")
    # alert = relationship("Alert", back_populates="actions")  # Alert model no longer exists
    # operator = relationship("User", back_populates="actions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_action_operator', 'operator_id'),
        Index('idx_action_type', 'action_type'),
        Index('idx_action_status', 'status'),
        Index('idx_action_priority', 'priority'),
        Index('idx_action_timestamp', 'action_timestamp'),
        Index('idx_action_conversation', 'conversation_id'),
        Index('idx_action_alert', 'alert_id'),
        Index('idx_action_category', 'action_category'),
        Index('idx_action_followup', 'requires_followup'),
        Index('idx_action_operator_type', 'operator_id', 'action_type'),
        Index('idx_action_status_priority', 'status', 'priority'),
    )
    
    def is_completed(self):
        """Check if action is completed"""
        return self.status == 'completed'
    
    def is_pending(self):
        """Check if action is pending"""
        return self.status == 'pending'
    
    def is_in_progress(self):
        """Check if action is in progress"""
        return self.status == 'in_progress'
    
    def is_urgent(self):
        """Check if action is urgent"""
        return self.priority == 'urgent'
    
    def is_high_impact(self):
        """Check if action has high impact"""
        return self.impact_level in ['high', 'critical']
    
    def needs_followup(self):
        """Check if action needs follow-up"""
        return self.requires_followup and not self.followup_completed
    
    def is_followup_overdue(self):
        """Check if follow-up is overdue"""
        if not self.requires_followup or self.followup_completed:
            return False
        return self.followup_due_date and datetime.utcnow() > self.followup_due_date
    
    def start_action(self):
        """Mark action as in progress"""
        self.status = 'in_progress'
        self.updated_at = datetime.utcnow()
    
    def complete_action(self, result='success', notes=None):
        """Mark action as completed"""
        self.status = 'completed'
        self.result = result
        self.completion_time = datetime.utcnow()
        if notes:
            self.result_notes = notes
        
        # Calculate resolution time if we have the start time
        if self.action_timestamp:
            delta = self.completion_time - self.action_timestamp
            self.resolution_time_minutes = int(delta.total_seconds() / 60)
    
    def fail_action(self, reason=None):
        """Mark action as failed"""
        self.status = 'failed'
        self.result = 'failed'
        self.completion_time = datetime.utcnow()
        if reason:
            self.result_notes = reason
    
    def cancel_action(self, reason=None):
        """Cancel the action"""
        self.status = 'cancelled'
        self.result = 'cancelled'
        self.completion_time = datetime.utcnow()
        if reason:
            self.result_notes = reason
    
    def complete_followup(self, notes=None):
        """Mark follow-up as completed"""
        self.followup_completed = True
        self.followup_notes = notes
        self.updated_at = datetime.utcnow()
    
    def calculate_response_time(self):
        """Calculate response time in minutes"""
        if self.action_timestamp and self.created_at:
            delta = self.action_timestamp - self.created_at
            return int(delta.total_seconds() / 60)
        return None
    
    def to_dict_with_metrics(self):
        """Convert to dictionary with calculated metrics"""
        data = self.to_dict_serialized()
        
        # Add calculated metrics
        data['response_time_minutes'] = self.calculate_response_time()
        data['is_completed'] = self.is_completed()
        data['is_pending'] = self.is_pending()
        data['is_in_progress'] = self.is_in_progress()
        data['is_urgent'] = self.is_urgent()
        data['is_high_impact'] = self.is_high_impact()
        data['needs_followup'] = self.needs_followup()
        data['is_followup_overdue'] = self.is_followup_overdue()
        
        return data
    
    def __repr__(self):
        return f"<OperatorAction(id='{self.action_id}', type='{self.action_type}', status='{self.status}')>"

#!/usr/bin/env python3
"""
Guardrail Event Model
Handles guardrail violations and safety events
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    Float,
    Boolean,
    JSON,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime, timezone


class GuardrailEvent(BaseModel):
    """Guardrail event model for safety violations and detections"""

    __tablename__ = "guardrail_events"

    # Basic event information
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    conversation_id = Column(
        String(50), ForeignKey("conversation_sessions.id"), nullable=False, index=True
    )

    # Event classification
    event_type = Column(
        String(50), nullable=False, index=True
    )  # self_harm, violence, inappropriate_content, etc.
    severity = Column(
        String(20), nullable=False, index=True
    )  # CRITICAL, HIGH, MEDIUM, LOW
    category = Column(
        String(30), nullable=False, default="alert", index=True
    )  # alert, conversation, system, etc. - derived from event_type

    # Title for display (required by database)
    title = Column(
        String(200), nullable=False, default="Guardrail Event"
    )  # Human-readable title for the event

    # Description (required by database, separate from message_content)
    description = Column(
        Text, nullable=False, default="Guardrail event detected"
    )  # Detailed description of the event

    # Event details
    message_content = Column(
        Text, nullable=True
    )  # The original message content (nullable for backward compatibility)
    detected_text = Column(
        Text, nullable=True
    )  # The actual text that triggered the event

    # Detection information
    confidence_score = Column(
        Float, nullable=False, default=0.0
    )  # NOT NULL with default value to match database constraint
    detection_method = Column(
        String(50), nullable=True
    )  # ai_model, keyword, pattern, manual
    model_version = Column(String(20), nullable=True)

    # Context information
    message_id = Column(String(50), nullable=True)
    message_timestamp = Column(DateTime(timezone=True), nullable=True)

    # --- FIX: STATUS MISMATCH ---
    # Status and workflow
    # Your services (AlertService, EscalationService) use PENDING, ACKNOWLEDGED, RESOLVED, ESCALATED.
    status = Column(
        String(20), default="PENDING", nullable=False, index=True
    )  # PENDING, ACKNOWLEDGED, RESOLVED, ESCALATED
    reviewed_by = Column(
        String(50), nullable=True, index=True
    )  # Kept for 'acknowledged_by' / 'resolved_by'
    reviewed_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Kept for 'acknowledged_at' / 'resolved_at'

    # Action taken
    action_taken = Column(
        String(100), nullable=True
    )  # escalated, warning_sent, conversation_paused, etc.
    action_notes = Column(Text, nullable=True)  # Replaced 'resolution_notes'

    # --- ADDED COLUMNS TO MATCH AlertService/EnhancedDatabaseService ---
    # These columns may not exist in database yet - migration will add them
    # Using deferred() won't help with .count() queries, so we use func.count() in queries instead
    response_time_minutes = Column(Integer, nullable=True)
    acknowledged_by = Column(String(50), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(50), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalated_to = Column(String(50), nullable=True)
    priority = Column(String(20), default="NORMAL", nullable=False, index=True)
    tags = Column(String(255), nullable=True)  # Use String if not JSON
    user_message = Column(Text, nullable=True)
    bot_response = Column(Text, nullable=True)

    # Full details from the original Kafka event
    details = Column(JSON, nullable=True)

    # False positive tracking
    is_false_positive = Column(Boolean, default=False, nullable=False)
    false_positive_reason = Column(Text, nullable=True)
    false_positive_reported_by = Column(String(50), nullable=True)
    false_positive_reported_at = Column(DateTime(timezone=True), nullable=True)

    # Learning and improvement
    feedback_score = Column(Float, nullable=True)  # User feedback on detection quality
    feedback_notes = Column(Text, nullable=True)
    model_learning_data = Column(JSON, nullable=True)  # Data for model improvement

    # Metadata
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    event_metadata = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("ConversationSession", back_populates="events")

    # Indexes for performance
    __table_args__ = (
        Index("idx_event_conversation", "conversation_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_event_severity", "severity"),
        Index("idx_event_status", "status"),
        Index("idx_event_detected", "created_at"),
        Index("idx_event_confidence", "confidence_score"),
        Index("idx_event_false_positive", "is_false_positive"),
        Index("idx_event_conversation_type", "conversation_id", "event_type"),
        Index("idx_event_severity_status", "severity", "status"),
        Index("idx_event_priority", "priority"),
    )

    def is_critical(self):
        """Check if event is critical"""
        return self.severity in ["CRITICAL", "critical"]

    def is_high_confidence(self):
        """Check if event has high confidence score"""
        return self.confidence_score and self.confidence_score >= 0.8

    def is_reviewed(self):
        """Check if event has been reviewed"""
        return self.status in ["ACKNOWLEDGED", "RESOLVED"]

    def is_false_positive_confirmed(self):
        """Check if event is confirmed as false positive"""
        return self.is_false_positive and self.false_positive_reported_at is not None

    def mark_as_false_positive(self, user_id, reason=None):
        """Mark event as false positive"""
        self.is_false_positive = True
        self.false_positive_reason = reason
        self.false_positive_reported_by = user_id
        self.false_positive_reported_at = datetime.now(timezone.utc)
        self.status = "RESOLVED"

    def review(self, user_id, action_taken=None, notes=None):
        """Mark event as reviewed"""
        self.status = "ACKNOWLEDGED"
        self.reviewed_by = user_id
        self.reviewed_at = datetime.now(timezone.utc)
        if action_taken:
            self.action_taken = action_taken
        if notes:
            self.action_notes = notes

    def acknowledge(self, user_id):
        """Acknowledge the event"""
        self.status = "ACKNOWLEDGED"
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now(timezone.utc)
        self.reviewed_by = user_id  # Also set reviewer
        self.reviewed_at = self.acknowledged_at
        if self.created_at is not None:
            delta = self.acknowledged_at - self.created_at
            self.response_time_minutes = int(delta.total_seconds() / 60)

    def resolve(self, user_id, notes=None, action=None):
        """Resolve the event"""
        self.status = "RESOLVED"
        self.resolved_by = user_id
        self.resolved_at = datetime.now(timezone.utc)
        self.reviewed_by = user_id  # Also set reviewer
        self.reviewed_at = self.resolved_at
        if notes:
            self.resolution_notes = notes
        if action:
            self.action_taken = action

    def get_risk_level(self):
        """Get risk level based on severity and confidence"""
        # Extract values to avoid SQLAlchemy Column type issues in conditionals
        severity_val: str = str(self.severity) if self.severity is not None else ""  # type: ignore
        confidence_val: float = float(self.confidence_score) if self.confidence_score is not None else 0.0  # type: ignore

        severity_str = severity_val.upper()
        confidence = confidence_val

        # Check conditions explicitly to avoid ColumnElement boolean issues
        if severity_str == "CRITICAL":
            if confidence >= 0.8:
                return "CRITICAL"
        elif severity_str == "HIGH":
            if confidence >= 0.7:
                return "HIGH"
        elif severity_str == "MEDIUM":
            if confidence >= 0.6:
                return "MEDIUM"

        return "LOW"

    def to_dict(self):
        """Helper to serialize model"""
        return self.to_dict_serialized()

    def to_dict_with_context(self):
        """Convert to dictionary with conversation context"""
        data = self.to_dict_serialized()

        # Add conversation context if available
        if self.details is not None and isinstance(self.details, dict):
            if "context" in self.details:
                data["context"] = self.details["context"]

        # Add risk level
        data["risk_level"] = self.get_risk_level()

        return data

    def __repr__(self):
        return f"<GuardrailEvent(id='{self.id}', event_id='{self.event_id}', type='{self.event_type}', severity='{self.severity}')>"

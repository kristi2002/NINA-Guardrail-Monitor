#!/usr/bin/env python3
"""
Conversation Model
Handles conversation sessions and patient information
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
)
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime, timezone


class ConversationSession(BaseModel):
    """Conversation session between patient and NINA chatbot"""

    __tablename__ = "conversation_sessions"

    # --- MODIFIED: Override id to use String as primary key ---
    id = Column(
        String(50), primary_key=True, index=True
    )  # Use the string session_id as the PK

    patient_id = Column(
        String(50), nullable=True, index=True
    )  # Allow NULL for backward compatibility

    # Session timing
    session_start = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    session_end = Column(DateTime(timezone=True), nullable=True)
    session_duration_minutes = Column(Integer, nullable=True)

    # Session status
    status = Column(
        String(20), default="ACTIVE", nullable=False, index=True
    )  # ACTIVE, COMPLETED, TERMINATED, ESCALATED

    # Conversation metrics
    total_messages = Column(Integer, default=0, nullable=False)
    guardrail_violations = Column(Integer, default=0, nullable=False)

    # --- ADDED COLUMNS (Replaced @property) ---
    patient_info = Column(JSON, nullable=True)
    risk_level = Column(
        String(20), default="LOW", nullable=False, index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL
    situation = Column(
        String(255), nullable=True
    )  # Renamed from 'title' in some services
    is_monitored = Column(Boolean, default=True, nullable=False)
    requires_attention = Column(Boolean, default=False, nullable=False, index=True)
    escalated = Column(Boolean, default=False, nullable=False, index=True)
    sentiment_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    satisfaction_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    session_metadata = Column(JSON, nullable=True)

    # Properties for backward compatibility
    @property
    def session_id(self):
        """Map session_id to id for backward compatibility"""
        return self.id

    # Helper properties for patient info access
    @property
    def patient_name(self):
        """Patient name (from patient_info or default)"""
        if self.patient_info is not None and isinstance(self.patient_info, dict):
            return self.patient_info.get("name", f"Patient {self.patient_id}")
        return f"Patient {self.patient_id}"

    @property
    def patient_age(self):
        """Patient age (from patient_info or default)"""
        if self.patient_info is not None and isinstance(self.patient_info, dict):
            return self.patient_info.get("age", 0)
        return 0

    @property
    def patient_gender(self):
        """Patient gender (from patient_info or default)"""
        if self.patient_info is not None and isinstance(self.patient_info, dict):
            return self.patient_info.get("gender", "U")
        return "U"

    @property
    def patient_pathology(self):
        """Patient pathology (from patient_info or default)"""
        if self.patient_info is not None and isinstance(self.patient_info, dict):
            return self.patient_info.get("pathology", "Unknown")
        return "Unknown"

    @property
    def situation_level(self):
        """Situation level (derived from risk_level)"""
        risk_to_level = {
            "LOW": "low",
            "MEDIUM": "medium",
            "HIGH": "high",
            "CRITICAL": "critical",
        }
        risk_level_val: str = str(self.risk_level) if self.risk_level is not None else "LOW"  # type: ignore
        return risk_to_level.get(risk_level_val, "low")

    # Relationships
    events = relationship("GuardrailEvent", back_populates="conversation")
    messages = relationship("ChatMessage", back_populates="conversation")
    actions = relationship("OperatorAction", back_populates="conversation")

    # Indexes for performance
    __table_args__ = (
        Index("idx_conversation_patient", "patient_id"),
        Index("idx_conversation_status", "status"),
        Index("idx_conversation_start", "session_start"),
        Index("idx_conversation_patient_status", "patient_id", "status"),
        Index("idx_conversation_risk_level", "risk_level"),
        Index("idx_conversation_requires_attention", "requires_attention"),
    )

    def get_duration_minutes(self):
        """Calculate session duration in minutes"""
        if self.session_end is not None and self.session_start is not None:
            delta = self.session_end - self.session_start
            return int(delta.total_seconds() / 60)
        return None

    def is_active(self):
        """Check if session is currently active"""
        return self.status == "ACTIVE" and self.session_end is None

    def is_high_risk(self):
        """Check if session is high risk"""
        risk_level_val: str = str(self.risk_level) if self.risk_level is not None else ""  # type: ignore
        return risk_level_val in ["HIGH", "CRITICAL"]

    def needs_attention(self):
        """Check if session needs operator attention"""
        return (
            self.requires_attention
            or self.guardrail_violations > 0
            or self.is_high_risk()
        )

    def to_dict_with_patient(self):
        """Convert to dictionary with patient information"""
        data = self.to_dict_serialized()

        # Add patient information if available
        if self.patient_info is not None:
            data["patientInfo"] = self.patient_info
        else:
            # Fallback patient info
            data["patientInfo"] = {
                "name": f"Paziente {self.patient_id}",
                "age": 45,
                "gender": "M",
                "pathology": "Non specificata",
            }

        return data

    def __repr__(self):
        return f"<ConversationSession(id='{self.session_id}', patient='{self.patient_id}', status='{self.status}')>"

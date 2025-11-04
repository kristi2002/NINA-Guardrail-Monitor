#!/usr/bin/env python3
"""
Guardrail Event Repository
Handles guardrail event-specific database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import and_, or_, desc, asc, func # type: ignore
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from models.guardrail_event import GuardrailEvent # type: ignore
import logging

logger = logging.getLogger(__name__)

class GuardrailEventRepository(BaseRepository):
    """Repository for GuardrailEvent model with event-specific operations"""
    
    def __init__(self, db: Session): # type: ignore
        super().__init__(db, GuardrailEvent)
    
    def get_by_event_id(self, event_id: str) -> Optional[GuardrailEvent]: 
        """Get event by event_id"""
        return self.get_by_field('event_id', event_id)
    
    def get_by_conversation_id(self, conversation_id: str, limit: int = 100) -> List[GuardrailEvent]: 
        """Get events by conversation ID"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.conversation_id == conversation_id,
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting events for conversation {conversation_id}: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            raise
    
    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[GuardrailEvent]: 
        """Get events by event type"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.event_type == event_type,
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting events by type {event_type}: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            raise
    
    def get_by_severity(self, severity: str, limit: int = 100) -> List[GuardrailEvent]: 
        """Get events by severity"""
        try:
            events = self.db.query(GuardrailEvent).filter(
                GuardrailEvent.severity.in_([severity.upper(), severity.lower(), severity.capitalize()]),
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
            return events
        except Exception as e:
            logger.error(f"Error getting events by severity {severity}: {e}")
            # Rollback failed transaction to prevent "InFailedSqlTransaction" errors
            try:
                self.db.rollback()
            except Exception:
                pass  # Ignore rollback errors
            return []  # Return empty list instead of raising
    
    def get_high_confidence_events(self, confidence_threshold: float = 0.8, limit: int = 100) -> List[GuardrailEvent]:
        """Get high confidence events"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.confidence_score >= confidence_threshold,
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting high confidence events: {e}")
            raise
    
    def get_false_positives(self, limit: int = 100) -> List[GuardrailEvent]:
        """Get false positive events"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.is_false_positive == True,
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting false positive events: {e}")
            raise
    
    def get_unreviewed_events(self, limit: int = 100) -> List[GuardrailEvent]:
        """Get unreviewed events"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.status == 'PENDING',
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting unreviewed events: {e}")
            raise
    
    def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[GuardrailEvent]:
        """Get recent events"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).order_by(desc(GuardrailEvent.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            return []  # Return empty list instead of raising
    
    def mark_as_false_positive(self, event_id: str, user_id: str, reason: str = None) -> Optional[GuardrailEvent]:
        """Mark event as false positive"""
        try:
            event = self.get_by_event_id(event_id)
            if not event:
                return None
            
            event.mark_as_false_positive(user_id, reason)
            self.db.commit()
            self.db.refresh(event)
            
            logger.info(f"Event {event_id} marked as false positive by {user_id}")
            return event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking event {event_id} as false positive: {e}")
            raise
    
    def review_event(self, event_id: str, user_id: str, action_taken: str = None, notes: str = None) -> Optional[GuardrailEvent]:
        """Review an event"""
        try:
            event = self.get_by_event_id(event_id)
            if not event:
                return None
            
            event.review(user_id, action_taken, notes)
            self.db.commit()
            self.db.refresh(event)
            
            logger.info(f"Event {event_id} reviewed by {user_id}")
            return event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reviewing event {event_id}: {e}")
            raise
    
    def acknowledge_event(self, event_id: str, user_id: str) -> Optional[GuardrailEvent]:
        """Acknowledge an event"""
        try:
            event = self.get_by_event_id(event_id)
            if not event:
                return None
            
            event.acknowledge(user_id)
            self.db.commit()
            self.db.refresh(event)
            
            logger.info(f"Event {event_id} acknowledged by {user_id}")
            return event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error acknowledging event {event_id}: {e}")
            raise
    
    def get_event_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get event statistics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Total events - use func.count to avoid loading all columns
            total_events = self.db.query(func.count(GuardrailEvent.id)).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).scalar() or 0
            
            # Events by type
            type_stats = self.db.query(
                GuardrailEvent.event_type,
                func.count(GuardrailEvent.id).label('count')
            ).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).group_by(GuardrailEvent.event_type).all()
            
            # Events by severity
            severity_stats = self.db.query(
                GuardrailEvent.severity,
                func.count(GuardrailEvent.id).label('count')
            ).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).group_by(GuardrailEvent.severity).all()
            
            # Events by status
            status_stats = self.db.query(
                GuardrailEvent.status,
                func.count(GuardrailEvent.id).label('count')
            ).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).group_by(GuardrailEvent.status).all()
            
            # False positive rate - use func.count to avoid loading all columns
            false_positives = self.db.query(func.count(GuardrailEvent.id)).filter(
                GuardrailEvent.is_false_positive == True,
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).scalar() or 0
            
            false_positive_rate = (false_positives / total_events) if total_events > 0 else 0
            
            # Average confidence score
            avg_confidence = self.db.query(
                func.avg(GuardrailEvent.confidence_score)
            ).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.is_deleted.is_(False)
            ).scalar()
            
            return {
                'total_events': total_events,
                'false_positives': false_positives,
                'false_positive_rate': false_positive_rate,
                'average_confidence_score': float(avg_confidence) if avg_confidence else 0,
                'type_distribution': {stat.event_type: stat.count for stat in type_stats},
                'severity_distribution': {stat.severity: stat.count for stat in severity_stats},
                'status_distribution': {stat.status: stat.count for stat in status_stats},
                'time_range_hours': hours,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            raise

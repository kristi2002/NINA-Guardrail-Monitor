#!/usr/bin/env python3
"""
Alert Service
Handles business logic for alert management
READS FROM GUARDRAIL_EVENT MODEL
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import func # type: ignore
from datetime import datetime, timedelta
from .base_service import BaseService
# from repositories.alert_repository import AlertRepository # No longer used
# from models.alert import Alert # No longer used
from models.guardrail_event import GuardrailEvent # <-- IMPORT NEW MODEL
from models.conversation import ConversationSession # <-- Import for joins
import logging

logger = logging.getLogger(__name__)

class AlertService(BaseService):
    """Service for alert business logic (reads from GuardrailEvent)"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        # We query the model directly, no repository needed for this.
        self.db = self.get_session()

    def get_by_id(self, event_id: int) -> Optional[GuardrailEvent]:
        """Get guardrail event by its database ID"""
        try:
            return self.db.query(GuardrailEvent).filter(GuardrailEvent.id == event_id).first()
        except Exception as e:
            self.logger.error(f"Error getting event {event_id}: {e}")
            return None
    
    def get_by_event_id_str(self, event_id_str: str) -> Optional[GuardrailEvent]:
        """Get guardrail event by its string event_id"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.event_id == event_id_str
            ).first()
        except Exception as e:
            self.logger.error(f"Error getting event by string ID {event_id_str}: {e}")
            return None

    def get_active_alerts(self, limit: int = 100) -> List[GuardrailEvent]:
        """Get all active alerts (PENDING status)"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.status == 'PENDING',
                GuardrailEvent.severity.in_(['CRITICAL', 'critical', 'HIGH', 'high'])
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []
    
    def get_critical_alerts(self, limit: int = 100) -> List[GuardrailEvent]:
        """Get all critical alerts"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.severity.in_(['CRITICAL', 'critical']),
                GuardrailEvent.status == 'PENDING'
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting critical alerts: {e}")
            return []
    
    def get_alerts_by_severity(self, severity: str, limit: int = 100) -> List[GuardrailEvent]:
        """Get alerts by severity level"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.severity == severity.upper()
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting alerts by severity {severity}: {e}")
            return []
    
    def get_alerts_by_status(self, status: str, limit: int = 100) -> List[GuardrailEvent]:
        """Get alerts by status"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.status == status.lower()
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting alerts by status {status}: {e}")
            return []
    
    def get_recent_alerts(self, hours: int = 24, limit: int = 100) -> List[GuardrailEvent]:
        """Get recent alerts"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.created_at >= cutoff_time
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def get_alerts_needing_attention(self, limit: int = 100) -> List[GuardrailEvent]:
        """Get alerts that need attention (PENDING or ESCALATED status)"""
        try:
            return self.db.query(GuardrailEvent).filter(
                GuardrailEvent.status.in_(['PENDING', 'ESCALATED'])
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"Error getting alerts needing attention: {e}")
            return []
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creating alerts via API is not supported. Events are ingested from Kafka."""
        self.logger.warning("Attempted to create alert via API. This is not supported.")
        return self.format_response(
            success=False,
            message="Alerts cannot be created via API. They are ingested from the Kafka guardrail_events topic."
        )
    
    def update(self, event_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a guardrail event (e.g., its status)"""
        try:
            event = self.get_by_id(event_id)
            if not event:
                return self.format_response(success=False, message="Alert not found")
            
            sanitized_data = self.sanitize_input(data)
            
            # Only allow updating specific fields
            allowed_fields = ['status', 'action_notes']
            updated_fields = []
            
            for field in allowed_fields:
                if field in sanitized_data:
                    setattr(event, field, sanitized_data[field])
                    updated_fields.append(field)
            
            if updated_fields:
                event.last_updated_at = datetime.utcnow()
                self.db.commit()
                self.log_operation('alert_updated', details={
                    'event_id': event_id,
                    'updated_fields': updated_fields
                })

            return self.format_response(
                success=True,
                data=event.to_dict(),
                message="Alert updated successfully"
            )
            
        except Exception as e:
            self.db.rollback()
            return self.handle_exception(e, 'update_alert')
    
    def delete(self, event_id: int) -> Dict[str, Any]:
        """Delete alert (hard delete)"""
        try:
            event = self.get_by_id(event_id)
            if not event:
                return self.format_response(success=False, message="Alert not found")
            
            self.db.delete(event)
            self.db.commit()
            
            self.log_operation('alert_deleted', details={'event_id': event_id})
            
            return self.format_response(
                success=True,
                message="Alert deleted successfully"
            )
            
        except Exception as e:
            self.db.rollback()
            return self.handle_exception(e, 'delete_alert')
    
    def acknowledge_alert(self, event_id: int, operator_id: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        try:
            event = self.get_by_id(event_id)
            if not event:
                return self.format_response(success=False, message="Alert not found")
            
            if event.status == 'dismissed':
                return self.format_response(success=False, message=f"Alert is already dismissed")
            
            # Use the model's acknowledge method
            event.acknowledge(operator_id)
            event.last_updated_at = datetime.utcnow()
            
            self.db.commit()
            
            self.log_operation('alert_acknowledged', operator_id, {
                'event_id': event_id,
                'event_id_str': event.event_id
            })
            
            return self.format_response(
                success=True,
                data=event.to_dict(),
                message="Alert acknowledged successfully"
            )
            
        except Exception as e:
            self.db.rollback()
            return self.handle_exception(e, 'acknowledge_alert', operator_id)
    
    def resolve_alert(self, event_id: int, operator_id: str, notes: str = None, action: str = None) -> Dict[str, Any]:
        """Resolve an alert"""
        try:
            event = self.get_by_id(event_id)
            if not event:
                return self.format_response(success=False, message="Alert not found")

            # Use the model's resolve method
            event.resolve(operator_id, notes=notes, action=action)
            event.last_updated_at = datetime.utcnow()
            
            self.db.commit()
            
            self.log_operation('alert_resolved', operator_id, {
                'event_id': event_id,
                'event_id_str': event.event_id,
                'action': action
            })
            
            return self.format_response(
                success=True,
                data=event.to_dict(),
                message="Alert resolved successfully"
            )
            
        except Exception as e:
            self.db.rollback()
            return self.handle_exception(e, 'resolve_alert', operator_id)
    
    def escalate_alert(self, event_id: int, level: int = 1) -> Dict[str, Any]:
        """Escalate an alert"""
        try:
            event = self.get_by_id(event_id)
            if not event:
                return self.format_response(success=False, message="Alert not found")
            
            # Update action_taken to indicate escalation
            event.action_taken = f'escalated_level_{level}'
            event.action_notes = f"Escalated to level {level}"
            event.last_updated_at = datetime.utcnow()
            
            self.db.commit()
            
            self.log_operation('alert_escalated', details={
                'event_id': event_id,
                'event_id_str': event.event_id,
                'escalation_level': level
            })
            
            return self.format_response(
                success=True,
                data=event.to_dict(),
                message="Alert escalated successfully"
            )
            
        except Exception as e:
            self.db.rollback()
            return self.handle_exception(e, 'escalate_alert')
    
    def get_alert_statistics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Get alert statistics from GuardrailEvent"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_query = self.db.query(GuardrailEvent).filter(
                GuardrailEvent.created_at >= cutoff_time
            )
            
            total_alerts = base_query.count()
            critical_alerts = base_query.filter(
                GuardrailEvent.severity.in_(['CRITICAL', 'critical'])
            ).count()
            active_alerts = base_query.filter(
                GuardrailEvent.status == 'PENDING'
            ).count()
            
            severity_dist = base_query.with_entities(
                GuardrailEvent.severity, func.count(GuardrailEvent.id)
            ).group_by(GuardrailEvent.severity).all()
            
            status_dist = base_query.with_entities(
                GuardrailEvent.status, func.count(GuardrailEvent.id)
            ).group_by(GuardrailEvent.status).all()
            
            stats = {
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'active_alerts': active_alerts,
                'severity_distribution': {s: c for s, c in severity_dist},
                'status_distribution': {s: c for s, c in status_dist},
            }
            
            self.log_operation('alert_statistics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=stats,
                message="Alert statistics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_alert_statistics')
    
    def get_response_time_metrics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Get response time metrics from GuardrailEvent"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            base_query = self.db.query(GuardrailEvent).filter(
                GuardrailEvent.created_at >= cutoff_time,
                GuardrailEvent.reviewed_at.isnot(None)
            )
            
            # Calculate average response time (reviewed_at - created_at)
            avg_response_query = base_query.with_entities(
                func.avg(func.extract('epoch', GuardrailEvent.reviewed_at - GuardrailEvent.created_at) / 60)
            ).scalar()
            
            avg_response_time_minutes = float(avg_response_query) if avg_response_query else 0
            
            # Response time by severity
            response_by_severity = base_query.with_entities(
                GuardrailEvent.severity,
                func.avg(func.extract('epoch', GuardrailEvent.reviewed_at - GuardrailEvent.created_at) / 60)
            ).group_by(GuardrailEvent.severity).all()
            
            metrics = {
                'average_response_time_minutes': avg_response_time_minutes,
                'response_time_by_severity': {s: float(c) for s, c in response_by_severity}
            }
            
            self.log_operation('response_time_metrics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=metrics,
                message="Response time metrics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_response_time_metrics')
    
    def acknowledge_multiple_alerts(self, event_ids: List[int], operator_id: str) -> Dict[str, Any]:
        """Acknowledge multiple alerts"""
        try:
            results = []
            successful = 0
            failed = 0
            
            for event_id in event_ids:
                result = self.acknowledge_alert(event_id, operator_id)
                results.append({
                    'event_id': event_id,
                    'success': result['success'],
                    'message': result.get('message', '')
                })
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
            
            self.log_operation('multiple_alerts_acknowledged', operator_id, {
                'total_alerts': len(event_ids),
                'successful': successful,
                'failed': failed
            })
            
            return self.format_response(
                success=True,
                data={
                    'results': results,
                    'summary': {
                        'total': len(event_ids),
                        'successful': successful,
                        'failed': failed
                    }
                },
                message=f"Acknowledged {successful} out of {len(event_ids)} alerts"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'acknowledge_multiple_alerts', operator_id)
    
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
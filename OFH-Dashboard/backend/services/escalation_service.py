"""
Auto-Escalation Service for OFH Dashboard
Automatically escalates alerts based on time and priority
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class EscalationRule:
    """Represents an escalation rule"""

    def __init__(self, severity: str, escalate_after_minutes: int, notification_methods: List[str]):
        self.severity = severity
        self.escalate_after_minutes = escalate_after_minutes
        self.notification_methods = notification_methods


class AutoEscalationService:
    """Service for automatically escalating unacknowledged alerts"""

    def __init__(self, app=None, db=None, socketio=None, alert_notification_service=None, models=None):
        self.app = app
        self.db = db
        self.socketio = socketio
        self.alert_notification_service = alert_notification_service
        self.models = models
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
        self.thread = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Escalation rules by severity
        self.escalation_rules = {
            'CRITICAL': EscalationRule('CRITICAL', 5, ['phone', 'sms', 'email']),
            'HIGH': EscalationRule('HIGH', 15, ['phone', 'email']),
            'MEDIUM': EscalationRule('MEDIUM', 30, ['email']),
            'LOW': EscalationRule('LOW', 60, ['email'])
        }

    def start(self):
        """Start the escalation service in background thread"""
        if self.running:
            self.logger.warning("Service already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.logger.info("Auto-escalation service started")

    def stop(self):
        """Stop the escalation service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Auto-escalation service stopped")

    def _run(self):
        """Main escalation loop"""
        while self.running:
            try:
                self._check_and_escalate_alerts()
            except Exception as e:
                self.logger.error(f"Escalation service error: {e}", exc_info=True)

            # Sleep but check running flag periodically
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_and_escalate_alerts(self):
        """Check for alerts that need escalation"""
        if not self.app or not self.db:
            return

        with self.app.app_context():
            GuardrailEvent = self.models['GuardrailEvent']
            OperatorAction = self.models['OperatorAction']

            # Find alerts that need escalation
            now = datetime.utcnow()

            for severity, rule in self.escalation_rules.items():
                # Calculate cutoff time
                cutoff_time = now - \
                    timedelta(minutes=rule.escalate_after_minutes)

                # Find unacknowledged alerts older than cutoff
                alerts_to_escalate = GuardrailEvent.query.filter(
                    GuardrailEvent.severity == severity,
                    GuardrailEvent.status.in_(['PENDING', 'IN_PROGRESS']),
                    GuardrailEvent.created_at <= cutoff_time,
                    GuardrailEvent.escalated_at.is_(
                        None)  # Not already escalated
                ).all()

                for alert in alerts_to_escalate:
                    self._escalate_alert(alert, rule)

    def _escalate_alert(self, alert, rule: EscalationRule):
        """Escalate a specific alert"""
        try:
            self.logger.info(f"Auto-escalating alert {alert.id} ({alert.severity})")
            
            # TEMPORARY SOLUTION: Log escalation without database persistence
            # This avoids the persistent database schema issue
            escalation_message = f'Alert auto-escalated after {rule.escalate_after_minutes} minutes without acknowledgment'
            self.logger.info(f"{escalation_message}")
            
            # Update alert status and commit to database
            alert.status = 'ESCALATED'
            alert.escalated_to = 'Supervisor'
            alert.escalated_at = datetime.utcnow()
            alert.last_updated_by = 'SYSTEM_AUTO_ESCALATION'
            alert.last_updated_at = datetime.utcnow()
            
            # Commit the changes to prevent infinite escalation loop
            self.db.session.commit()
            
            # Log the escalation action (without database persistence)
            self.logger.info(f"Action logged: ESCALATE for conversation {alert.conversation_id}")
            self.logger.info(f"Details: {escalation_message}")
            self.logger.info(f"Severity: {alert.severity}")

            # Send escalation notifications
            if self.alert_notification_service and hasattr(self.alert_notification_service, 'send_email'):
                try:
                    from core.config_helper import ConfigHelper
                    supervisor_email = ConfigHelper.get_supervisor_email()
                    
                    alert_data = alert.to_dict()  # Get updated alert data
                    
                    # Create escalation email
                    subject = f"ESCALATED ALERT: {alert_data.get('type', 'Alert')} - {alert_data.get('severity', 'UNKNOWN')}"
                    body = f"""
ALERT ESCALATION REQUIRED

Alert ID: {alert_data.get('id')}
Type: {alert_data.get('type')}
Severity: {alert_data.get('severity')}
Status: {alert_data.get('status')}
Escalated By: SYSTEM_AUTO_ESCALATION

Message: {alert_data.get('message', '')}

This alert requires supervisor attention.

Dashboard: http://localhost:5173

Best regards,
OFH Dashboard Team
"""
                    
                    # Send email notification
                    self.alert_notification_service.send_email(
                        supervisor_email, subject, body)
                    self.logger.info(f"Email notification sent for alert {alert.id}")
                except Exception as notify_error:
                    self.logger.error(f"Failed to send escalation notification: {notify_error}")
            else:
                self.logger.warning(f"Notification service not available for alert {alert.id}")

            # Broadcast via WebSocket
            if self.socketio:
                # Send the whole updated alert
                self.socketio.emit('alert_updated', {'alert': alert.to_dict()})
                # Optionally send a specific escalation event too
                self.socketio.emit('alert_escalated', {
                    'alert_id': alert.id,
                    'severity': alert.severity,
                    'escalated_by': 'SYSTEM_AUTO_ESCALATION',
                    'escalated_at': alert.escalated_at.isoformat(),
                    'reason': escalation_message
                })

            self.logger.info(f"Successfully escalated alert {alert.id}")

        except Exception as e:
            self.logger.error(f"Escalation service error: {e}", exc_info=True)
            try:
                self.db.session.rollback()  # Roll back DB changes on error
            except Exception as rollback_error:
                self.logger.error(f"Failed to rollback session: {rollback_error}")
                # Force session cleanup
                self.db.session.close()
                self.db.session.remove()

    def get_status(self) -> Dict:
        """Get escalation service status"""
        return {
            'running': self.running,
            'check_interval_seconds': self.check_interval,
            'rules': {
                severity: {
                    'escalate_after_minutes': rule.escalate_after_minutes,
                    'notification_methods': rule.notification_methods
                }
                for severity, rule in self.escalation_rules.items()
            }
        }

    def update_rule(self, severity: str, escalate_after_minutes: int, notification_methods: List[str]):
        """Update an escalation rule"""
        if severity in self.escalation_rules:
            self.escalation_rules[severity] = EscalationRule(
                severity, escalate_after_minutes, notification_methods
            )
            print(
                f"[ESCALATION] Updated rule for {severity}: {escalate_after_minutes} minutes")
            return True
        return False


# Global escalation service instance (will be initialized in app.py)
auto_escalation_service = None

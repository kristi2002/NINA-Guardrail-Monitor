#!/usr/bin/env python3
"""
Notification Orchestrator
Main service that coordinates all notification features
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from services.base_service import BaseService
from services.notifications.enhanced_notification_service import EnhancedNotificationService
from services.notifications.notification_digest_service import NotificationDigestService
from services.notifications.notification_escalation_service import NotificationEscalationService
from services.notifications.notification_template_service import NotificationTemplateService
from repositories.notifications.notification_rule_repository import NotificationRuleRepository
from repositories.notifications.notification_group_repository import NotificationGroupRepository
from repositories.user_repository import UserRepository
from models.notifications.notification import NotificationType, NotificationPriority, NotificationChannel
from models.notifications.notification_rule import RuleAction
import logging

logger = logging.getLogger(__name__)


class NotificationOrchestrator(BaseService):
    """Main orchestrator for all notification features"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.notification_service = EnhancedNotificationService(self.get_session())
        self.digest_service = NotificationDigestService(self.get_session())
        self.escalation_service = NotificationEscalationService(self.get_session())
        self.template_service = NotificationTemplateService()
        self.rule_repo = NotificationRuleRepository(self.get_session())
        self.group_repo = NotificationGroupRepository(self.get_session())
        self.user_repo = UserRepository(self.get_session())
    
    def send_alert_notification(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        recipients: Optional[List[int]] = None,
        recipient_groups: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send alert notification with full orchestration"""
        try:
            # Determine recipients
            user_ids = self._determine_recipients(recipients, recipient_groups, alert_data)
            
            if not user_ids:
                return self.format_response(
                    success=False,
                    message="No recipients found"
                )
            
            # Evaluate notification rules
            context = self._build_alert_context(alert_id, alert_data)
            matching_rules = self.rule_repo.get_matching_rules(context)
            
            # Determine notification parameters
            priority = self._determine_priority(alert_data.get('severity', 'normal'))
            notification_type = NotificationType.ALERT
            
            # Check if any rule says to suppress
            for rule in matching_rules:
                if rule.action == RuleAction.SUPPRESS:
                    return self.format_response(
                        success=True,
                        message="Notification suppressed by rule"
                    )
            
            # Check if digest is required
            use_digest = False
            for rule in matching_rules:
                if rule.action == RuleAction.SEND_DIGEST:
                    use_digest = True
                    break
            
            # Get template
            template_name = self._get_template_name(priority, alert_data)
            template_vars = self._build_template_variables(alert_id, alert_data)
            rendered = self.template_service.render_template(template_name, template_vars)
            
            # Send notifications
            results = []
            for user_id in user_ids:
                if use_digest:
                    # Queue for digest
                    result = self.notification_service.create_notification(
                        user_id=user_id,
                        title=rendered['subject'],
                        message=rendered['text'],
                        notification_type=notification_type,
                        priority=priority,
                        channel=NotificationChannel.IN_APP,
                        alert_id=alert_id,
                        html_content=rendered.get('html')
                    )
                    results.append({'user_id': user_id, 'status': 'queued_for_digest', 'notification_id': result.id})
                else:
                    # Send immediately
                    result = self.notification_service.send_notification(
                        user_id=user_id,
                        title=rendered['subject'],
                        message=rendered['text'],
                        notification_type=notification_type,
                        priority=priority,
                        html_content=rendered.get('html'),
                        alert_id=alert_id,
                        notification_metadata={'alert_id': alert_id, 'severity': alert_data.get('severity')}
                    )
                    results.append({'user_id': user_id, 'result': result})
            
            # Update rule trigger counts
            for rule in matching_rules:
                self.rule_repo.increment_trigger_count(rule.id)
            
            return self.format_response(
                success=True,
                data={
                    'recipients_count': len(user_ids),
                    'results': results,
                    'rules_matched': len(matching_rules),
                    'digest_mode': use_digest
                },
                message=f"Alert notification sent to {len(user_ids)} recipient(s)"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'send_alert_notification')
    
    def send_conversation_notification(
        self,
        conversation_id: str,
        conversation_data: Dict[str, Any],
        recipients: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Send conversation notification"""
        try:
            if not recipients:
                # Get all active admins
                admins = self.user_repo.get_by_filters({'is_active': True, 'role': 'admin'})
                recipients = [admin.id for admin in admins]
            
            priority = self._determine_priority_from_risk(conversation_data.get('risk_level', 'normal'))
            
            template_vars = {
                'conversation_id': conversation_id,
                'patient_id': conversation_data.get('patient_id', 'Unknown'),
                'status': conversation_data.get('status', 'Unknown'),
                'risk_level': conversation_data.get('risk_level', 'normal'),
                'message': conversation_data.get('message', 'Conversation update'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            rendered = self.template_service.render_template('conversation_update', template_vars)
            
            results = []
            for user_id in recipients:
                result = self.notification_service.send_notification(
                    user_id=user_id,
                    title=rendered['subject'],
                    message=rendered['text'],
                    notification_type=NotificationType.CONVERSATION,
                    priority=priority,
                    html_content=rendered.get('html'),
                    conversation_id=conversation_id,
                    notification_metadata={'conversation_id': conversation_id, 'risk_level': conversation_data.get('risk_level')}
                )
                results.append({'user_id': user_id, 'result': result})
            
            return self.format_response(
                success=True,
                data={
                    'recipients_count': len(recipients),
                    'results': results
                },
                message=f"Conversation notification sent to {len(recipients)} recipient(s)"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'send_conversation_notification')
    
    def process_digests(self) -> Dict[str, Any]:
        """Process all pending digest notifications"""
        return self.digest_service.process_digest_queue()
    
    def process_escalations(self, escalation_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process all pending escalations"""
        return self.escalation_service.process_escalations(escalation_policies)
    
    def retry_failed_notifications(self, max_retries: int = 10) -> Dict[str, Any]:
        """Retry failed notifications"""
        return self.notification_service.retry_failed_notifications(max_retries)
    
    # ============================================
    # Helper Methods
    # ============================================
    
    def _determine_recipients(
        self,
        recipients: Optional[List[int]],
        recipient_groups: Optional[List[str]],
        context: Dict[str, Any]
    ) -> List[int]:
        """Determine notification recipients"""
        user_ids = set()
        
        # Direct recipients
        if recipients:
            user_ids.update(recipients)
        
        # Group recipients
        if recipient_groups:
            for group_name in recipient_groups:
                group = self.group_repo.get_by_name(group_name)
                if group:
                    user_ids.update(group.get_member_ids())
        
        # Default: all admins if no recipients specified
        if not user_ids:
            admins = self.user_repo.get_by_filters({'is_active': True, 'role': 'admin'})
            user_ids.update([admin.id for admin in admins])
        
        return list(user_ids)
    
    def _build_alert_context(self, alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for rule evaluation"""
        return {
            'alert_severity': alert_data.get('severity', 'normal'),
            'alert_type': alert_data.get('event_type', 'unknown'),
            'time_of_day': datetime.now(timezone.utc).strftime('%H:%M'),
            'day_of_week': datetime.now(timezone.utc).strftime('%A').lower()
        }
    
    def _determine_priority(self, severity: str) -> NotificationPriority:
        """Determine notification priority from severity"""
        mapping = {
            'low': NotificationPriority.LOW,
            'normal': NotificationPriority.NORMAL,
            'medium': NotificationPriority.NORMAL,
            'high': NotificationPriority.HIGH,
            'critical': NotificationPriority.URGENT,
            'urgent': NotificationPriority.URGENT
        }
        return mapping.get(severity.lower(), NotificationPriority.NORMAL)
    
    def _determine_priority_from_risk(self, risk_level: str) -> NotificationPriority:
        """Determine notification priority from risk level"""
        return self._determine_priority(risk_level)
    
    def _get_template_name(self, priority: NotificationPriority, alert_data: Dict[str, Any]) -> str:
        """Get template name based on priority"""
        if priority == NotificationPriority.URGENT:
            return 'alert_critical'
        elif priority == NotificationPriority.HIGH:
            return 'alert_high'
        else:
            return 'system_notification'
    
    def _build_template_variables(self, alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build template variables from alert data"""
        return {
            'alert_id': alert_id,
            'alert_title': alert_data.get('title', 'Alert'),
            'severity': alert_data.get('severity', 'normal'),
            'message': alert_data.get('message', 'No message'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'conversation_id': alert_data.get('conversation_id', 'N/A'),
            'event_type': alert_data.get('event_type', 'unknown'),
            'action_button': self._build_action_button(alert_id) if alert_id else ''
        }
    
    def _build_action_button(self, alert_id: str) -> str:
        """Build HTML action button"""
        return f'<a href="/alerts/{alert_id}" class="button">View Alert</a>'


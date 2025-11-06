#!/usr/bin/env python3
"""
Notification Background Tasks
Scheduled tasks for digest processing, escalation checking, and retry logic
"""

from typing import Dict, Any
from datetime import datetime, timezone
from services.base_service import BaseService
from services.notifications.notification_digest_service import NotificationDigestService
from services.notifications.notification_escalation_service import NotificationEscalationService
from services.notifications.enhanced_notification_service import EnhancedNotificationService
import logging

logger = logging.getLogger(__name__)


class NotificationBackgroundTasks(BaseService):
    """Background tasks for notification system"""
    
    def __init__(self, db_session=None):
        super().__init__(db_session)
        self.digest_service = NotificationDigestService(self.get_session())
        self.escalation_service = NotificationEscalationService(self.get_session())
        self.notification_service = EnhancedNotificationService(self.get_session())
    
    def run_all_tasks(self) -> Dict[str, Any]:
        """Run all background notification tasks"""
        results = {
            'digests': {},
            'escalations': {},
            'retries': {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Process digests
            logger.info("Processing notification digests...")
            digest_result = self.digest_service.process_digest_queue()
            results['digests'] = digest_result.get('data', {})
            
        except Exception as e:
            logger.error(f"Error processing digests: {e}", exc_info=True)
            results['digests'] = {'error': str(e)}
        
        try:
            # Process escalations
            logger.info("Processing notification escalations...")
            # Default escalation policy
            escalation_policies = [{
                'enabled': True,
                'timeout_minutes': 15,
                'type': 'supervisor',
                'supervisor_email': None  # Will default to admin
            }]
            escalation_result = self.escalation_service.process_escalations(escalation_policies)
            results['escalations'] = escalation_result.get('data', {})
            
        except Exception as e:
            logger.error(f"Error processing escalations: {e}", exc_info=True)
            results['escalations'] = {'error': str(e)}
        
        try:
            # Retry failed notifications
            logger.info("Retrying failed notifications...")
            retry_result = self.notification_service.retry_failed_notifications(max_retries=10)
            results['retries'] = retry_result.get('data', {})
            
        except Exception as e:
            logger.error(f"Error retrying failed notifications: {e}", exc_info=True)
            results['retries'] = {'error': str(e)}
        
        return results


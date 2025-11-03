#!/usr/bin/env python3
"""
Error Alerting Service for NINA Guardrail Monitor
Handles critical error notifications and monitoring alerts
"""

import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, deque
from typing import Dict, List, Optional

class ErrorAlertingService:
    def __init__(self, config=None):
        """Initialize error alerting service"""
        self.config = config or self._get_default_config()
        self.alert_history = deque(maxlen=1000)  # Keep last 1000 alerts
        self.error_counts = defaultdict(int)
        self.alert_thresholds = {
            'critical_errors': 5,      # Alert after 5 critical errors
            'retry_failures': 10,      # Alert after 10 retry failures
            'dlq_messages': 20,       # Alert after 20 DLQ messages
            'connection_failures': 3   # Alert after 3 connection failures
        }
        
        # Setup logging (using centralized logging config)
        self.logger = logging.getLogger('error_alerts')
        
        # Initialize alert channels
        self._setup_alert_channels()
    
    def _get_default_config(self):
        """Get default configuration for alerting"""
        return {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': 'nina-alerts@company.com',
                'to_emails': ['admin@company.com']
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': '#nina-alerts'
            },
            'log_file': {
                'enabled': True,
                'file_path': 'logs/error_alerts.log'
            },
            'console': {
                'enabled': True
            }
        }
    
    def _setup_alert_channels(self):
        """Setup alert channels based on configuration"""
        # Log file handler is now managed by centralized logging config
        # No need to add duplicate handlers here
        pass
    
    def send_alert(self, alert_type: str, message: str, severity: str = 'WARNING', 
                   details: Dict = None, force_send: bool = False):
        """Send alert through configured channels"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'severity': severity,
            'details': details or {}
        }
        
        # Add to alert history
        self.alert_history.append(alert)
        
        # Check if we should send this alert
        if not force_send and not self._should_send_alert(alert_type, severity):
            return
        
        # Send through all enabled channels
        self._send_to_console(alert)
        self._send_to_log_file(alert)
        
        if self.config['email']['enabled']:
            self._send_to_email(alert)
        
        if self.config['slack']['enabled']:
            self._send_to_slack(alert)
    
    def _should_send_alert(self, alert_type: str, severity: str) -> bool:
        """Determine if alert should be sent based on thresholds and rate limiting"""
        # Always send critical alerts
        if severity == 'CRITICAL':
            return True
        
        # Check thresholds
        if alert_type in self.alert_thresholds:
            threshold = self.alert_thresholds[alert_type]
            if self.error_counts[alert_type] >= threshold:
                return True
        
        # Rate limiting - don't send same alert type more than once per minute
        recent_alerts = [a for a in self.alert_history 
                        if a['type'] == alert_type and 
                        datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(minutes=1)]
        
        return len(recent_alerts) == 0
    
    def _send_to_console(self, alert: Dict):
        """Send alert to console"""
        if not self.config['console']['enabled']:
            return
        
        severity_emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        emoji = severity_emoji.get(alert['severity'], '📢')
        self.logger.warning(f"ALERT [{alert['severity']}] {alert['type']}: {alert['message']}")
        
        if alert['details']:
            self.logger.debug(f"Alert details: {json.dumps(alert['details'], indent=2)}")
    
    def _send_to_log_file(self, alert: Dict):
        """Send alert to log file"""
        if not self.config['log_file']['enabled']:
            return
        
        log_message = f"ALERT [{alert['severity']}] {alert['type']}: {alert['message']}"
        if alert['details']:
            log_message += f" | Details: {json.dumps(alert['details'])}"
        
        if alert['severity'] == 'CRITICAL':
            self.logger.critical(log_message)
        elif alert['severity'] == 'ERROR':
            self.logger.error(log_message)
        elif alert['severity'] == 'WARNING':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _send_to_email(self, alert: Dict):
        """Send alert via email"""
        if not self.config['email']['enabled'] or not self.config['email']['username']:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from_email']
            msg['To'] = ', '.join(self.config['email']['to_emails'])
            msg['Subject'] = f"[{alert['severity']}] NINA Alert: {alert['type']}"
            
            body = f"""
NINA Guardrail Monitor Alert

Alert Type: {alert['type']}
Severity: {alert['severity']}
Message: {alert['message']}
Timestamp: {alert['timestamp']}

Details:
{json.dumps(alert['details'], indent=2)}

This is an automated alert from the NINA Guardrail Monitor system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['username'], self.config['email']['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent: {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _send_to_slack(self, alert: Dict):
        """Send alert to Slack"""
        if not self.config['slack']['enabled'] or not self.config['slack']['webhook_url']:
            return
        
        try:
            import requests # type: ignore
            
            severity_color = {
                'INFO': '#36a64f',
                'WARNING': '#ff9500',
                'ERROR': '#ff0000',
                'CRITICAL': '#8b0000'
            }
            
            color = severity_color.get(alert['severity'], '#36a64f')
            
            slack_message = {
                'channel': self.config['slack']['channel'],
                'attachments': [{
                    'color': color,
                    'title': f"NINA Alert: {alert['type']}",
                    'text': alert['message'],
                    'fields': [
                        {'title': 'Severity', 'value': alert['severity'], 'short': True},
                        {'title': 'Timestamp', 'value': alert['timestamp'], 'short': True}
                    ],
                    'footer': 'NINA Guardrail Monitor',
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            if alert['details']:
                slack_message['attachments'][0]['fields'].append({
                    'title': 'Details',
                    'value': json.dumps(alert['details'], indent=2),
                    'short': False
                })
            
            response = requests.post(self.config['slack']['webhook_url'], json=slack_message)
            response.raise_for_status()
            
            self.logger.info(f"Slack alert sent: {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    def alert_kafka_connection_failure(self, error: str, component: str):
        """Alert for Kafka connection failures"""
        self.error_counts['connection_failures'] += 1
        self.send_alert(
            alert_type='connection_failures',
            message=f"Kafka connection failed for {component}: {error}",
            severity='ERROR',
            details={'component': component, 'error': error}
        )
    
    def alert_producer_retry_failure(self, topic: str, error: str, retry_count: int):
        """Alert for producer retry failures"""
        self.error_counts['retry_failures'] += 1
        self.send_alert(
            alert_type='retry_failures',
            message=f"Producer retry failed for topic {topic} after {retry_count} attempts",
            severity='ERROR',
            details={'topic': topic, 'error': error, 'retry_count': retry_count}
        )
    
    def alert_consumer_processing_failure(self, topic: str, error: str, retry_count: int):
        """Alert for consumer processing failures"""
        self.error_counts['retry_failures'] += 1
        self.send_alert(
            alert_type='retry_failures',
            message=f"Consumer processing failed for topic {topic} after {retry_count} attempts",
            severity='ERROR',
            details={'topic': topic, 'error': error, 'retry_count': retry_count}
        )
    
    def alert_dlq_message(self, original_topic: str, error: str, retry_count: int):
        """Alert for messages sent to DLQ"""
        self.error_counts['dlq_messages'] += 1
        self.send_alert(
            alert_type='dlq_messages',
            message=f"Message sent to DLQ from topic {original_topic}",
            severity='WARNING',
            details={'original_topic': original_topic, 'error': error, 'retry_count': retry_count}
        )
    
    def alert_critical_system_failure(self, component: str, error: str):
        """Alert for critical system failures"""
        self.error_counts['critical_errors'] += 1
        self.send_alert(
            alert_type='critical_errors',
            message=f"CRITICAL: System failure in {component}: {error}",
            severity='CRITICAL',
            details={'component': component, 'error': error},
            force_send=True
        )
    
    def alert_dlq_capacity_warning(self, message_count: int, threshold: int = 100):
        """Alert when DLQ has too many messages"""
        if message_count >= threshold:
            self.send_alert(
                alert_type='dlq_capacity',
                message=f"DLQ capacity warning: {message_count} messages (threshold: {threshold})",
                severity='WARNING',
                details={'message_count': message_count, 'threshold': threshold}
            )
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        """Get summary of alerts in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
        ]
        
        summary = {
            'total_alerts': len(recent_alerts),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int),
            'error_counts': dict(self.error_counts)
        }
        
        for alert in recent_alerts:
            summary['by_severity'][alert['severity']] += 1
            summary['by_type'][alert['type']] += 1
        
        return summary
    
    def print_alert_summary(self, hours: int = 24):
        """Print alert summary"""
        summary = self.get_alert_summary(hours)
        
        print("\n" + "="*60)
        print("🚨 ALERT SUMMARY")
        print("="*60)
        print(f"Total alerts (last {hours}h): {summary['total_alerts']}")
        
        if summary['total_alerts'] == 0:
            print("✅ No alerts - system is healthy!")
            return
        
        print(f"\n📊 By Severity:")
        for severity, count in sorted(summary['by_severity'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {severity}: {count}")
        
        print(f"\n📈 By Type:")
        for alert_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {alert_type}: {count}")
        
        print(f"\n🔢 Error Counts:")
        for error_type, count in summary['error_counts'].items():
            print(f"  {error_type}: {count}")
        
        print("="*60)
    
    def log_successful_delivery(self, topic: str, partition: int, offset: int):
        """Log successful message delivery for monitoring"""
        try:
            # Log to console for debugging
            self.logger.info(f"✅ Message successfully delivered to {topic}[{partition}] @ offset {offset}")
            
            # You can add more sophisticated logging here, such as:
            # - Writing to a metrics database
            # - Updating delivery statistics
            # - Sending to monitoring systems
            
        except Exception as e:
            self.logger.error(f"Error logging successful delivery: {e}")

def main():
    """Main function to test alerting service"""
    print("=" * 60)
    print("🚨 NINA Guardrail Monitor - Error Alerting Service")
    print("=" * 60)
    
    # Initialize alerting service
    alerting_service = ErrorAlertingService()
    
    try:
        # Test different types of alerts
        print("\n🧪 Testing alert system...")
        
        alerting_service.alert_kafka_connection_failure("Connection timeout", "Producer")
        alerting_service.alert_producer_retry_failure("guardrail.conversation.test", "Network error", 3)
        alerting_service.alert_consumer_processing_failure("operator.actions.test", "Database error", 3)
        alerting_service.alert_dlq_message("guardrail.conversation.test", "Max retries exceeded", 3)
        alerting_service.alert_critical_system_failure("Database", "Connection pool exhausted")
        
        # Print summary
        alerting_service.print_alert_summary(hours=1)
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Alerting Service stopped by user")

if __name__ == '__main__':
    main()


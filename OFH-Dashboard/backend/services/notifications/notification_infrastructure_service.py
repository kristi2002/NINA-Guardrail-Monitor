"""
Notification Service for OFH Dashboard
Handles email, SMS, and phone notifications for alerts
"""

import os
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import List, Dict, Optional
from enum import Enum

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    SLACK = "slack"
    TEAMS = "teams"

class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationService:
    """Base notification service"""
    
    def __init__(self):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # SMTP configuration - support both naming conventions
        self.smtp_server = os.getenv('SMTP_HOST') or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USER') or os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('EMAIL_FROM') or os.getenv('FROM_EMAIL', 'nina-alerts@company.com')
        
        # SMS/Phone configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '')
        
        # Slack configuration
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        
        # Teams configuration
        self.teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL', '')
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   priority: NotificationPriority = NotificationPriority.NORMAL,
                   html_body: str = None) -> bool:
        """Send email notification"""
        try:
            if not self.smtp_username or not self.smtp_password:
                self.logger.warning("SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{priority.value.upper()}] {subject}"
            
            # Add priority header
            priority_headers = {
                NotificationPriority.LOW: '5',
                NotificationPriority.NORMAL: '3',
                NotificationPriority.HIGH: '2',
                NotificationPriority.URGENT: '1'
            }
            msg['X-Priority'] = priority_headers.get(priority, '3')
            
            # Create text and HTML parts
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email sent to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}", exc_info=True)
            return False
    
    def send_sms(self, phone_numbers: List[str], message: str, 
                 priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """Send SMS notification using Twilio"""
        try:
            if not self.twilio_account_sid or not self.twilio_auth_token:
                print("⚠️ Twilio credentials not configured")
                return False
            
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            success_count = 0
            for phone_number in phone_numbers:
                try:
                    message_obj = client.messages.create(
                        body=f"[{priority.value.upper()}] {message}",
                        from_=self.twilio_phone_number,
                        to=phone_number
                    )
                    success_count += 1
                    print(f"✅ SMS sent to {phone_number}: {message_obj.sid}")
                except Exception as e:
                    print(f"❌ Failed to send SMS to {phone_number}: {e}")
            
            return success_count > 0
            
        except ImportError:
            print("⚠️ Twilio library not installed")
            return False
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
            return False
    
    def make_phone_call(self, phone_numbers: List[str], message: str,
                       priority: NotificationPriority = NotificationPriority.URGENT) -> bool:
        """Make phone call using Twilio"""
        try:
            if not self.twilio_account_sid or not self.twilio_auth_token:
                print("⚠️ Twilio credentials not configured")
                return False
            
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            success_count = 0
            for phone_number in phone_numbers:
                try:
                    call = client.calls.create(
                        twiml=f'<Response><Say voice="alice">{message}</Say></Response>',
                        from_=self.twilio_phone_number,
                        to=phone_number
                    )
                    success_count += 1
                    print(f"✅ Phone call initiated to {phone_number}: {call.sid}")
                except Exception as e:
                    print(f"❌ Failed to call {phone_number}: {e}")
            
            return success_count > 0
            
        except ImportError:
            print("⚠️ Twilio library not installed")
            return False
        except Exception as e:
            print(f"❌ Failed to make phone calls: {e}")
            return False
    
    def send_slack_message(self, message: str, channel: str = None,
                          priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """Send Slack notification"""
        try:
            if not self.slack_webhook_url:
                print("⚠️ Slack webhook URL not configured")
                return False
            
            import requests
            
            payload = {
                'text': f"[{priority.value.upper()}] {message}",
                'channel': channel or '#nina-alerts',
                'username': 'NINA Alert Bot',
                'icon_emoji': ':robot_face:'
            }
            
            response = requests.post(self.slack_webhook_url, json=payload)
            response.raise_for_status()
            
            print(f"✅ Slack message sent to {payload['channel']}")
            return True
            
        except ImportError:
            print("⚠️ Requests library not installed")
            return False
        except Exception as e:
            print(f"❌ Failed to send Slack message: {e}")
            return False
    
    def send_teams_message(self, message: str, priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """Send Microsoft Teams notification"""
        try:
            if not self.teams_webhook_url:
                print("⚠️ Teams webhook URL not configured")
                return False
            
            import requests
            
            payload = {
                'text': f"[{priority.value.upper()}] {message}",
                'themeColor': self._get_priority_color(priority)
            }
            
            response = requests.post(self.teams_webhook_url, json=payload)
            response.raise_for_status()
            
            print("✅ Teams message sent")
            return True
            
        except ImportError:
            print("⚠️ Requests library not installed")
            return False
        except Exception as e:
            print(f"❌ Failed to send Teams message: {e}")
            return False
    
    def _get_priority_color(self, priority: NotificationPriority) -> str:
        """Get color code for priority"""
        colors = {
            NotificationPriority.LOW: '00ff00',
            NotificationPriority.NORMAL: '0000ff',
            NotificationPriority.HIGH: 'ffa500',
            NotificationPriority.URGENT: 'ff0000'
        }
        return colors.get(priority, '0000ff')
    
    def send_notification(self, notification_type: NotificationType, 
                         recipients: List[str], message: str,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         **kwargs) -> bool:
        """Send notification using specified type"""
        if notification_type == NotificationType.EMAIL:
            return self.send_email(recipients, kwargs.get('subject', 'NINA Alert'), 
                                 message, priority, kwargs.get('html_body'))
        elif notification_type == NotificationType.SMS:
            return self.send_sms(recipients, message, priority)
        elif notification_type == NotificationType.PHONE:
            return self.make_phone_call(recipients, message, priority)
        elif notification_type == NotificationType.SLACK:
            return self.send_slack_message(message, kwargs.get('channel'), priority)
        elif notification_type == NotificationType.TEAMS:
            return self.send_teams_message(message, priority)
        else:
            print(f"❌ Unsupported notification type: {notification_type}")
            return False


class AlertNotificationService:
    """Service for sending alert notifications"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.alert_recipients = {
            'low': os.getenv('ALERT_EMAILS_LOW', '').split(','),
            'normal': os.getenv('ALERT_EMAILS_NORMAL', '').split(','),
            'high': os.getenv('ALERT_EMAILS_HIGH', '').split(','),
            'urgent': os.getenv('ALERT_EMAILS_URGENT', '').split(',')
        }
        
        # Clean up empty strings
        for priority in self.alert_recipients:
            self.alert_recipients[priority] = [email.strip() for email in self.alert_recipients[priority] if email.strip()]
    
    def send_alert_notification(self, alert_data: Dict, notification_methods: List[str] = None) -> bool:
        """Send alert notification using multiple methods"""
        if not notification_methods:
            notification_methods = ['email']  # Default to email only
        
        priority = self._determine_priority(alert_data.get('severity', 'normal'))
        recipients = self._get_recipients(priority)
        
        if not recipients:
            print(f"⚠️ No recipients configured for priority: {priority}")
            return False
        
        subject = f"NINA Alert: {alert_data.get('title', 'Unknown Alert')}"
        message = self._format_alert_message(alert_data)
        
        success = True
        for method in notification_methods:
            if method == 'email':
                success &= self.notification_service.send_email(
                    recipients, subject, message, priority
                )
            elif method == 'sms':
                phone_numbers = self._get_phone_numbers(priority)
                if phone_numbers:
                    success &= self.notification_service.send_sms(
                        phone_numbers, message, priority
                    )
            elif method == 'phone':
                phone_numbers = self._get_phone_numbers(priority)
                if phone_numbers:
                    success &= self.notification_service.make_phone_call(
                        phone_numbers, message, priority
                    )
            elif method == 'slack':
                success &= self.notification_service.send_slack_message(
                    message, priority=priority
                )
            elif method == 'teams':
                success &= self.notification_service.send_teams_message(
                    message, priority
                )
        
        return success
    
    def _determine_priority(self, severity: str) -> NotificationPriority:
        """Determine notification priority from alert severity"""
        severity_map = {
            'low': NotificationPriority.LOW,
            'normal': NotificationPriority.NORMAL,
            'medium': NotificationPriority.NORMAL,
            'high': NotificationPriority.HIGH,
            'critical': NotificationPriority.URGENT,
            'urgent': NotificationPriority.URGENT
        }
        return severity_map.get(severity.lower(), NotificationPriority.NORMAL)
    
    def _get_recipients(self, priority: NotificationPriority) -> List[str]:
        """Get recipients for priority level"""
        return self.alert_recipients.get(priority.value, [])
    
    def _get_phone_numbers(self, priority: NotificationPriority) -> List[str]:
        """Get phone numbers for priority level"""
        phone_env = f'ALERT_PHONES_{priority.value.upper()}'
        phone_numbers = os.getenv(phone_env, '').split(',')
        return [phone.strip() for phone in phone_numbers if phone.strip()]
    
    def _format_alert_message(self, alert_data: Dict) -> str:
        """Format alert data into notification message"""
        message = f"""
NINA Guardrail Monitor Alert

Alert ID: {alert_data.get('id', 'Unknown')}
Severity: {alert_data.get('severity', 'Unknown')}
Title: {alert_data.get('title', 'Unknown Alert')}
Message: {alert_data.get('message', 'No message')}
Timestamp: {alert_data.get('created_at', 'Unknown')}

Conversation ID: {alert_data.get('conversation_id', 'N/A')}
Event Type: {alert_data.get('event_type', 'N/A')}

This is an automated alert from the NINA Guardrail Monitor system.
Please review and take appropriate action.
"""
        return message.strip()


# Global instances
notification_service = NotificationService()
alert_notification_service = AlertNotificationService(notification_service)

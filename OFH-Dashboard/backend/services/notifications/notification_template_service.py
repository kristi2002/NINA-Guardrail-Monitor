#!/usr/bin/env python3
"""
Notification Template Service
Handles notification templates with variable substitution
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class NotificationTemplateService:
    """Service for managing notification templates"""
    
    def __init__(self):
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load default notification templates"""
        return {
            'alert_critical': {
                'subject': '[CRITICAL] Alert: {alert_title}',
                'text': '''Critical Alert Detected

Alert ID: {alert_id}
Title: {alert_title}
Severity: {severity}
Message: {message}
Timestamp: {timestamp}

Conversation ID: {conversation_id}
Event Type: {event_type}

Please review and take immediate action.
''',
                'html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .critical {{ background-color: #ef4444; color: white; padding: 15px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .button {{ background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="critical">
        <h1>🚨 CRITICAL ALERT</h1>
    </div>
    <div class="content">
        <h2>{alert_title}</h2>
        <p><strong>Alert ID:</strong> {alert_id}</p>
        <p><strong>Severity:</strong> {severity}</p>
        <p><strong>Message:</strong> {message}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Conversation ID:</strong> {conversation_id}</p>
        <p><strong>Event Type:</strong> {event_type}</p>
        {action_button}
    </div>
</body>
</html>
'''
            },
            'alert_high': {
                'subject': '[HIGH] Alert: {alert_title}',
                'text': '''High Priority Alert

Alert ID: {alert_id}
Title: {alert_title}
Severity: {severity}
Message: {message}
Timestamp: {timestamp}

Please review at your earliest convenience.
''',
                'html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .high {{ background-color: #f59e0b; color: white; padding: 15px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="high">
        <h1>⚠️ HIGH PRIORITY ALERT</h1>
    </div>
    <div class="content">
        <h2>{alert_title}</h2>
        <p><strong>Alert ID:</strong> {alert_id}</p>
        <p><strong>Message:</strong> {message}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
    </div>
</body>
</html>
'''
            },
            'conversation_update': {
                'subject': 'Conversation Update: {conversation_id}',
                'text': '''Conversation Update

Conversation ID: {conversation_id}
Patient ID: {patient_id}
Status: {status}
Risk Level: {risk_level}
Update: {message}

Timestamp: {timestamp}
''',
                'html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="content">
        <h2>Conversation Update</h2>
        <p><strong>Conversation ID:</strong> {conversation_id}</p>
        <p><strong>Patient ID:</strong> {patient_id}</p>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Risk Level:</strong> {risk_level}</p>
        <p>{message}</p>
        <p><small>Timestamp: {timestamp}</small></p>
    </div>
</body>
</html>
'''
            },
            'system_notification': {
                'subject': 'System Notification: {title}',
                'text': '''System Notification

{title}

{message}

Timestamp: {timestamp}
''',
                'html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="content">
        <h2>{title}</h2>
        <p>{message}</p>
        <p><small>Timestamp: {timestamp}</small></p>
    </div>
</body>
</html>
'''
            },
            'digest_daily': {
                'subject': 'Daily Notification Digest - {count} notification(s)',
                'text': '''Daily Notification Digest

You have {count} notification(s) in your digest:

{notifications_list}

View all notifications in the dashboard.
''',
                'html': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #3b82f6; color: white; padding: 20px; }}
        .content {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Daily Notification Digest</h1>
        <p>{count} notification(s)</p>
    </div>
    <div class="content">
        {notifications_list_html}
    </div>
</body>
</html>
'''
            }
        }
    
    def render_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        include_html: bool = True
    ) -> Dict[str, str]:
        """Render a template with variables"""
        if template_name not in self.templates:
            logger.warning(f"Template '{template_name}' not found, using default")
            template = self.templates.get('system_notification', {})
        else:
            template = self.templates[template_name]
        
        result = {
            'subject': self._substitute_variables(template.get('subject', ''), variables),
            'text': self._substitute_variables(template.get('text', ''), variables)
        }
        
        if include_html and 'html' in template:
            result['html'] = self._substitute_variables(template['html'], variables)
        
        return result
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template string"""
        # Handle default values and formatting
        def replace_var(match):
            var_name = match.group(1)
            default = match.group(2) if match.group(2) else ''
            
            value = variables.get(var_name, default)
            
            # Format datetime if needed
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            return str(value)
        
        # Replace {variable} or {variable|default}
        pattern = r'\{(\w+)(?:\|([^}]+))?\}'
        return re.sub(pattern, replace_var, template)
    
    def add_template(self, name: str, template: Dict[str, str]):
        """Add or update a template"""
        self.templates[name] = template
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())


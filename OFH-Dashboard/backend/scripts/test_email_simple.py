#!/usr/bin/env python3
"""
Simple email test - sends to the configured email address
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.notification_infrastructure_service import NotificationService, NotificationPriority

def test_email_simple():
    """Send test email to the specified recipient"""
    
    smtp_user = os.getenv('SMTP_USER', '')
    recipient = 'krsiti.komini@gmail.com'
    
    if not smtp_user:
        print("❌ SMTP_USER not configured")
        return False
    
    print("📧 Sending test email to:", recipient)
    print(f"   From: {smtp_user}")
    print()
    
    notification_service = NotificationService()
    
    success = notification_service.send_email(
        to_emails=[recipient],  # Send to specified recipient
        subject="OFH Dashboard - Test Email",
        body="""Hello!

This is a test email from the OFH Dashboard system.

If you received this email, your email configuration is working correctly!

Best regards,
OFH Dashboard System""",
        priority=NotificationPriority.NORMAL,
        html_body="""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">✅ Email Test Successful!</h2>
    <p>This is a test email from the <strong>OFH Dashboard</strong> system.</p>
    <p>If you received this email, your email configuration is working correctly!</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
    <p style="color: #6b7280; font-size: 12px;">Best regards,<br>OFH Dashboard System</p>
  </div>
</body>
</html>"""
    )
    
    if success:
        print("=" * 60)
        print("✅ SUCCESS! Email sent successfully!")
        print("=" * 60)
        print(f"📧 Check the inbox of: {recipient}")
        print("   (Also check spam folder if not in inbox)")
        return True
    else:
        print("=" * 60)
        print("❌ FAILED! Could not send email")
        print("=" * 60)
        print("   Check server logs for error details")
        return False

if __name__ == '__main__':
    success = test_email_simple()
    sys.exit(0 if success else 1)


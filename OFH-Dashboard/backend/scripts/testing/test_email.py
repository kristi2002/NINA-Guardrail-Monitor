#!/usr/bin/env python3
"""
Test Email Sending Script
Tests email functionality with Gmail SMTP
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.notification_infrastructure_service import NotificationService, NotificationPriority

def test_email():
    """Test sending an email"""
    
    # Get configuration
    email_enabled = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    print("=" * 60)
    print("OFH Dashboard - Email Test")
    print("=" * 60)
    print()
    
    # Check if email is enabled
    if not email_enabled:
        print("❌ EMAIL_ENABLED is set to False")
        print("   Set EMAIL_ENABLED=True in your .env file")
        return False
    
    # Check credentials
    if not smtp_user or not smtp_password:
        print("❌ SMTP credentials not configured")
        print(f"   SMTP_USER: {'Set' if smtp_user else 'Not set'}")
        print(f"   SMTP_PASSWORD: {'Set' if smtp_password else 'Not set'}")
        print()
        print("   Configure in your .env file:")
        print("   SMTP_USER=your-email@gmail.com")
        print("   SMTP_PASSWORD=your-app-password")
        return False
    
    print(f"✅ Email enabled: {email_enabled}")
    print(f"✅ SMTP User: {smtp_user}")
    print(f"✅ SMTP Password: {'*' * len(smtp_password)} (configured)")
    print()
    
    # Get recipient email
    recipient = input("Enter recipient email address (or press Enter to use sender): ").strip()
    if not recipient:
        recipient = smtp_user
    
    print(f"📧 Sending test email to: {recipient}")
    print()
    
    # Create notification service
    notification_service = NotificationService()
    
    # Prepare email content
    subject = "OFH Dashboard - Test Email"
    body = f"""
Hello!

This is a test email from the OFH Dashboard system.

Email Configuration:
- SMTP Server: {os.getenv('SMTP_HOST', 'smtp.gmail.com')}
- SMTP Port: {os.getenv('SMTP_PORT', '587')}
- From: {os.getenv('EMAIL_FROM', smtp_user)}
- From Name: {os.getenv('EMAIL_FROM_NAME', 'OFH Dashboard')}

If you received this email, your email configuration is working correctly!

Best regards,
OFH Dashboard System
"""
    
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2563eb;">OFH Dashboard - Test Email</h2>
    <p>Hello!</p>
    <p>This is a test email from the <strong>OFH Dashboard</strong> system.</p>
    
    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
      <h3 style="margin-top: 0;">Email Configuration:</h3>
      <ul>
        <li><strong>SMTP Server:</strong> {os.getenv('SMTP_HOST', 'smtp.gmail.com')}</li>
        <li><strong>SMTP Port:</strong> {os.getenv('SMTP_PORT', '587')}</li>
        <li><strong>From:</strong> {os.getenv('EMAIL_FROM', smtp_user)}</li>
        <li><strong>From Name:</strong> {os.getenv('EMAIL_FROM_NAME', 'OFH Dashboard')}</li>
      </ul>
    </div>
    
    <p style="color: #059669; font-weight: bold;">✅ If you received this email, your email configuration is working correctly!</p>
    
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
    <p style="color: #6b7280; font-size: 12px;">Best regards,<br>OFH Dashboard System</p>
  </div>
</body>
</html>
"""
    
    try:
        # Send email
        print("⏳ Sending email...")
        success = notification_service.send_email(
            to_emails=[recipient],
            subject=subject,
            body=body,
            priority=NotificationPriority.NORMAL,
            html_body=html_body
        )
        
        if success:
            print("=" * 60)
            print("✅ SUCCESS! Email sent successfully!")
            print("=" * 60)
            print(f"📧 Check the inbox of: {recipient}")
            return True
        else:
            print("=" * 60)
            print("❌ FAILED! Could not send email")
            print("=" * 60)
            print("   Check the error logs for more details")
            return False
            
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR! Failed to send email")
        print("=" * 60)
        print(f"   Error: {str(e)}")
        print()
        print("   Common issues:")
        print("   - Gmail app password not set correctly")
        print("   - 2FA not enabled on Gmail account")
        print("   - Firewall blocking port 587")
        print("   - SMTP credentials incorrect")
        return False

if __name__ == '__main__':
    success = test_email()
    sys.exit(0 if success else 1)


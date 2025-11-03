# Gmail SMTP Setup Guide

Step-by-step guide to configure Gmail for sending emails from OFH Dashboard.

## 📧 Step 1: Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Sign in with `nina.guardrail.alerts@gmail.com`
3. Under "2-Step Verification", click **Get Started**
4. Follow the prompts to enable 2FA (you'll need your phone)

**Important**: Gmail requires 2FA to be enabled before you can create an app password.

## 🔑 Step 2: Create App-Specific Password

1. After enabling 2FA, go back to [Google Account Security](https://myaccount.google.com/security)
2. Search for "App passwords" or go directly to [App Passwords](https://myaccount.google.com/apppasswords)
3. Select **Mail** as the app
4. Select **Other (Custom name)** as the device
5. Enter name: `OFH Dashboard`
6. Click **Generate**
7. **Copy the 16-character password** (it looks like: `abcd efgh ijkl mnop`)

⚠️ **Important**: This password is only shown once! Save it securely.

## ⚙️ Step 3: Configure Environment Variables

1. In the `backend` directory, copy `env.example` to `.env` (if you haven't already):
   ```bash
   cd backend
   copy env.example .env
   ```

2. Edit your `.env` file and update these values:

```env
# Email Configuration
EMAIL_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=nina.guardrail.alerts@gmail.com
SMTP_PASSWORD=your-16-character-app-password-here
SMTP_USE_TLS=True
EMAIL_FROM=nina.guardrail.alerts@gmail.com
EMAIL_FROM_NAME=OFH Dashboard
```

**Replace `your-16-character-app-password-here`** with the app password you generated in Step 2.

## 🧪 Step 4: Test Email Sending

Run the test script:

```powershell
cd backend
.\venv\Scripts\python.exe scripts\test_email.py
```

Or if you're using the helper script:
```powershell
cd backend
.\run.ps1
# Then in Python:
python scripts\test_email.py
```

The script will:
- Check your email configuration
- Prompt for a recipient email
- Send a test email
- Show success/failure status

## ✅ Step 5: Verify Email Received

Check the recipient's inbox (and spam folder) for the test email.

## 🔧 Troubleshooting

### "Username and Password not accepted"

**Solutions:**
- ✅ Make sure 2FA is enabled on the Gmail account
- ✅ Use the app-specific password (not your regular Gmail password)
- ✅ Remove spaces from the app password (it might have been copied with spaces)
- ✅ Check that `SMTP_USER` matches the Gmail address exactly

### "Connection refused" or "Timeout"

**Solutions:**
- ✅ Check firewall settings (port 587 should be open)
- ✅ Verify `SMTP_PORT=587` is set correctly
- ✅ Try port 465 with `SMTP_USE_TLS=True` (though 587 is recommended)

### "Authentication failed"

**Solutions:**
- ✅ Verify the app password is correct (generate a new one if needed)
- ✅ Make sure `EMAIL_ENABLED=True` (capital T)
- ✅ Check that the Gmail account has "Less secure app access" is NOT needed (app passwords are used instead)

### Email goes to Spam

**Solutions:**
- ✅ Mark as "Not spam" in Gmail
- ✅ Use a custom "From" address if you have a domain
- ✅ Add SPF/DKIM records if using a custom domain (advanced)

## 📝 Quick Reference

**SMTP Settings for Gmail:**
```
Host: smtp.gmail.com
Port: 587 (TLS) or 465 (SSL)
Security: TLS (StartTLS)
Username: Your full Gmail address
Password: App-specific password (16 characters)
```

## 🚀 After Setup

Once email is working, you can:
- Send notifications for alerts
- Send escalation emails
- Send password reset emails
- Send system alerts

All of these will use the same Gmail configuration!


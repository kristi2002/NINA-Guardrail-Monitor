# Quick Email Setup for Gmail

## ⚠️ Important: You Need an App-Specific Password

Gmail **requires** an app-specific password (not your regular password) when using SMTP.

## 🚀 Quick Steps

### 1. Enable 2FA (if not already enabled)
1. Go to: https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the setup steps

### 2. Create App Password
1. After 2FA is enabled, go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter: `OFH Dashboard`
4. Click "Generate"
5. **Copy the 16-character password** (it will look like: `abcd efgh ijkl mnop`)

### 3. Configure .env File

In `backend/.env`, set:
```env
EMAIL_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=nina.guardrail.alerts@gmail.com
SMTP_PASSWORD=your-16-char-app-password-here
SMTP_USE_TLS=True
EMAIL_FROM=nina.guardrail.alerts@gmail.com
EMAIL_FROM_NAME=OFH Dashboard
```

### 4. Test

Run:
```powershell
.\venv\Scripts\python.exe scripts\test_email.py
```

## 🔍 Quick Check

**Your current password (`ninaguardrails123`) is the regular Gmail password.**

You need to generate an **app-specific password** (16 characters) from Google Account settings.

**Direct link**: https://myaccount.google.com/apppasswords

---

**Note**: If you try to use your regular password, you'll get an authentication error. App passwords are required for security.


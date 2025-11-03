# Email Authentication Troubleshooting

## Current Error
`SMTPAuthenticationError: Username and Password not accepted`

## ✅ Configuration Status
- Password length: Correct (16 characters)
- Email: nina.guardrail.alerts@gmail.com
- SMTP settings: Correct

## 🔍 Troubleshooting Steps

### Step 1: Verify 2FA is Enabled

1. Go to: https://myaccount.google.com/security
2. Check if "2-Step Verification" shows as **ON**
3. If OFF, enable it first (required for app passwords)

### Step 2: Regenerate App Password

The current app password might be incorrect. Generate a new one:

1. Go to: https://myaccount.google.com/apppasswords
2. If you see "App passwords" → Great! 
3. If you see "2-Step Verification is off" → Enable 2FA first
4. Click **"Select app"** → Choose **"Mail"**
5. Click **"Select device"** → Choose **"Other (Custom name)"**
6. Enter: `OFH Dashboard`
7. Click **"Generate"**
8. **Copy the 16-character password immediately** (shown only once!)

### Step 3: Update .env File

1. Open `backend/.env`
2. Find the line: `SMTP_PASSWORD=...`
3. Replace with the NEW app password (remove all spaces)
4. Example: If Google shows `abcd efgh ijkl mnop`, use `abcdefghijklmnop`

### Step 4: Test Again

```powershell
python scripts/test_email_simple.py
```

## ⚠️ Common Issues

### Issue: "Username and Password not accepted"
**Solutions:**
- ✅ Use app password (not regular password)
- ✅ Remove ALL spaces from app password
- ✅ Make sure 2FA is enabled
- ✅ Generate a fresh app password

### Issue: "App passwords not available"
**Solution:** Enable 2-Step Verification first

### Issue: Password has spaces
**Solution:** Remove all spaces. Google shows `abcd efgh` but use `abcdefgh`

## 🔑 Quick Checklist

- [ ] 2-Step Verification is ON
- [ ] App password generated from Google Account
- [ ] App password copied correctly (no spaces)
- [ ] `.env` file has `SMTP_PASSWORD=` with 16-character password (no spaces)
- [ ] `.env` file has `EMAIL_ENABLED=True`
- [ ] `.env` file has `SMTP_USER=nina.guardrail.alerts@gmail.com`

## 📧 After Fixing

The test will send to: **krsiti.komini@gmail.com**

Once working, you can:
- Send alerts via email
- Send escalation notifications
- Send password reset emails


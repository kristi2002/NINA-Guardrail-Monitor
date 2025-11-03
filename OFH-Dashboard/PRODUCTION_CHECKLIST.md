# Production Deployment Checklist

This guide helps you complete all pre-production tasks step by step.

## 🔐 Security Configuration

### 1. Change All Default Passwords

**Default passwords** (change these immediately!):
- Admin: `admin` / `admin`
- Operator: `operator` / `operator123`

**How to change passwords:**

**Option A: Using the script (recommended)**
```bash
cd backend
python scripts/change_production_passwords.py
```

**Option B: Manual change via API or database**
```bash
# Use the reset script with environment variable
cd backend
ADMIN_PASSWORD=your-secure-password python scripts/reset_admin_password.py
```

**Option C: Change in the application**
1. Log in as admin
2. Navigate to user profile
3. Change password

### 2. Generate and Set Secure Keys

**Current state**: Default keys in `env.example` are placeholders.

**Generate secure keys:**
```bash
cd backend
python scripts/generate_secrets.py
```

This will generate:
- `SECRET_KEY` (64 characters)
- `JWT_SECRET_KEY` (64 characters)

**Add to your `.env` file:**
```bash
SECRET_KEY=<generated-secret-key>
JWT_SECRET_KEY=<generated-jwt-secret-key>
```

**⚠️ IMPORTANT:**
- Never commit `.env` to version control
- Use different keys for each environment
- Store keys securely (use secret management in production)

### 3. Configure Proper Database

**Development (current)**: SQLite
**Production (required)**: PostgreSQL

**Steps:**
1. Set up PostgreSQL server
2. Create database and user:
   ```sql
   CREATE DATABASE nina_db;
   CREATE USER nina_user WITH ENCRYPTED PASSWORD 'your-secure-password';
   GRANT ALL PRIVILEGES ON DATABASE nina_db TO nina_user;
   ```
3. Update `.env`:
   ```bash
   DATABASE_URL=postgresql://nina_user:your-secure-password@localhost:5432/nina_db
   ```

See `DEPLOYMENT.md` for detailed PostgreSQL setup.

### 4. Configure Email Notifications

**Current state**: Email service is configured but not enabled.

**Enable email:**

1. **Update `.env` file:**
   ```bash
   EMAIL_ENABLED=True
   SMTP_HOST=smtp.gmail.com  # or your SMTP server
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password  # Use app-specific password for Gmail
   SMTP_USE_TLS=True
   EMAIL_FROM=noreply@yourdomain.com
   EMAIL_FROM_NAME=OFH Dashboard
   ```

2. **For Gmail:**
   - Enable 2-factor authentication
   - Generate app-specific password
   - Use app password in `SMTP_PASSWORD`

3. **For other providers:**
   - See `backend/env.example` for configuration options
   - Update SMTP settings based on your provider

### 5. Set Up Monitoring and Alerting

**Current monitoring:**
- ✅ Health check endpoint (`/api/health`)
- ✅ System metrics endpoint (`/api/metrics`)
- ✅ Comprehensive logging with rotation
- ✅ Error alerting service

**Optional enhancements:**

**Prometheus/Grafana** (if needed for enterprise monitoring):
- See `IMPROVEMENTS.md` for when this is needed
- Currently optional for most deployments

**Sentry** (for advanced error tracking):
- See `IMPROVEMENTS.md` for benefits
- Ready to integrate (ErrorBoundary prepared)

### 6. Review and Update TODOs

**Current TODOs found:**

1. **`backend/services/analytics_service.py`**:
   - Line 513: Patient demographics queries
   - Line 521: Conversation feedback queries
   - Line 526: User login/action log queries

2. **`backend/services/user_service.py`**:
   - Line 391: Email sending service integration
   - Status: ConfigHelper ready, needs email service implementation

3. **`backend/services/notification_service.py`**:
   - Line 231: Database-backed notification storage
   - Status: ConfigHelper provides storage config

4. **`backend/services/kafka_consumer.py`**:
   - Line 228: Decouple from Flask app context
   - Status: Non-critical architectural improvement

**Action items:**
- Review each TODO
- Implement critical ones before production
- Defer non-critical improvements
- Document decisions in code comments

## ✅ Already Completed

- [x] Set up Redis for rate limiting ✅
- [x] Enable HTTPS/SSL ✅ (See DEPLOYMENT.md)
- [x] Configure proper CORS origins ✅ (via CORS_ORIGINS env var)
- [x] Set up log rotation ✅
- [x] Enable HTTPS only ✅
- [x] Configure security headers ✅
- [x] Configure rate limiting ✅

## 🔒 Security Hardening Checklist

**📖 See `SECURITY_HARDENING.md` for complete security hardening guide.**

### Quick Reference

1. **Firewall Rules:**
   ```bash
   # Ubuntu/Debian (UFW)
   sudo ufw default deny incoming
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP (redirects to HTTPS)
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```
   See `SECURITY_HARDENING.md` for detailed UFW and firewalld setup.

2. **Database SSL:**
   - Enable SSL in PostgreSQL configuration
   - Update `DATABASE_URL` to use `sslmode=require`
   - Example: `postgresql://user:pass@host:5432/db?sslmode=require`
   - See `SECURITY_HARDENING.md` for PostgreSQL SSL setup steps

3. **Review Environment Variables:**
   ```bash
   # Validate environment variables
   cd backend
   python scripts/validate_env.py
   ```
   See `SECURITY_HARDENING.md` for complete validation checklist.

4. **Backup Strategy:**
   ```bash
   # Create and test backup script
   cd backend
   chmod +x scripts/backup_database.sh
   ./scripts/backup_database.sh
   
   # Schedule with cron (daily at 2 AM)
   crontab -e
   # Add: 0 2 * * * /path/to/backend/scripts/backup_database.sh
   ```
   See `SECURITY_HARDENING.md` for complete backup strategy and disaster recovery plan.

## 📋 Quick Production Setup Script

Create a script to automate common tasks:

```bash
#!/bin/bash
# production-setup.sh

echo "🔐 Generating secure keys..."
cd backend
python scripts/generate_secrets.py > .env.keys
echo "Add keys to .env file"

echo "🔒 Changing default passwords..."
python scripts/change_production_passwords.py

echo "✅ Production setup checklist complete!"
```

## 📝 Verification Steps

Before going live, verify:

1. **Security:**
   - [ ] All default passwords changed
   - [ ] Secure keys generated and set
   - [ ] CORS origins configured (not `*`)
   - [ ] HTTPS enabled
   - [ ] Firewall configured

2. **Configuration:**
   - [ ] Database connection tested
   - [ ] Redis connection tested (if using)
   - [ ] Email service tested (if enabled)
   - [ ] All environment variables set

3. **Monitoring:**
   - [ ] Health check endpoint responding
   - [ ] Logs being written correctly
   - [ ] Error alerts configured

4. **Documentation:**
   - [ ] Production credentials documented (securely)
   - [ ] Backup procedures documented
   - [ ] Recovery procedures documented

---

**Remember:** Security is critical. Never use default credentials in production!


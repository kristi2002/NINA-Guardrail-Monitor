# Security Hardening Guide

Complete guide for securing the OFH Dashboard in production.

## 🔥 Firewall Rules

### Ubuntu/Debian (UFW)

**Basic firewall setup:**
```bash
# Install UFW if not present
sudo apt update
sudo apt install ufw

# Set default policies (deny incoming, allow outgoing)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (do this first or you'll lock yourself out!)
sudo ufw allow 22/tcp

# Allow HTTP (for Let's Encrypt certificate renewal)
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# If using PostgreSQL from external hosts (only if needed)
# sudo ufw allow from 10.0.0.0/8 to any port 5432

# If using Redis from external hosts (only if needed)
# sudo ufw allow from 10.0.0.0/8 to any port 6379

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

**Firewall rules for application:**
```bash
# If backend runs on specific port (default 5000, but behind Nginx)
# Only allow localhost access since Nginx proxies to it
sudo ufw allow from 127.0.0.1 to any port 5000
```

### CentOS/RHEL (firewalld)

```bash
# Install firewalld
sudo yum install firewalld

# Start and enable
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow SSH
sudo firewall-cmd --permanent --add-service=ssh

# Allow HTTP
sudo firewall-cmd --permanent --add-service=http

# Allow HTTPS
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

### Docker Deployment

If using Docker, configure firewall on the host:
```bash
# Allow Docker containers to communicate
sudo ufw allow in on docker0
```

## 🔒 Database SSL Configuration

### PostgreSQL SSL Setup

**1. Enable SSL in PostgreSQL:**

Edit `/etc/postgresql/14/main/postgresql.conf` (or your version):
```conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

**2. Configure client authentication:**

Edit `/etc/postgresql/14/main/pg_hba.conf`:
```conf
# Require SSL for remote connections
hostssl    all    all    0.0.0.0/0    md5
```

**3. Generate SSL certificates (if using self-signed):**

```bash
# Generate self-signed certificate
sudo openssl req -new -x509 -days 365 -nodes -text \
  -out /etc/postgresql/14/main/server.crt \
  -keyout /etc/postgresql/14/main/server.key \
  -subj "/CN=db.example.com"

# Set proper permissions
sudo chmod 600 /etc/postgresql/14/main/server.key
sudo chown postgres:postgres /etc/postgresql/14/main/server.key
sudo chown postgres:postgres /etc/postgresql/14/main/server.crt

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**4. Update application connection string:**

In your `.env` file:
```bash
# With SSL required
DATABASE_URL=postgresql://nina_user:nina_pass@localhost:5432/nina_db?sslmode=require

# Or verify-full (if using CA-signed certificate)
DATABASE_URL=postgresql://nina_user:nina_pass@localhost:5432/nina_db?sslmode=verify-full
```

**5. Test SSL connection:**

```bash
psql "postgresql://nina_user:nina_pass@localhost:5432/nina_db?sslmode=require"
```

**For production, use:**
- CA-signed certificates (Let's Encrypt or commercial CA)
- `sslmode=verify-full` for certificate verification
- Store certificates securely

## 📋 Environment Variables Review

### Security Checklist for Environment Variables

Review each variable in `backend/env.example`:

**🔴 Critical (Must Change):**
- `SECRET_KEY` - Must be unique, min 32 characters
- `JWT_SECRET_KEY` - Must be unique, min 32 characters
- `ADMIN_PASSWORD` - Change from default `admin123`
- `OPERATOR_PASSWORD` - Change from default `operator123`
- `DATABASE_PASSWORD` - Must be strong password

**🟡 Important (Should Configure):**
- `CORS_ORIGINS` - Must not be `*` in production
- `DATABASE_URL` - Use PostgreSQL, not SQLite
- `REDIS_URL` - Use Redis, not `memory://`
- `EMAIL_*` - Configure for email notifications
- `APP_DEBUG` - Must be `False` in production

**🟢 Optional (Based on Needs):**
- `KAFKA_BOOTSTRAP_SERVERS` - Only if using Kafka
- `SLACK_WEBHOOK_URL` - Only if using Slack
- `ESCALATION_*` - Configure escalation rules
- `NOTIFICATION_*` - Configure notification channels

### Environment Variable Validation Script

Create a validation script to check your `.env` file:

```bash
#!/bin/bash
# validate-env.sh

echo "🔍 Validating environment variables..."

# Check critical variables
if grep -q "your-secret-key-change-this" .env; then
  echo "❌ SECRET_KEY not changed!"
fi

if grep -q "your-jwt-secret-key-change-this" .env; then
  echo "❌ JWT_SECRET_KEY not changed!"
fi

if grep -q "CORS_ORIGINS=\*" .env; then
  echo "⚠️  CORS_ORIGINS is set to '*' - not recommended for production"
fi

if grep -q "APP_DEBUG=True" .env; then
  echo "⚠️  APP_DEBUG is True - set to False in production"
fi

if grep -q "sqlite://" .env; then
  echo "⚠️  Using SQLite - PostgreSQL recommended for production"
fi

echo "✅ Environment validation complete"
```

## 💾 Backup Strategy

### PostgreSQL Backup

**1. Manual Backup:**

```bash
# Create backup
pg_dump -U nina_user -d nina_db -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# Restore from backup
pg_restore -U nina_user -d nina_db backup_20240101_120000.dump
```

**2. Automated Backup Script:**

Create `backend/scripts/backup_database.sh`:
```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/var/backups/ofh-dashboard"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nina_db_$DATE.dump"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U nina_user -d nina_db -F c -f $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than retention period
find $BACKUP_DIR -name "nina_db_*.dump.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup created: $BACKUP_FILE.gz"
```

**3. Schedule with Cron:**

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backend/scripts/backup_database.sh >> /var/log/ofh-backup.log 2>&1
```

**4. Backup to Remote Storage:**

**Option A: S3/Azure Blob Storage**
```bash
# After creating backup, upload to S3
aws s3 cp $BACKUP_FILE.gz s3://your-backup-bucket/database/
```

**Option B: rsync to remote server**
```bash
rsync -avz $BACKUP_FILE.gz user@backup-server:/backups/ofh-dashboard/
```

### Redis Backup (if using persistent storage)

```bash
# Redis RDB snapshot backup
cp /var/lib/redis/dump.rdb /var/backups/redis/redis_$(date +%Y%m%d_%H%M%S).rdb
```

### Application Files Backup

```bash
# Backup logs (if needed for compliance)
tar -czf logs_backup_$(date +%Y%m%d).tar.gz backend/logs/

# Backup configuration (without secrets!)
tar -czf config_backup_$(date +%Y%m%d).tar.gz backend/env.example docker-compose.yml
```

### Backup Verification

**Test restore procedure regularly:**

```bash
# Test database restore to a test database
createdb -U nina_user test_restore_db
pg_restore -U nina_user -d test_restore_db backup_file.dump
# Verify data integrity
dropdb -U nina_user test_restore_db
```

### Backup Retention Policy

Recommended retention:
- **Daily backups**: Keep 7 days
- **Weekly backups**: Keep 4 weeks
- **Monthly backups**: Keep 12 months
- **Critical snapshots**: Keep indefinitely (compliance)

### Disaster Recovery Plan

1. **Document recovery procedures**
2. **Test recovery quarterly**
3. **Store backups off-site**
4. **Verify backup integrity**
5. **Document recovery time objectives (RTO)**
6. **Document recovery point objectives (RPO)**

## 🔍 Security Audit Checklist

Before going to production, verify:

- [ ] All default passwords changed
- [ ] Secure keys generated and set
- [ ] CORS origins configured (not `*`)
- [ ] Firewall rules configured
- [ ] Database SSL enabled
- [ ] HTTPS/SSL certificates installed
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Log rotation configured
- [ ] Backups automated and tested
- [ ] Environment variables reviewed
- [ ] Secrets stored securely (not in code)
- [ ] Debug mode disabled
- [ ] Error messages don't leak sensitive info
- [ ] SQL injection protection enabled
- [ ] XSS protection enabled
- [ ] CSRF protection (if applicable)

## 📝 Quick Security Setup

```bash
# 1. Set up firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 2. Enable database SSL
# Edit PostgreSQL config (see above)
sudo systemctl restart postgresql

# 3. Review environment variables
cd backend
python scripts/validate_env.py  # If created

# 4. Set up backups
chmod +x scripts/backup_database.sh
crontab -e  # Add backup schedule
```

---

**Remember**: Security is an ongoing process. Review and update regularly!


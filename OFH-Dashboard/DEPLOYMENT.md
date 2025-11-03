# OFH Dashboard - Production Deployment Guide

This guide provides step-by-step instructions for deploying the OFH Dashboard to production with PostgreSQL.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend Configuration](#backend-configuration)
4. [Frontend Configuration](#frontend-configuration)
5. [Running the Application](#running-the-application)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.9+** - Backend runtime
- **Node.js 18+** - Frontend build tool
- **PostgreSQL 14+** - Production database
- **Kafka** (optional) - Message bus for real-time events
- **Nginx** (recommended) - Reverse proxy

### System Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 20GB+ free space
- **Network**: HTTPS enabled

---

## Database Setup

### 1. Install PostgreSQL

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### CentOS/RHEL
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE nina_db;

# Create user with password
CREATE USER nina_user WITH ENCRYPTED PASSWORD 'nina_pass';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE nina_db TO nina_user;

# Grant privileges on schema (for PostgreSQL 15+)
\c nina_db
GRANT ALL ON SCHEMA public TO nina_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nina_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nina_user;

# Exit
\q
```

### 3. Configure PostgreSQL

Edit `/etc/postgresql/14/main/pg_hba.conf` (or appropriate path for your version):

```conf
# Allow local connections
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5

# Allow remote connections (if needed, adjust for security)
host    all             all             10.0.0.0/8              md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 4. Verify Database Connection

```bash
psql -h localhost -U nina_user -d nina_db
```

---

## Backend Configuration

### 1. Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
cp env.example .env
nano .env  # Or use your preferred editor
```

**CRITICAL**: Update these values for production:

```env
# Change these secrets!
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters-long
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-minimum-32-characters-long

# PostgreSQL connection
DATABASE_URL=postgresql://nina_user:nina_pass@localhost:5432/nina_db

# Disable debug mode!
APP_DEBUG=False

# Change admin password!
ADMIN_PASSWORD=your_secure_admin_password
OPERATOR_PASSWORD=your_secure_operator_password

# Update notification settings
EMAIL_SMTP_HOST=your-smtp-host.com
EMAIL_SMTP_USER=your-email@example.com
EMAIL_SMTP_PASSWORD=your-email-password

# Update Kafka settings if using Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka-server:9092
```

### 3. Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Run initialization script
python init_database.py
```

This will:
- Create all database tables
- Create admin user (default: `admin` / `admin`)
- Create operator user (default: `operator` / `operator123`)

**⚠️ IMPORTANT**: Change these default passwords immediately!

### 4. Test Backend

```bash
# Start backend server
python app.py
```

You should see:
```
✅ Database engine configured with connection pooling
✅ Database connection test successful
✅ Database tables created successfully
🚀 Backend running on http://0.0.0.0:5000
```

### 5. Run Backend as a Service (Systemd)

Create `/etc/systemd/system/ofh-dashboard-backend.service`:

```ini
[Unit]
Description=OFH Dashboard Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/OFH-Dashboard/backend
Environment="PATH=/path/to/OFH-Dashboard/backend/venv/bin"
ExecStart=/path/to/OFH-Dashboard/backend/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ofh-dashboard-backend
sudo systemctl start ofh-dashboard-backend
sudo systemctl status ofh-dashboard-backend
```

---

## Frontend Configuration

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

### 2. Build for Production

```bash
npm run build
```

This creates an optimized production build in `frontend/build/`.

### 3. Serve with Nginx

Create `/etc/nginx/sites-available/ofh-dashboard`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (use Let's Encrypt for free SSL)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Serve frontend
    root /path/to/OFH-Dashboard/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/ofh-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Install SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 5. Configure CDN (Content Delivery Network)

CDN configuration improves performance by serving static assets from edge locations closer to users.

#### Option A: Using Cloudflare (Recommended)

1. **Sign up for Cloudflare** and add your domain
2. **Update DNS records** to point to Cloudflare nameservers
3. **Configure caching rules** in Cloudflare dashboard:
   - Static assets (JS/CSS): Cache Everything, Edge TTL: 1 month
   - HTML files: Cache Level: Standard, Edge TTL: 2 hours
   - API routes: Bypass cache

4. **Enable Auto Minify** in Cloudflare Speed settings:
   - JavaScript: Enabled
   - CSS: Enabled
   - HTML: Enabled

5. **Update Vite build** to use CDN base URL:
   ```bash
   # Build with CDN base URL
   VITE_CDN_BASE_URL=https://cdn.yourdomain.com/ npm run build
   ```

#### Option B: Using AWS CloudFront

1. **Create S3 bucket** for static assets:
   ```bash
   aws s3 mb s3://ofh-dashboard-assets
   aws s3 sync ./frontend/dist s3://ofh-dashboard-assets --delete
   ```

2. **Create CloudFront distribution**:
   - Origin: S3 bucket (ofh-dashboard-assets)
   - Default root object: index.html
   - Viewer protocol policy: Redirect HTTP to HTTPS
   - Allowed HTTP methods: GET, HEAD, OPTIONS

3. **Configure caching behaviors**:
   - Path pattern: `*.js, *.css, *.png, *.jpg, *.svg`
   - Cache policy: CachingOptimized
   - TTL: 31536000 (1 year)

4. **Update build configuration**:
   ```bash
   VITE_CDN_BASE_URL=https://your-cloudfront-url.cloudfront.net/ npm run build
   ```

#### Option C: Using Vercel/Netlify (For Frontend Hosting)

Both platforms provide automatic CDN:

1. **Deploy to Vercel**:
   ```bash
   npm install -g vercel
   vercel --prod
   ```

2. **Deploy to Netlify**:
   ```bash
   npm install -g netlify-cli
   netlify deploy --prod
   ```

#### Nginx Configuration for CDN Integration

Update your Nginx config to serve static assets from CDN:

```nginx
server {
    # ... existing configuration ...

    # Serve static assets from CDN in production
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        # Option 1: Serve from CDN
        proxy_pass https://cdn.yourdomain.com;
        proxy_cache_valid 200 1y;
        add_header Cache-Control "public, immutable";
        
        # Option 2: Or serve locally with long cache
        # expires 1y;
        # add_header Cache-Control "public, immutable";
    }
}
```

#### Environment Variables

Add to your `.env` file:

```bash
# CDN Configuration (for Vite builds)
VITE_CDN_BASE_URL=https://cdn.yourdomain.com/
```

Then rebuild:
```bash
cd frontend
npm run build
```

#### Benefits of CDN

- **Faster load times**: Assets served from edge locations closer to users
- **Reduced server load**: Static assets don't hit your server
- **Better global performance**: CDN nodes worldwide
- **Automatic compression**: Most CDNs compress assets automatically
- **DDoS protection**: Many CDNs include protection

---

## Running the Application

### Development Mode

```bash
# Backend
cd backend
source venv/bin/activate
python app.py

# Frontend (separate terminal)
cd frontend
npm start
```

### Production Mode

1. **Backend**: Started via systemd service (see above)
2. **Frontend**: Served via Nginx (see above)
3. **Database**: Running PostgreSQL service

---

## Verification

### 1. Check Services Status

```bash
# Backend service
sudo systemctl status ofh-dashboard-backend

# PostgreSQL
sudo systemctl status postgresql

# Nginx
sudo systemctl status nginx
```

### 2. Test Database Connection

```bash
cd backend
source venv/bin/activate
python -c "from core.database import init_database; init_database().test_connection()"
```

### 3. Access Application

Open browser: `https://your-domain.com`

Login with:
- Username: `admin`
- Password: (the password you set in `.env`)

### 4. Check Logs

```bash
# Backend logs
sudo journalctl -u ofh-dashboard-backend -f

# Application logs
tail -f backend/logs/security.log
tail -f backend/logs/error_alerts.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## Troubleshooting

### Database Connection Issues

**Error**: `Connection refused` or `password authentication failed`

**Solutions**:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check database credentials in `.env`
3. Verify `pg_hba.conf` allows connections
4. Test connection manually: `psql -h localhost -U nina_user -d nina_db`

### Backend Won't Start

**Error**: `ModuleNotFoundError` or import errors

**Solutions**:
1. Activate virtual environment: `source venv/bin/activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (needs 3.9+)

### Frontend Build Errors

**Error**: `npm ERR!` or build failures

**Solutions**:
1. Clear cache: `npm cache clean --force`
2. Remove `node_modules`: `rm -rf node_modules`
3. Reinstall: `npm install`
4. Check Node version: `node --version` (needs 18+)

### Port Already in Use

**Error**: `Address already in use`

**Solutions**:
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>

# Or change port in .env
APP_PORT=5001
```

### Permission Issues

**Error**: `Permission denied`

**Solutions**:
1. Check file permissions: `ls -la`
2. Fix ownership: `sudo chown -R www-data:www-data /path/to/OFH-Dashboard`
3. Fix permissions: `sudo chmod -R 755 /path/to/OFH-Dashboard`

---

## Security Checklist

Before deploying to production, ensure:

- [ ] Changed all default passwords
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Disabled `APP_DEBUG` mode
- [ ] Configured HTTPS/SSL
- [ ] Restricted database access
- [ ] Enabled firewall rules
- [ ] Set up regular backups
- [ ] Configured log rotation
- [ ] Set up monitoring and alerts
- [ ] Reviewed application logs

---

## Backup and Recovery

### Database Backup

```bash
# Create backup
pg_dump -h localhost -U nina_user nina_db > backup_$(date +%Y%m%d).sql

# Restore backup
psql -h localhost -U nina_user nina_db < backup_20240101.sql
```

### Automated Backups

Create cron job:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * pg_dump -h localhost -U nina_user nina_db > /backups/ofh-dashboard_$(date +\%Y\%m\%d).sql
```

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Guide](https://letsencrypt.org/getting-started/)

---

## Support

For issues or questions:
1. Check this documentation
2. Review application logs
3. Consult ARCHITECTURE.md for system design
4. Contact system administrator


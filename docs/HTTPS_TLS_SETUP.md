# HTTPS/TLS Configuration Guide

This guide explains how to set up HTTPS/TLS for the NINA Guardrail Monitor in production using Nginx as a reverse proxy.

## 🎯 Overview

For production deployments, you should:
1. Use a reverse proxy (Nginx) to handle SSL/TLS termination
2. Configure SSL certificates (Let's Encrypt recommended)
3. Redirect HTTP to HTTPS
4. Secure headers and best practices

## 📋 Prerequisites

- Domain name pointing to your server
- Nginx installed
- Ports 80 and 443 open in firewall
- Docker Compose setup (optional, for containerized deployment)

## 🔧 Option 1: Nginx Reverse Proxy (Recommended)

### Step 1: Install Nginx

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install nginx
```

**CentOS/RHEL:**
```bash
sudo yum install nginx
```

### Step 2: Install SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Step 3: Configure Nginx

Create `/etc/nginx/sites-available/nina-guardrail-monitor`:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration (modern, secure)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend (React app)
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket support
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Guardrail Strategy API (if exposed)
    location /guardrail {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 4: Enable Site and Restart Nginx

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/nina-guardrail-monitor /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 5: Update CORS Configuration

Update your `.env` file:

```env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 🔧 Option 2: Docker Compose with Nginx

### Step 1: Create Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://ofh-dashboard-frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://ofh-dashboard-backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://ofh-dashboard-backend:5000;
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

### Step 2: Add Nginx Service to docker-compose.yml

```yaml
  nginx:
    image: nginx:alpine
    container_name: nina-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl:/etc/nginx/ssl  # Mount SSL certificates
    depends_on:
      - ofh-dashboard-frontend
      - ofh-dashboard-backend
    networks:
      - nina-network
    restart: unless-stopped
```

## 🔒 SSL Certificate Options

### Let's Encrypt (Free, Recommended)

```bash
# Install Certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

### Self-Signed Certificate (Development Only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

⚠️ **Warning**: Self-signed certificates are for development only. Use Let's Encrypt or commercial certificates for production.

## 🔐 Security Best Practices

1. **Use Strong Cipher Suites**: Configure modern TLS protocols (1.2+)
2. **Enable HSTS**: Force HTTPS with Strict-Transport-Security header
3. **Regular Certificate Renewal**: Set up auto-renewal for Let's Encrypt
4. **Firewall Configuration**: Only expose ports 80 and 443
5. **Update CORS**: Ensure CORS_ORIGINS uses HTTPS URLs
6. **Rate Limiting**: Configure Nginx rate limiting for DDoS protection

## 📝 Environment Variables

Update your `.env` file for HTTPS:

```env
# Use HTTPS URLs
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Backend should know it's behind HTTPS
FORCE_HTTPS=true
```

## 🧪 Testing

1. **Test HTTP Redirect:**
   ```bash
   curl -I http://yourdomain.com
   # Should return 301 redirect to HTTPS
   ```

2. **Test HTTPS:**
   ```bash
   curl -I https://yourdomain.com
   # Should return 200 OK
   ```

3. **Test SSL Configuration:**
   ```bash
   openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
   ```

## 🆘 Troubleshooting

### Certificate Not Found
- Check certificate paths in Nginx config
- Verify certificates exist: `ls -la /etc/letsencrypt/live/yourdomain.com/`

### 502 Bad Gateway
- Check backend services are running: `docker compose ps`
- Check Nginx can reach backend: `curl http://localhost:5000/api/health`

### SSL Handshake Failed
- Verify certificate is valid: `openssl x509 -in cert.pem -text -noout`
- Check certificate expiration: `certbot certificates`

## 📚 Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

---

**Last Updated**: December 2025


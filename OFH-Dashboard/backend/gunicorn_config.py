#!/usr/bin/env python3
"""
Gunicorn Configuration for Production
Production WSGI server configuration for Flask-SocketIO
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('API_PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'eventlet'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'nina-ofh-dashboard-backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed - uncomment and configure)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("🚀 NINA OFH Dashboard Backend is ready to accept connections")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("👋 NINA OFH Dashboard Backend is shutting down")


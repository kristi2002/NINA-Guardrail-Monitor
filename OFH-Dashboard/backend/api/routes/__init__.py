"""
API Routes Package
Registers all route blueprints
"""

import os
from datetime import datetime
from flask import Flask, jsonify # type: ignore
from .auth import auth_bp
from .alerts import alerts_bp
from .conversations import conversations_bp
from .analytics import analytics_bp
from .security import security_bp
from .metrics import metrics_bp
from .escalations import escalations_bp
from .notifications import notifications_bp

def register_routes(app: Flask):
    """Register all API route blueprints with the Flask app"""
    
    # Register blueprints with current API prefix (/api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(escalations_bp)
    app.register_blueprint(notifications_bp)
    
    # API versioning is handled by versioning_middleware.py
    # All /api/v1/* requests are rewritten to /api/* internally
    # This provides backward compatibility while supporting future versioning
    
    # Enhanced health check endpoint
    @app.route('/api/health', methods=['GET'])
    @app.route('/api/v1/health', methods=['GET'])  # Support versioned endpoint
    def health_check():
        """Enhanced health check endpoint with component status"""
        try:
            from core.database import get_database_manager
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'components': {}
            }
            
            overall_healthy = True
            
            # Check database
            try:
                db_manager = get_database_manager()
                if db_manager and db_manager.test_connection():
                    health_status['components']['database'] = {
                        'status': 'healthy',
                        'type': 'sqlalchemy'
                    }
                else:
                    health_status['components']['database'] = {
                        'status': 'unhealthy',
                        'type': 'sqlalchemy'
                    }
                    overall_healthy = False
            except Exception as e:
                health_status['components']['database'] = {
                    'status': 'error',
                    'error': str(e),
                    'type': 'sqlalchemy'
                }
                overall_healthy = False
            
            # Check Redis/Cache
            try:
                from core.cache import cache_service, set_cache, get_cache, delete_cache
                if cache_service:
                    # Test cache connection
                    test_key = '__health_check__'
                    set_result = set_cache(test_key, 'test', ttl=10)
                    cached_value = get_cache(test_key)
                    delete_cache(test_key)
                    
                    if cached_value == 'test' and set_result:
                        cache_type = 'redis' if cache_service.enabled and cache_service.redis_client else 'memory'
                        health_status['components']['cache'] = {
                            'status': 'healthy',
                            'type': cache_type
                        }
                    else:
                        cache_type = 'redis' if cache_service.enabled and cache_service.redis_client else 'memory'
                        health_status['components']['cache'] = {
                            'status': 'degraded',
                            'type': cache_type,
                            'message': 'Cache read/write test failed'
                        }
                else:
                    health_status['components']['cache'] = {
                        'status': 'not_configured',
                        'type': 'none'
                    }
            except Exception as e:
                health_status['components']['cache'] = {
                    'status': 'error',
                    'error': str(e),
                    'type': 'unknown'
                }
            
            # Check Kafka (if configured)
            try:
                kafka_service = getattr(app, 'kafka_service', None)
                if kafka_service:
                    # Try to get stats to verify it's working
                    try:
                        stats = kafka_service.get_system_stats()
                        health_status['components']['kafka'] = {
                            'status': 'healthy',
                            'consumer_running': stats.get('consumer_running', False),
                            'active_conversations': stats.get('active_conversations', 0)
                        }
                    except Exception:
                        health_status['components']['kafka'] = {
                            'status': 'degraded',
                            'message': 'Service initialized but stats unavailable'
                        }
                else:
                    health_status['components']['kafka'] = {
                        'status': 'not_configured'
                    }
            except Exception as e:
                health_status['components']['kafka'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Check rate limiter
            try:
                limiter = app.extensions.get('limiter')
                if limiter:
                    health_status['components']['rate_limiter'] = {
                        'status': 'healthy',
                        'storage': 'redis' if 'redis' in str(limiter._storage).lower() else 'memory'
                    }
                else:
                    health_status['components']['rate_limiter'] = {
                        'status': 'not_configured'
                    }
            except Exception as e:
                health_status['components']['rate_limiter'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Set overall status based on components
            if not overall_healthy:
                health_status['status'] = 'degraded'
            
            status_code = 200 if overall_healthy else 503
            return jsonify(health_status), status_code
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'error': str(e)
            }), 500
    
    print("[OK] All API routes registered successfully")
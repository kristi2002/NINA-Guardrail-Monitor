#!/usr/bin/env python3
"""
Metrics Routes
Handles system metrics and performance data
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
import logging
from api.middleware.auth_middleware import token_required, get_current_user
from services.analytics_service import AnalyticsService
from core.database import get_session_context

logger = logging.getLogger(__name__)

# Create Blueprint
metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')

@metrics_bp.route('/metrics', methods=['GET'])
@token_required
def get_metrics():
    """Get system metrics for dashboard"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Metrics requested by {current_user}")
        
        # Use the service to get real data from database
        with get_session_context() as session:
            service = AnalyticsService(session)
            
            # Get dashboard overview for summary metrics
            overview_response = service.get_dashboard_overview('24h')
            overview_data = overview_response.get('data', {})
            
            # Get alert analytics for alert metrics
            alert_response = service.get_alert_analytics('24h')
            alert_data = alert_response.get('data', {})
            
            # Get conversation analytics for conversation metrics (24h for general stats)
            conversation_response = service.get_conversation_analytics('24h')
            conversation_data = conversation_response.get('data', {})
            
            # Get conversations from today (since midnight UTC) for "Conversazioni Oggi"
            # Calculate hours since midnight UTC to get today's conversations
            # Note: Repository uses datetime.utcnow(), so we use UTC for consistency
            now_utc = datetime.now(timezone.utc)
            today_start_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            hours_since_midnight = (now_utc - today_start_utc).total_seconds() / 3600
            # Use hours since midnight to get conversations from today
            today_conversation_response = service.get_conversation_analytics(f'{int(hours_since_midnight)}h')
            today_conversation_data = today_conversation_response.get('data', {})
            
            # Build metrics from real data
            metrics_data = {
                'summary_metrics': {
                    'total_conversations': overview_data.get('conversations', {}).get('total', 0),
                    'active_conversations': overview_data.get('conversations', {}).get('active', 0),
                    'total_alerts': overview_data.get('alerts', {}).get('total', 0),
                    'critical_alerts': overview_data.get('alerts', {}).get('critical', 0),
                    'resolved_alerts': overview_data.get('alerts', {}).get('total', 0) - overview_data.get('alerts', {}).get('active', 0),
                    'average_response_time': alert_data.get('response_time_metrics', {}).get('average_response_time_minutes', 0)
                },
                'conversation_metrics': {
                    'total_sessions': today_conversation_data.get('summary', {}).get('total_conversations', 0),  # Today's conversations
                    'active_sessions': conversation_data.get('summary', {}).get('active_conversations', 0),  # Currently active (24h)
                    'completed_sessions': today_conversation_data.get('summary', {}).get('total_conversations', 0) - conversation_data.get('summary', {}).get('active_conversations', 0),
                    'average_session_duration': conversation_data.get('summary', {}).get('average_duration', 0)
                },
                'alert_metrics': {
                    'total_alerts': alert_data.get('summary', {}).get('total_alerts', 0),
                    'critical_alerts': alert_data.get('summary', {}).get('critical_alerts', 0),
                    'active_alerts': alert_data.get('summary', {}).get('active_alerts', 0),
                    'resolved_alerts': alert_data.get('summary', {}).get('total_alerts', 0) - alert_data.get('summary', {}).get('active_alerts', 0)
                },
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify(metrics_data)
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve metrics',
            'message': str(e)
        }), 500

@metrics_bp.route('/kafka/stats', methods=['GET'])
@token_required
def get_kafka_stats():
    """Get Kafka statistics"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Kafka stats requested by {current_user}")
        
        # Get Kafka service from app context
        from flask import current_app
        kafka_service = getattr(current_app, 'kafka_service', None)
        
        # Get real Kafka stats if service is available
        if kafka_service:
            system_stats = kafka_service.get_system_stats()
            
            # Check producer and consumer connection status
            producer_connected = kafka_service.producer.producer is not None if kafka_service.producer else False
            consumer_connected = kafka_service.consumer.consumer is not None if kafka_service.consumer else False
            consumer_running = system_stats.get('consumer_running', False)
            
            kafka_stats = {
                'active_conversations': system_stats.get('active_conversations', 0),
                'total_events': system_stats.get('total_events', 0),
                'consumer_running': consumer_running,
                'producer_connected': producer_connected,
                'consumer_connected': consumer_connected,
                'bootstrap_servers': kafka_service.bootstrap_servers,
                'uptime': system_stats.get('uptime', datetime.now().isoformat()),
                'topics': system_stats.get('kafka_topics', {}),
                'status': 'connected' if (producer_connected or consumer_connected) else 'disconnected'
            }
        else:
            # Return minimal stats if Kafka not available
            kafka_stats = {
                'consumer_running': False,
                'producer_connected': False,
                'consumer_connected': False,
                'status': 'service_unavailable',
                'error': 'Kafka service not available',
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'kafka_stats': kafka_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving Kafka stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve Kafka stats',
            'message': str(e)
        }), 500

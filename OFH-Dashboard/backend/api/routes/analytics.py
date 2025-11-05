#!/usr/bin/env python3
"""
Analytics Routes
Handles analytics data, metrics, and reporting
"""

from flask import Blueprint, request, jsonify # type: ignore
from datetime import datetime
import logging
from api.middleware.auth_middleware import token_required, get_current_user
from services.analytics_service import AnalyticsService
from core.database import get_session_context
from core.cache import get_cache, set_cache

logger = logging.getLogger(__name__)

# Create Blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/overview', methods=['GET'])
@token_required
def get_analytics_overview():
    """Get analytics overview data from database (with caching)"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Analytics overview requested by {current_user} for range: {time_range}")
        
        # Try to get from cache first
        cache_key = f"analytics:overview:{time_range}"
        cached_data = get_cache(cache_key)
        
        if cached_data:
            logger.info(f"Cache hit for analytics overview: {time_range}")
            status_code = 200 if cached_data.get('success') else 500
            return jsonify(cached_data), status_code
        
        # Cache miss - fetch from database
        logger.info(f"Cache miss - fetching from database: {time_range}")
        with get_session_context() as session:
            service = AnalyticsService(session)
            response_data = service.get_dashboard_overview(time_range)
        
        # Cache the result for 5 minutes
        if response_data.get('success'):
            set_cache(cache_key, response_data, ttl=300)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in analytics overview route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500


@analytics_bp.route('/alerts', methods=['GET'])
@token_required
def get_alerts_analytics():
    """Get alerts analytics data (with caching)"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Alerts analytics requested by {current_user} for range: {time_range}")
        
        # Try to get from cache first
        cache_key = f"analytics:alerts:{time_range}"
        cached_data = get_cache(cache_key)
        
        if cached_data:
            logger.info(f"Cache hit for alerts analytics: {time_range}")
            return jsonify(cached_data), 200
        
        # Cache miss - fetch from database
        logger.info(f"Cache miss - fetching from database: {time_range}")
        with get_session_context() as session:
            service = AnalyticsService(session)
            response_data = service.get_alert_analytics(time_range)
        
        # Cache the result for 5 minutes
        if response_data.get('success'):
            set_cache(cache_key, response_data, ttl=300)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in alerts route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500

@analytics_bp.route('/export', methods=['POST'])
@token_required
def export_analytics():
    """Export analytics data in various formats"""
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        export_format = data.get('format', 'json')
        time_range = data.get('timeRange', '7d')
        
        logger.info(f"Analytics export requested by {current_user} in format: {export_format}")
        
        # Use the service with a database session to get real data
        with get_session_context() as session:
            service = AnalyticsService(session)
            
            # Get dashboard overview data for export
            overview_response = service.get_dashboard_overview(time_range)
            
            if not overview_response.get('success'):
                return jsonify(overview_response), 500
            
            overview_data = overview_response.get('data', {})
            
            # Build export data with real metrics
            export_data = {
                'exported_by': current_user,
                'exported_at': datetime.now().isoformat(),
                'format': export_format,
                'time_range': time_range,
                'data': {
                    'summary_metrics': {
                        'total_conversations': overview_data.get('conversations', {}).get('total', 0),
                        'total_alerts': overview_data.get('alerts', {}).get('total', 0),
                        'critical_alerts': overview_data.get('alerts', {}).get('critical', 0),
                        'active_conversations': overview_data.get('conversations', {}).get('active', 0),
                        'total_users': overview_data.get('users', {}).get('total', 0)
                    }
                }
            }
        
        if export_format == 'csv':
            # In production, generate actual CSV
            return jsonify({
                'success': True,
                'message': 'CSV export generated',
                'download_url': f'/api/analytics/download/{current_user}_export.csv',
                'data': export_data
            })
        elif export_format == 'pdf':
            # In production, generate actual PDF
            return jsonify({
                'success': True,
                'message': 'PDF export generated',
                'download_url': f'/api/analytics/download/{current_user}_export.pdf',
                'data': export_data
            })
        else:
            return jsonify({
                'success': True,
                'message': 'JSON export generated',
                'data': export_data
            })
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to export analytics',
            'message': str(e)
        }), 500

@analytics_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications_analytics():
    """Get notifications analytics data"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Notifications analytics requested by {current_user} for range: {time_range}")
        
        # Use the service with a database session
        with get_session_context() as session:
            service = AnalyticsService(session)
            # Call the new notifications analytics method
            response_data = service.get_notification_analytics(time_range)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Critical error in notifications route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500

@analytics_bp.route('/admin-performance', methods=['GET'])
@token_required
def get_admin_performance_analytics():
    """Get admin performance analytics data"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Admin performance analytics requested by {current_user} for range: {time_range}")
        
        # Use the service with a database session
        with get_session_context() as session:
            service = AnalyticsService(session)
            # Use user analytics which includes admin/user data
            response_data = service.get_user_analytics(time_range)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in admin-performance route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500

@analytics_bp.route('/alert-trends', methods=['GET'])
@token_required
def get_alert_trends():
    """Get alert trends analytics data"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Alert trends requested by {current_user} for range: {time_range}")
        
        # Use the service with a database session
        with get_session_context() as session:
            service = AnalyticsService(session)
            # Call the correct service method
            response_data = service.get_alert_analytics(time_range)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in alert trends route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500

@analytics_bp.route('/response-times', methods=['GET'])
@token_required
def get_response_times():
    """Get response times analytics data"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Response times requested by {current_user} for range: {time_range}")
        
        # Use the service with a database session
        with get_session_context() as session:
            service = AnalyticsService(session)
            # Use alert analytics which includes response time metrics
            response_data = service.get_alert_analytics(time_range)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in response times route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500

@analytics_bp.route('/escalations', methods=['GET'])
@token_required
def get_escalations():
    """Get escalations analytics data"""
    try:
        time_range = request.args.get('timeRange', '7d')
        current_user = get_current_user()
        
        logger.info(f"Escalations requested by {current_user} for range: {time_range}")
        
        # Use the service with a database session
        with get_session_context() as session:
            service = AnalyticsService(session)
            # Use conversation analytics which includes escalation data
            response_data = service.get_conversation_analytics(time_range)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in escalations route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500
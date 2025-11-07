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
    """Export analytics data in various formats - supports tab-specific exports"""
    try:
        current_user = get_current_user()
        data = request.get_json() or {}
        export_format = data.get('format', 'json')
        time_range = data.get('timeRange', '7d')
        active_tab = data.get('activeTab', 'overview')
        
        logger.info(f"Analytics export requested by {current_user} for tab: {active_tab}, format: {export_format}, range: {time_range}")
        
        # Use the service with a database session to get real data
        with get_session_context() as session:
            service = AnalyticsService(session)
            
            # Map tab IDs to service methods
            tab_data = {}
            
            if active_tab == 'overview':
                overview_response = service.get_dashboard_overview(time_range)
                if overview_response.get('success'):
                    tab_data = overview_response.get('data', {})
            elif active_tab == 'notifications':
                notifications_response = service.get_notification_analytics(time_range)
                if notifications_response.get('success'):
                    tab_data = notifications_response.get('data', {})
            elif active_tab == 'users' or active_tab == 'admin-performance':
                users_response = service.get_user_analytics(time_range, admin_only=True)
                if users_response.get('success'):
                    tab_data = users_response.get('data', {})
            elif active_tab == 'alerts' or active_tab == 'alert-trends':
                alerts_response = service.get_alert_trends_analytics(time_range)
                if alerts_response.get('success'):
                    tab_data = alerts_response.get('data', {})
            elif active_tab == 'response' or active_tab == 'response-times':
                response_response = service.get_response_times_analytics(time_range)
                if response_response.get('success'):
                    tab_data = response_response.get('data', {})
            elif active_tab == 'escalations':
                escalations_response = service.get_escalation_analytics(time_range)
                if escalations_response.get('success'):
                    tab_data = escalations_response.get('data', {})
            elif active_tab == 'guardrail-performance':
                guardrail_response = service.get_guardrail_performance_analytics(time_range)
                if guardrail_response.get('success'):
                    tab_data = guardrail_response.get('data', {})
            else:
                # Default to overview
                overview_response = service.get_dashboard_overview(time_range)
                if overview_response.get('success'):
                    tab_data = overview_response.get('data', {})
            
            # Build comprehensive export data
            export_data = {
                'exported_by': current_user,
                'exported_at': datetime.now().isoformat(),
                'format': export_format,
                'time_range': time_range,
                'tab': active_tab,
                'data': tab_data
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
        logger.error(f"Error exporting analytics: {e}", exc_info=True)
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
            # Get admin-only analytics for admin performance tab
            response_data = service.get_user_analytics(time_range, admin_only=True)
        
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

@analytics_bp.route('/guardrail-performance', methods=['GET'])
@token_required
def get_guardrail_performance():
    """Get guardrail performance analytics from Guardrail Strategy service (with caching)"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Guardrail performance analytics requested by {current_user}")
        
        # Try to get from cache first (cache for 5 minutes since guardrail data changes less frequently)
        cache_key = "analytics:guardrail-performance"
        cached_data = get_cache(cache_key)
        
        if cached_data:
            logger.info("Cache hit for guardrail performance analytics")
            status_code = 200 if cached_data.get('success') else 500
            return jsonify(cached_data), status_code
        
        # Cache miss - fetch from Guardrail Strategy service
        logger.info("Cache miss - fetching guardrail performance from Guardrail Strategy service")
        with get_session_context() as session:
            service = AnalyticsService(session)
            response_data = service.get_guardrail_performance_analytics()
        
        # Cache the result for 5 minutes (300 seconds) - longer cache for better performance
        if response_data.get('success'):
            set_cache(cache_key, response_data, ttl=300)
        
        status_code = 200 if response_data.get('success') else 500
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"Critical error in guardrail-performance route: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Critical internal error',
            'message': str(e)
        }), 500
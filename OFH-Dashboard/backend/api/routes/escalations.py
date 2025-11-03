#!/usr/bin/env python3
"""
Escalations Routes
Handles escalation workflows, stats, and management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from api.middleware.auth_middleware import token_required, get_current_user

logger = logging.getLogger(__name__)

# Create Blueprint
escalations_bp = Blueprint('escalations', __name__, url_prefix='/api/escalations')

@escalations_bp.route('/workflows', methods=['GET'])
@token_required
def get_escalation_workflows():
    """Get escalation workflows"""
    try:
        current_user = get_current_user()
        
        logger.info(f"Escalation workflows requested by {current_user}")
        
        # Mock escalation workflows data
        workflows_data = {
            'workflows': [
                {
                    'id': 'wf1',
                    'name': 'Critical Alert Escalation',
                    'description': 'Escalates critical alerts after 5 minutes',
                    'trigger_conditions': {
                        'severity': 'critical',
                        'timeout_minutes': 5
                    },
                    'escalation_steps': [
                        {'step': 1, 'action': 'notify_operator', 'delay_minutes': 0},
                        {'step': 2, 'action': 'notify_supervisor', 'delay_minutes': 5},
                        {'step': 3, 'action': 'notify_manager', 'delay_minutes': 15}
                    ],
                    'active': True
                },
                {
                    'id': 'wf2',
                    'name': 'High Priority Escalation',
                    'description': 'Escalates high priority alerts after 15 minutes',
                    'trigger_conditions': {
                        'severity': 'high',
                        'timeout_minutes': 15
                    },
                    'escalation_steps': [
                        {'step': 1, 'action': 'notify_operator', 'delay_minutes': 0},
                        {'step': 2, 'action': 'notify_supervisor', 'delay_minutes': 15}
                    ],
                    'active': True
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'data': workflows_data
        })
        
    except Exception as e:
        logger.error(f"Error getting escalation workflows: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get escalation workflows',
            'message': str(e)
        }), 500

@escalations_bp.route('/stats', methods=['GET'])
@token_required
def get_escalation_stats():
    """Get escalation statistics"""
    try:
        time_range = request.args.get('range', '24h')
        current_user = get_current_user()
        
        logger.info(f"Escalation stats requested by {current_user} for range: {time_range}")
        
        # Mock escalation stats data
        stats_data = {
            'total_escalations': 23,
            'by_workflow': {
                'wf1': 15,
                'wf2': 8
            },
            'by_severity': {
                'critical': 15,
                'high': 8
            },
            'resolution_times': {
                'avg_minutes': 12.5,
                'median_minutes': 8.0,
                'max_minutes': 45.0
            },
            'trends': [
                {'hour': '00:00', 'count': 2},
                {'hour': '01:00', 'count': 1},
                {'hour': '02:00', 'count': 0},
                {'hour': '03:00', 'count': 1},
                {'hour': '04:00', 'count': 0},
                {'hour': '05:00', 'count': 1},
                {'hour': '06:00', 'count': 2},
                {'hour': '07:00', 'count': 3},
                {'hour': '08:00', 'count': 4},
                {'hour': '09:00', 'count': 5},
                {'hour': '10:00', 'count': 3},
                {'hour': '11:00', 'count': 2},
                {'hour': '12:00', 'count': 1},
                {'hour': '13:00', 'count': 2},
                {'hour': '14:00', 'count': 3},
                {'hour': '15:00', 'count': 4},
                {'hour': '16:00', 'count': 3},
                {'hour': '17:00', 'count': 2},
                {'hour': '18:00', 'count': 1},
                {'hour': '19:00', 'count': 1},
                {'hour': '20:00', 'count': 0},
                {'hour': '21:00', 'count': 1},
                {'hour': '22:00', 'count': 1},
                {'hour': '23:00', 'count': 1}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': stats_data
        })
        
    except Exception as e:
        logger.error(f"Error getting escalation stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get escalation stats',
            'message': str(e)
        }), 500

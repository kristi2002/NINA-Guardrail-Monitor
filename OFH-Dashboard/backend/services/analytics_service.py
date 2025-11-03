#!/usr/bin/env python3
"""
Analytics Service
Handles business logic for analytics and reporting
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime, timedelta
from .base_service import BaseService
from repositories.conversation_repository import ConversationRepository
from repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class AnalyticsService(BaseService):
    """Service for analytics business logic"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        # self.alert_repo = AlertRepository(self.get_session())  # No longer needed
        self.conversation_repo = ConversationRepository(self.get_session())
        self.user_repo = UserRepository(self.get_session())
        # We will query GuardrailEvent directly
        from models.guardrail_event import GuardrailEvent
        self.GuardrailEvent = GuardrailEvent
    
    def get_by_id(self, record_id: int) -> Optional[Any]:
        """Not applicable for analytics service"""
        return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Not applicable for analytics service"""
        return self.format_response(
            success=False,
            message="Create operation not supported for analytics"
        )
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Not applicable for analytics service"""
        return self.format_response(
            success=False,
            message="Update operation not supported for analytics"
        )
    
    def delete(self, record_id: int) -> Dict[str, Any]:
        """Not applicable for analytics service"""
        return self.format_response(
            success=False,
            message="Delete operation not supported for analytics"
        )
    
    def get_dashboard_overview(self, time_range: str = '7d') -> Dict[str, Any]:
        """Get dashboard overview analytics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # Get alert statistics from GuardrailEvent
            alert_stats = self._get_guardrail_event_statistics(hours)
            
            # Get conversation statistics
            conversation_stats = self.conversation_repo.get_conversation_statistics(hours)
            
            # Get user statistics
            user_stats = self.user_repo.get_user_statistics()
            
            # Calculate key metrics
            overview = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'alerts': {
                    'total': alert_stats.get('total_alerts', 0),
                    'critical': alert_stats.get('critical_alerts', 0),
                    'active': alert_stats.get('active_alerts', 0),
                    'severity_distribution': alert_stats.get('severity_distribution', {}),
                    'status_distribution': alert_stats.get('status_distribution', {})
                },
                'conversations': {
                    'total': conversation_stats.get('total_conversations', 0),
                    'active': conversation_stats.get('active_conversations', 0),
                    'high_risk': conversation_stats.get('high_risk_conversations', 0),
                    'average_duration': conversation_stats.get('average_duration_minutes', 0),
                    'risk_distribution': conversation_stats.get('risk_distribution', {})
                },
                'users': {
                    'total': user_stats.get('total_users', 0),
                    'active': user_stats.get('active_users', 0),
                    'role_distribution': user_stats.get('role_distribution', {})
                },
                'system_health': {
                    'alert_response_time': alert_stats.get('average_response_time_minutes', 0),
                    'conversation_escalation_rate': conversation_stats.get('escalation_rate', 0),
                    'user_activity_rate': user_stats.get('active_user_rate', 0)
                }
            }
            
            self.log_operation('dashboard_overview_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=overview,
                message="Dashboard overview retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_dashboard_overview')
    
    def get_alert_analytics(self, time_range: str = '7d') -> Dict[str, Any]:
        """Get alert analytics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # Get alert statistics from GuardrailEvent
            alert_stats = self._get_guardrail_event_statistics(hours)
            
            # Get response time metrics from GuardrailEvent
            response_metrics = self._get_guardrail_event_response_metrics(hours)
            
            # Get recent alerts from GuardrailEvent
            from sqlalchemy import func # type: ignore
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_alerts_raw = self.db.query(self.GuardrailEvent).filter(
                self.GuardrailEvent.created_at >= cutoff_time
            ).order_by(self.GuardrailEvent.created_at.desc()).limit(50).all()
            
            analytics = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {
                    'total_alerts': alert_stats.get('total_alerts', 0),
                    'critical_alerts': alert_stats.get('critical_alerts', 0),
                    'active_alerts': alert_stats.get('active_alerts', 0),
                    'average_response_time': response_metrics.get('average_response_time_minutes', 0),
                    'average_resolution_time': response_metrics.get('average_resolution_time_minutes', 0),
                    'fastest_response_time_minutes': self._get_fastest_response_time(hours),
                    'improvement_percentage': None  # Skipped for now
                },
                'distributions': {
                    'by_severity': alert_stats.get('severity_distribution', {}),
                    'by_status': alert_stats.get('status_distribution', {}),
                    'by_event_type': alert_stats.get('type_distribution', {})  # <-- FIX
                },
                'performance_metrics': {
                    'response_time_by_severity': response_metrics.get('response_time_by_severity', {}),
                    'resolution_time_trends': self._get_resolution_time_trends(hours)
                },
                'recent_alerts': [
                    {
                        'id': event.id,
                        # --- FIX: Campo corretto ---
                        'title': event.message_content, 
                        'severity': event.severity,
                        'status': event.status,
                        'detected_at': event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
                        # --- FIX: Campo corretto ---
                        'response_time': getattr(event, 'response_time_minutes', None) 
                    }
                    for event in recent_alerts_raw
                ]
            }
            
            self.log_operation('alert_analytics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=analytics,
                message="Alert analytics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_alert_analytics')
    
    def get_conversation_analytics(self, time_range: str = '7d') -> Dict[str, Any]:
        """Get conversation analytics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # Get conversation statistics
            conversation_stats = self.conversation_repo.get_conversation_statistics(hours)
            
            # Get conversation metrics
            conversation_metrics = self.conversation_repo.get_conversation_metrics(hours)
            
            # Get recent conversations
            recent_conversations = self.conversation_repo.get_recent_conversations(hours, 50)
            
            analytics = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {
                    'total_conversations': conversation_stats.get('total_conversations', 0),
                    'active_conversations': conversation_stats.get('active_conversations', 0),
                    'high_risk_conversations': conversation_stats.get('high_risk_conversations', 0),
                    'average_duration': conversation_stats.get('average_duration_minutes', 0),
                    'escalation_rate': conversation_stats.get('escalation_rate', 0)
                },
                'distributions': {
                    'by_risk_level': conversation_stats.get('risk_distribution', {}),
                    'by_status': conversation_stats.get('status_distribution', {}),
                    'by_patient_demographics': self._get_patient_demographics_distribution(hours)
                },
                'quality_metrics': {
                    'average_sentiment': conversation_metrics.get('average_sentiment_score', 0),
                    'average_engagement': conversation_metrics.get('average_engagement_score', 0),
                    'satisfaction_trends': self._get_satisfaction_trends(hours)
                },
                'recent_conversations': [
                    {
                        'id': conv.session_id,
                        'patient_id': conv.patient_id,
                        'risk_level': conv.risk_level,
                        'status': conv.status,
                        'duration_minutes': conv.session_duration_minutes,
                        'created_at': conv.created_at.isoformat()
                    }
                    for conv in recent_conversations
                ]
            }
            
            self.log_operation('conversation_analytics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=analytics,
                message="Conversation analytics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_conversation_analytics')
    
    def get_user_analytics(self, time_range: str = '7d') -> Dict[str, Any]:
        """Get user analytics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # Get user statistics
            user_stats = self.user_repo.get_user_statistics()
            
            # Get user activity metrics
            user_activity = self._get_user_activity_metrics(hours)
            
            analytics = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {
                    'total_users': user_stats.get('total_users', 0),
                    'active_users': user_stats.get('active_users', 0),
                    'locked_users': user_stats.get('locked_users', 0),
                    'recent_logins': user_activity.get('recent_logins', 0)
                },
                'distributions': {
                    'by_role': user_stats.get('role_distribution', {}),
                    'by_department': user_stats.get('department_distribution', {}),
                    'by_activity_level': user_activity.get('activity_distribution', {})
                },
                'performance_metrics': {
                    'average_session_duration': user_activity.get('average_session_duration', 0),
                    'login_frequency': user_activity.get('login_frequency', 0),
                    'failed_login_rate': user_activity.get('failed_login_rate', 0)
                },
                'recent_activity': user_activity.get('recent_activity', [])
            }
            
            self.log_operation('user_analytics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=analytics,
                message="User analytics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_user_analytics')
    
    def get_system_health_metrics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # Get various metrics
            alert_stats = self._get_guardrail_event_statistics(hours)  # Use GuardrailEvent
            response_metrics = self._get_guardrail_event_response_metrics(hours)
            conversation_stats = self.conversation_repo.get_conversation_statistics(hours)
            user_stats = self.user_repo.get_user_statistics()
            
            # Calculate health scores
            health_metrics = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'overall_health_score': self._calculate_overall_health_score(alert_stats, conversation_stats, user_stats),
                'alert_health': {
                    'score': self._calculate_alert_health_score(alert_stats),
                    'critical_alerts': alert_stats.get('critical_alerts', 0),
                    'response_time_avg': response_metrics.get('average_response_time_minutes', 0),
                    'resolution_rate': self._calculate_resolution_rate(alert_stats)
                },
                'conversation_health': {
                    'score': self._calculate_conversation_health_score(conversation_stats),
                    'high_risk_rate': conversation_stats.get('high_risk_rate', 0),
                    'escalation_rate': conversation_stats.get('escalation_rate', 0),
                    'average_duration': conversation_stats.get('average_duration_minutes', 0)
                },
                'user_health': {
                    'score': self._calculate_user_health_score(user_stats),
                    'active_user_rate': user_stats.get('active_user_rate', 0),
                    'locked_user_rate': user_stats.get('locked_user_rate', 0),
                    'login_success_rate': user_stats.get('login_success_rate', 0)
                },
                'recommendations': self._generate_health_recommendations(alert_stats, conversation_stats, user_stats)
            }
            
            self.log_operation('system_health_metrics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=health_metrics,
                message="System health metrics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_system_health_metrics')
    
    def get_notification_analytics(self, time_range: str = '7d') -> Dict[str, Any]:
        """Get notification analytics from alerts and conversations"""
        try:
            hours = self._parse_time_range_to_hours(time_range)
            
            # Get alert statistics which serve as notifications from GuardrailEvent
            alert_stats = self._get_guardrail_event_statistics(hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_alerts = self.db.query(self.GuardrailEvent).filter(
                self.GuardrailEvent.created_at >= cutoff_time
            ).order_by(self.GuardrailEvent.created_at.desc()).limit(100).all()
            
            # Calculate notification metrics based on alerts
            total_notifications = alert_stats.get('total_alerts', 0)
            
            # Group by type (using alert types as notification types)
            by_type = {}
            by_status = alert_stats.get('status_distribution', {})
            
            # Track notification trends (daily breakdown)
            trends = []
            current_date = datetime.now()
            for i in range(min(7, hours // 24)):
                day_start = current_date - timedelta(days=i)
                day_end = current_date - timedelta(days=i-1)
                
                day_alerts = len([a for a in recent_alerts 
                                 if a.created_at and day_start <= a.created_at < day_end])
                trends.insert(0, {
                    'date': day_start.strftime('%Y-%m-%d'),
                    'count': day_alerts
                })
            
            # --- FIX: Stato corretto ---
            sent_count = by_status.get('dismissed', 0) + by_status.get('ACKNOWLEDGED', 0)
            pending_count = by_status.get('PENDING', 0)
            # --- FINE FIX ---
            
            analytics = {
                'time_range': time_range,
                'generated_at': datetime.utcnow().isoformat(),
                'total_notifications': total_notifications,
                'by_type': {
                    'alert': total_notifications  # All notifications are alerts
                },
                'by_status': {
                    'sent': sent_count,
                    'failed': 0,  # Corretto
                    'pending': pending_count
                },
                'notification_breakdown': [
                    {
                        'method': 'Alert',
                        'delivered': sent_count,
                        'rate': (sent_count / total_notifications * 100) if total_notifications > 0 else 0
                    }
                ],
                'trends': trends
            }
            
            self.log_operation('notification_analytics_requested', details={
                'time_range': time_range,
                'hours': hours
            })
            
            return self.format_response(
                success=True,
                data=analytics,
                message="Notification analytics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_notification_analytics')
    
    def _get_guardrail_event_statistics(self, hours: int) -> Dict[str, Any]:
        """Helper to get stats from GuardrailEvent table"""
        from sqlalchemy import func # type: ignore
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        base_query = self.db.query(self.GuardrailEvent).filter(
            self.GuardrailEvent.created_at >= cutoff_time
        )
        
        total_alerts = base_query.count()
        critical_alerts = base_query.filter(
            self.GuardrailEvent.severity.in_(['CRITICAL', 'critical'])
        ).count()
        active_alerts = base_query.filter(
            self.GuardrailEvent.status == 'PENDING'
        ).count()
        
        severity_dist = base_query.with_entities(
            self.GuardrailEvent.severity, func.count(self.GuardrailEvent.id)
        ).group_by(self.GuardrailEvent.severity).all()
        
        status_dist = base_query.with_entities(
            self.GuardrailEvent.status, func.count(self.GuardrailEvent.id)
        ).group_by(self.GuardrailEvent.status).all()
        
        type_dist = base_query.with_entities(
            self.GuardrailEvent.event_type, func.count(self.GuardrailEvent.id)
        ).group_by(self.GuardrailEvent.event_type).all()
        
        return {
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'active_alerts': active_alerts,
            'severity_distribution': {s: c for s, c in severity_dist},
            'status_distribution': {s: c for s, c in status_dist},
            'type_distribution': {t: c for t, c in type_dist if t},
        }

    def _get_guardrail_event_response_metrics(self, hours: int) -> Dict[str, Any]:
        """Helper to get response/resolution metrics from GuardrailEvent"""
        from sqlalchemy import func # type: ignore
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        base_query = self.db.query(self.GuardrailEvent).filter(
            self.GuardrailEvent.created_at >= cutoff_time
        )
        
        # Average response time (reviewed_at - created_at)
        avg_response_time = base_query.filter(
            self.GuardrailEvent.reviewed_at.isnot(None)
        ).with_entities(
            func.avg(func.extract('epoch', self.GuardrailEvent.reviewed_at - self.GuardrailEvent.created_at) / 60)
        ).scalar()
        
        # Average resolution time (dismissed events)
        avg_resolution_time_query = base_query.filter(
            self.GuardrailEvent.status == 'dismissed',
            self.GuardrailEvent.reviewed_at.isnot(None)
        ).with_entities(
            func.avg(func.extract('epoch', self.GuardrailEvent.reviewed_at - self.GuardrailEvent.created_at) / 60)
        ).scalar()
        
        # Response time by severity
        response_by_severity = base_query.filter(
            self.GuardrailEvent.reviewed_at.isnot(None)
        ).group_by(self.GuardrailEvent.severity).with_entities(
            self.GuardrailEvent.severity,
            func.avg(func.extract('epoch', self.GuardrailEvent.reviewed_at - self.GuardrailEvent.created_at) / 60)
        ).all()
        
        return {
            'average_response_time_minutes': float(avg_response_time) if avg_response_time else 0,
            'average_resolution_time_minutes': float(avg_resolution_time_query) if avg_resolution_time_query else 0,
            'response_time_by_severity': {s: float(c) for s, c in response_by_severity}
        }
    
    def _get_fastest_response_time(self, hours: int) -> Optional[float]:
        """Get fastest response time from GuardrailEvent"""
        try:
            from sqlalchemy import func # type: ignore
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            fastest = self.db.query(
                func.min(func.extract('epoch', self.GuardrailEvent.reviewed_at - self.GuardrailEvent.created_at) / 60)
            ).filter(
                self.GuardrailEvent.reviewed_at.isnot(None),
                self.GuardrailEvent.created_at >= cutoff_time
            ).scalar()
            
            return float(fastest) if fastest else None
        except Exception as e:
            self.logger.warning(f"Error getting fastest response time: {e}")
            return None
    
    def _parse_time_range_to_hours(self, time_range: str) -> int:
        """Parse time range string to hours"""
        if time_range == '1h':
            return 1
        elif time_range in ['24h', '1d']:
            return 24
        elif time_range == '7d':
            return 24 * 7
        elif time_range == '30d':
            return 24 * 30
        elif time_range == '90d':
            return 24 * 90
        else:
            return 24  # Default to 24 hours
    
    def _get_alert_event_type_distribution(self, hours: int) -> Dict[str, int]:
        """Get alert distribution by event type from GuardrailEvent"""
        try:
            from sqlalchemy import func # type: ignore
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get events grouped by event_type
            type_stats = self.db.query(
                self.GuardrailEvent.event_type,
                func.count(self.GuardrailEvent.id).label('count')
            ).filter(
                self.GuardrailEvent.created_at >= cutoff_time,
                self.GuardrailEvent.event_type.isnot(None)
            ).group_by(self.GuardrailEvent.event_type).all()
            
            return {stat.event_type: stat.count for stat in type_stats}
        except Exception as e:
            self.logger.warning(f"Error getting alert event type distribution: {e}")
            return {}
    
    def _get_resolution_time_trends(self, hours: int) -> List[Dict[str, Any]]:
        """Get resolution time trends from GuardrailEvent"""
        try:
            from sqlalchemy import func # type: ignore
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get events with reviewed_at timestamps, grouped by day
            # GuardrailEvent doesn't have resolved_at, so we use reviewed_at as a proxy
            reviewed_events = self.db.query(self.GuardrailEvent).filter(
                self.GuardrailEvent.reviewed_at.isnot(None),
                self.GuardrailEvent.created_at >= cutoff_time
            ).all()
            
            # Group by date and calculate average resolution time per day
            trends_dict = {}
            for event in reviewed_events:
                if event.created_at and event.reviewed_at:
                    date_key = event.created_at.date().isoformat()
                    resolution_minutes = (event.reviewed_at - event.created_at).total_seconds() / 60
                    
                    if date_key not in trends_dict:
                        trends_dict[date_key] = {'date': date_key, 'total': 0, 'sum': 0}
                    trends_dict[date_key]['total'] += 1
                    trends_dict[date_key]['sum'] += resolution_minutes
            
            # Convert to list with average resolution time
            trends = []
            for date_key, data in sorted(trends_dict.items()):
                avg_time = data['sum'] / data['total'] if data['total'] > 0 else 0
                trends.append({
                    'date': date_key,
                    'average_resolution_time_minutes': round(avg_time, 2),
                    'count': data['total']
                })
            
            return trends
        except Exception as e:
            self.logger.warning(f"Error getting resolution time trends: {e}")
            return []
    
    def _get_patient_demographics_distribution(self, hours: int) -> Dict[str, Any]:
        """Get patient demographics distribution"""
        # TODO: Implement with actual database queries from conversation sessions
        return {
            'age_groups': {},
            'gender': {}
        }
    
    def _get_satisfaction_trends(self, hours: int) -> List[Dict[str, Any]]:
        """Get satisfaction trends"""
        # TODO: Implement with actual database queries from conversation feedback
        return []
    
    def _get_user_activity_metrics(self, hours: int) -> Dict[str, Any]:
        """Get user activity metrics"""
        # TODO: Implement with actual database queries from user login and action logs
        return {
            'recent_logins': 0,
            'activity_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'average_session_duration': 0,
            'login_frequency': 0,
            'failed_login_rate': 0,
            'recent_activity': []
        }
    
    def _calculate_overall_health_score(self, alert_stats: Dict, conversation_stats: Dict, user_stats: Dict) -> float:
        """Calculate overall system health score"""
        alert_score = self._calculate_alert_health_score(alert_stats)
        conversation_score = self._calculate_conversation_health_score(conversation_stats)
        user_score = self._calculate_user_health_score(user_stats)
        
        return (alert_score + conversation_score + user_score) / 3
    
    def _calculate_alert_health_score(self, alert_stats: Dict) -> float:
        """Calculate alert health score"""
        critical_alerts = alert_stats.get('critical_alerts', 0)
        total_alerts = alert_stats.get('total_alerts', 1)
        
        # Lower critical alert rate = higher score
        critical_rate = critical_alerts / total_alerts if total_alerts > 0 else 0
        return max(0, 100 - (critical_rate * 100))
    
    def _calculate_conversation_health_score(self, conversation_stats: Dict) -> float:
        """Calculate conversation health score"""
        high_risk_rate = conversation_stats.get('high_risk_rate', 0)
        escalation_rate = conversation_stats.get('escalation_rate', 0)
        
        # Lower high-risk and escalation rates = higher score
        return max(0, 100 - (high_risk_rate + escalation_rate) * 50)
    
    def _calculate_user_health_score(self, user_stats: Dict) -> float:
        """Calculate user health score"""
        active_rate = user_stats.get('active_user_rate', 0)
        locked_rate = user_stats.get('locked_user_rate', 0)
        
        # Higher active rate and lower locked rate = higher score
        return (active_rate * 0.7) + ((1 - locked_rate) * 0.3) * 100
    
    def _calculate_resolution_rate(self, alert_stats: Dict) -> float:
        """Calculate alert resolution rate"""
        total_alerts = alert_stats.get('total_alerts', 0)
        resolved_alerts = alert_stats.get('status_distribution', {}).get('resolved', 0)
        
        return (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
    
    def _generate_health_recommendations(self, alert_stats: Dict, conversation_stats: Dict, user_stats: Dict) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        # Alert recommendations
        if alert_stats.get('critical_alerts', 0) > 5:
            recommendations.append("High number of critical alerts - consider increasing monitoring staff")
        
        if alert_stats.get('average_response_time_minutes', 0) > 30:
            recommendations.append("Alert response time is high - review alert processing workflow")
        
        # Conversation recommendations
        if conversation_stats.get('high_risk_rate', 0) > 0.1:
            recommendations.append("High-risk conversation rate is elevated - review guardrail settings")
        
        if conversation_stats.get('escalation_rate', 0) > 0.05:
            recommendations.append("High escalation rate - consider additional training for operators")
        
        # User recommendations
        if user_stats.get('locked_user_rate', 0) > 0.1:
            recommendations.append("High user lockout rate - review password policies")
        
        if user_stats.get('active_user_rate', 0) < 0.8:
            recommendations.append("Low user activity - consider user engagement initiatives")
        
        return recommendations

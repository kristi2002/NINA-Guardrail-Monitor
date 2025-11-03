#!/usr/bin/env python3
"""
System Monitor for OFH Dashboard
Monitors the health and performance of all system components
"""

import time
import json
import psutil
import requests
import logging
from datetime import datetime, timedelta
from services.database_service import EnhancedDatabaseService
from .kafka_integration_service import KafkaIntegrationService
# from .kafka_topic_manager import KafkaTopicManager  # OBSOLETE - Removed for static topics

class SystemMonitor:
    def __init__(self):
        self.db_service = EnhancedDatabaseService()
        self.kafka_service = None
        # self.topic_manager = None  # OBSOLETE - Removed for static topics
        self.base_url = 'http://localhost:5000'
        self.frontend_url = 'http://localhost:3000'
        self.monitoring_data = {}
        self.alerts = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def initialize(self):
        """Initialize monitoring services"""
        try:
            # Initialize Kafka services (no topic manager needed with static topics)
            self.kafka_service = KafkaIntegrationService('localhost:9092')
            # self.topic_manager = KafkaTopicManager('localhost:9092')  # OBSOLETE - Static topics
            
            self.logger.info("System Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"System Monitor initialization error: {e}", exc_info=True)
            return False
    
    def check_system_health(self):
        """Check overall system health"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'alerts': [],
            'performance': {}
        }
        
        # Check each component
        components = [
            ('database', self.check_database_health),
            ('kafka', self.check_kafka_health),
            ('backend_api', self.check_backend_health),
            ('frontend', self.check_frontend_health),
            ('system_resources', self.check_system_resources)
        ]
        
        for component_name, check_func in components:
            try:
                component_status = check_func()
                health_status['components'][component_name] = component_status
                
                if component_status['status'] != 'healthy':
                    health_status['overall_status'] = 'degraded'
                    health_status['alerts'].append({
                        'component': component_name,
                        'message': component_status.get('message', 'Component not healthy'),
                        'severity': component_status.get('severity', 'warning')
                    })
            except Exception as e:
                health_status['components'][component_name] = {
                    'status': 'error',
                    'message': str(e),
                    'severity': 'critical'
                }
                health_status['overall_status'] = 'error'
                health_status['alerts'].append({
                    'component': component_name,
                    'message': str(e),
                    'severity': 'critical'
                })
        
        # Check performance
        health_status['performance'] = self.get_performance_metrics()
        
        return health_status
    
    def check_database_health(self):
        """Check database health"""
        try:
            # Test connection
            if not self.db_service.test_connection():
                return {
                    'status': 'error',
                    'message': 'Database connection failed',
                    'severity': 'critical'
                }
            
            # Check recent activity
            recent_events = self.db_service.get_recent_guardrail_events(hours=1)
            active_conversations = self.db_service.get_active_conversations()
            
            # Check database size and performance
            stats = self.db_service.get_system_statistics()
            
            return {
                'status': 'healthy',
                'message': 'Database is healthy',
                'metrics': {
                    'recent_events': len(recent_events),
                    'active_conversations': len(active_conversations),
                    'total_conversations': stats.get('total_conversations', 0),
                    'total_events_24h': stats.get('total_events_24h', 0)
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database health check failed: {e}',
                'severity': 'critical'
            }
    
    def check_kafka_health(self):
        """Check Kafka health"""
        try:
            if not self.kafka_service:
                return {
                    'status': 'error',
                    'message': 'Kafka service not initialized',
                    'severity': 'critical'
                }
            
            # Check consumer status
            stats = self.kafka_service.get_system_stats()
            consumer_running = stats.get('consumer_running', False)
            
            if not consumer_running:
                return {
                    'status': 'error',
                    'message': 'Kafka consumer not running',
                    'severity': 'critical'
                }
            
            # With static topics, we don't need to list conversation topics
            # Static topics: guardrail_events, operator_actions, guardrail_control
            static_topics_count = 3  # Fixed number of static topics
            
            return {
                'status': 'healthy',
                'message': 'Kafka is healthy',
                'metrics': {
                    'consumer_running': consumer_running,
                    'active_conversations': stats.get('active_conversations', 0),
                    'total_events': stats.get('total_events', 0),
                    'total_topics': static_topics_count  # Fixed: 3 static topics
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Kafka health check failed: {e}',
                'severity': 'critical'
            }
    
    def check_backend_health(self):
        """Check backend API health"""
        try:
            # Test basic endpoint
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'message': f'Backend API returned {response.status_code}',
                    'severity': 'critical'
                }
            
            # Test Kafka stats endpoint
            response = requests.get(f"{self.base_url}/api/kafka/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                return {
                    'status': 'healthy',
                    'message': 'Backend API is healthy',
                    'metrics': {
                        'api_response_time': response.elapsed.total_seconds(),
                        'kafka_stats_available': True,
                        'active_conversations': stats.get('database_stats', {}).get('active_conversations', 0)
                    }
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Backend API is running but Kafka stats unavailable',
                    'severity': 'warning'
                }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f'Backend API not accessible: {e}',
                'severity': 'critical'
            }
    
    def check_frontend_health(self):
        """Check frontend health"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'message': 'Frontend is healthy',
                    'metrics': {
                        'response_time': response.elapsed.total_seconds()
                    }
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'Frontend returned {response.status_code}',
                    'severity': 'warning'
                }
        except requests.exceptions.RequestException:
            return {
                'status': 'warning',
                'message': 'Frontend not accessible',
                'severity': 'warning'
            }
    
    def check_system_resources(self):
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            status = 'healthy'
            severity = 'info'
            
            # Check for resource warnings
            if cpu_percent > 80:
                status = 'warning'
                severity = 'warning'
            elif cpu_percent > 95:
                status = 'error'
                severity = 'critical'
            
            if memory.percent > 85:
                status = 'warning'
                severity = 'warning'
            elif memory.percent > 95:
                status = 'error'
                severity = 'critical'
            
            if disk.percent > 90:
                status = 'warning'
                severity = 'warning'
            
            return {
                'status': status,
                'message': f'System resources: CPU {cpu_percent}%, Memory {memory.percent}%',
                'severity': severity,
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3),
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'System resource check failed: {e}',
                'severity': 'critical'
            }
    
    def get_performance_metrics(self):
        """Get performance metrics"""
        try:
            metrics = {}
            
            # Database performance
            if self.db_service:
                db_stats = self.db_service.get_system_statistics()
                metrics['database'] = {
                    'total_conversations': db_stats.get('total_conversations', 0),
                    'active_conversations': db_stats.get('active_conversations', 0),
                    'total_events_24h': db_stats.get('total_events_24h', 0),
                    'average_duration_minutes': db_stats.get('average_duration_minutes', 0)
                }
            
            # Kafka performance
            if self.kafka_service:
                kafka_stats = self.kafka_service.get_system_stats()
                metrics['kafka'] = {
                    'consumer_running': kafka_stats.get('consumer_running', False),
                    'active_conversations': kafka_stats.get('active_conversations', 0),
                    'total_events': kafka_stats.get('total_events', 0),
                    'total_topics': kafka_stats.get('kafka_topics', {}).get('total_guardrail_topics', 0)
                }
            
            # System performance
            metrics['system'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
            
            return metrics
        except Exception as e:
            return {'error': str(e)}
    
    def generate_health_report(self):
        """Generate comprehensive health report"""
        health_status = self.check_system_health()
        
        report = {
            'timestamp': health_status['timestamp'],
            'overall_status': health_status['overall_status'],
            'summary': {
                'total_components': len(health_status['components']),
                'healthy_components': sum(1 for c in health_status['components'].values() if c['status'] == 'healthy'),
                'warning_components': sum(1 for c in health_status['components'].values() if c['status'] == 'warning'),
                'error_components': sum(1 for c in health_status['components'].values() if c['status'] == 'error'),
                'total_alerts': len(health_status['alerts'])
            },
            'components': health_status['components'],
            'alerts': health_status['alerts'],
            'performance': health_status['performance']
        }
        
        return report
    
    def monitor_continuously(self, interval=60):
        """Monitor system continuously"""
        self.logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        while True:
            try:
                report = self.generate_health_report()
                
                # Print status
                status_emoji = {
                    'healthy': '✅',
                    'degraded': '⚠️',
                    'error': '❌'
                }
                
                emoji = status_emoji.get(report['overall_status'], '❓')
                self.logger.info(f"System Status: {report['overall_status'].upper()}")
                self.logger.info(f"Components: {report['summary']['healthy_components']}/{report['summary']['total_components']} healthy")
                
                if report['alerts']:
                    self.logger.warning("Alerts detected:")
                    for alert in report['alerts']:
                        self.logger.warning(f"  - {alert['component']}: {alert['message']}")
                
                # Store monitoring data
                self.monitoring_data[report['timestamp']] = report
                
                # Keep only last 100 reports
                if len(self.monitoring_data) > 100:
                    oldest_key = min(self.monitoring_data.keys())
                    del self.monitoring_data[oldest_key]
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n⏸️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(interval)
    
    def get_monitoring_history(self, hours=24):
        """Get monitoring history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = []
        for timestamp, data in self.monitoring_data.items():
            if datetime.fromisoformat(timestamp) > cutoff_time:
                history.append(data)
        
        return sorted(history, key=lambda x: x['timestamp'])

def main():
    """Main monitoring function"""
    print("🔍 OFH Dashboard System Monitor")
    print("=" * 50)
    
    monitor = SystemMonitor()
    
    if not monitor.initialize():
        print("❌ Failed to initialize system monitor")
        return
    
    try:
        # Generate initial health report
        report = monitor.generate_health_report()
        
        print(f"\n📊 System Health Report")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"Components: {report['summary']['healthy_components']}/{report['summary']['total_components']} healthy")
        
        if report['alerts']:
            print("\n🚨 Alerts:")
            for alert in report['alerts']:
                print(f"   - {alert['component']}: {alert['message']}")
        
        # Start continuous monitoring
        print(f"\n🔍 Starting continuous monitoring...")
        monitor.monitor_continuously(interval=30)
        
    except KeyboardInterrupt:
        print("\n⏸️ Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Monitoring error: {e}")

if __name__ == '__main__':
    main()

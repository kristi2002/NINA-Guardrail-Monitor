#!/usr/bin/env python3
"""
Dead Letter Queue (DLQ) Management Service for NINA Guardrail Monitor
Handles DLQ topic creation, message recovery, and monitoring
"""

import json
import logging
from datetime import datetime, timedelta
from kafka import KafkaConsumer, KafkaProducer # type: ignore
from kafka.errors import KafkaError # type: ignore
from kafka.admin import KafkaAdminClient, ConfigResource, ConfigResourceType # type: ignore
from kafka.admin.config_resource import ConfigResource # type: ignore
from kafka.errors import TopicAlreadyExistsError # type: ignore

class DLQManagementService:
    def __init__(self, bootstrap_servers='localhost:9092'):
        """Initialize DLQ management service"""
        # Setup logging FIRST
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.bootstrap_servers = bootstrap_servers
        self.admin_client = None
        self.consumer = None
        self.producer = None
        
        # DLQ configuration
        self.dlq_topic = 'dead_letter_queue'
        self.dlq_configs = {
            'cleanup.policy': 'delete',
            'retention.ms': '2592000000',  # 30 days
            'segment.ms': '86400000',       # 1 day
            'compression.type': 'snappy',
            'min.insync.replicas': '1'
        }
        
        self.connect()
    
    def connect(self):
        """Connect to Kafka admin client"""
        try:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='nina-dlq-manager'
            )
            self.logger.info(f"DLQ Management Service connected to {self.bootstrap_servers}")
            return True
        except KafkaError as e:
            self.logger.error(f"Failed to connect to Kafka admin: {e}", exc_info=True)
            return False
    
    def create_dlq_topic(self):
        """Create the dead letter queue topic"""
        try:
            from kafka.admin import NewTopic # type: ignore
            
            topic = NewTopic(
                name=self.dlq_topic,
                num_partitions=3,
                replication_factor=1,
                topic_configs=self.dlq_configs
            )
            
            # Create topic
            result = self.admin_client.create_topics([topic])
            
            # Wait for topic creation
            for topic_name, future in result.items():
                try:
                    future.result()  # The result itself is None
                    print(f"✅ DLQ topic '{topic_name}' created successfully")
                    self.logger.info(f"DLQ topic '{topic_name}' created successfully")
                except TopicAlreadyExistsError:
                    print(f"ℹ️ DLQ topic '{topic_name}' already exists")
                    self.logger.info(f"DLQ topic '{topic_name}' already exists")
                except Exception as e:
                    print(f"❌ Failed to create DLQ topic '{topic_name}': {e}")
                    self.logger.error(f"Failed to create DLQ topic '{topic_name}': {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating DLQ topic: {e}")
            self.logger.error(f"Error creating DLQ topic: {e}")
            return False
    
    def get_dlq_messages(self, limit=100, hours_back=24):
        """Retrieve messages from DLQ for analysis"""
        try:
            consumer = KafkaConsumer(
                self.dlq_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id='dlq-analysis',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000
            )
            
            messages = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            self.logger.info(f"Analyzing DLQ messages from last {hours_back} hours...")
            
            for message in consumer:
                if len(messages) >= limit:
                    break
                
                dlq_data = message.value
                message_time = datetime.fromisoformat(dlq_data.get('timestamp', ''))
                
                if message_time >= cutoff_time:
                    messages.append({
                        'offset': message.offset,
                        'partition': message.partition,
                        'timestamp': dlq_data.get('timestamp'),
                        'original_topic': dlq_data.get('original_topic'),
                        'error': dlq_data.get('error'),
                        'retry_count': dlq_data.get('retry_count'),
                        'consumer_group': dlq_data.get('consumer_group')
                    })
            
            consumer.close()
            return messages
            
        except Exception as e:
            print(f"❌ Error retrieving DLQ messages: {e}")
            self.logger.error(f"Error retrieving DLQ messages: {e}")
            return []
    
    def analyze_dlq_patterns(self, hours_back=24):
        """Analyze DLQ message patterns to identify common failure causes"""
        messages = self.get_dlq_messages(limit=1000, hours_back=hours_back)
        
        if not messages:
            self.logger.info("No DLQ messages found for analysis")
            return {}
        
        # Analyze patterns
        analysis = {
            'total_messages': len(messages),
            'by_topic': {},
            'by_error': {},
            'by_consumer_group': {},
            'retry_distribution': {},
            'time_distribution': {}
        }
        
        for msg in messages:
            # By topic
            topic = msg['original_topic']
            analysis['by_topic'][topic] = analysis['by_topic'].get(topic, 0) + 1
            
            # By error type
            error = msg['error']
            error_type = error.split(':')[0] if ':' in error else error
            analysis['by_error'][error_type] = analysis['by_error'].get(error_type, 0) + 1
            
            # By consumer group
            group = msg['consumer_group']
            analysis['by_consumer_group'][group] = analysis['by_consumer_group'].get(group, 0) + 1
            
            # Retry distribution
            retry_count = msg['retry_count']
            analysis['retry_distribution'][retry_count] = analysis['retry_distribution'].get(retry_count, 0) + 1
            
            # Time distribution (by hour)
            timestamp = datetime.fromisoformat(msg['timestamp'])
            hour = timestamp.hour
            analysis['time_distribution'][hour] = analysis['time_distribution'].get(hour, 0) + 1
        
        return analysis
    
    def print_dlq_analysis(self, hours_back=24):
        """Print comprehensive DLQ analysis"""
        analysis = self.analyze_dlq_patterns(hours_back)
        
        if not analysis:
            return
        
        print("\n" + "="*60)
        print("📊 DEAD LETTER QUEUE ANALYSIS")
        print("="*60)
        print(f"Total DLQ messages (last {hours_back}h): {analysis['total_messages']}")
        
        if analysis['total_messages'] == 0:
            print("✅ No messages in DLQ - system is healthy!")
            return
        
        print(f"\n📈 By Original Topic:")
        for topic, count in sorted(analysis['by_topic'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {topic}: {count}")
        
        print(f"\n❌ By Error Type:")
        for error, count in sorted(analysis['by_error'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error}: {count}")
        
        print(f"\n👥 By Consumer Group:")
        for group, count in sorted(analysis['by_consumer_group'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {group}: {count}")
        
        print(f"\n🔄 By Retry Count:")
        for retry_count, count in sorted(analysis['retry_distribution'].items()):
            print(f"  {retry_count} retries: {count}")
        
        print(f"\n⏰ By Hour (last {hours_back}h):")
        for hour in sorted(analysis['time_distribution'].keys()):
            count = analysis['time_distribution'][hour]
            print(f"  {hour:02d}:00 - {count} messages")
        
        print("="*60)
    
    def recover_dlq_messages(self, original_topic, limit=10):
        """Attempt to recover and reprocess DLQ messages for a specific topic"""
        try:
            # Get DLQ messages for specific topic
            consumer = KafkaConsumer(
                self.dlq_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id='dlq-recovery',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000
            )
            
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            recovered_count = 0
            
            self.logger.info(f"Attempting to recover DLQ messages for topic: {original_topic}")
            
            for message in consumer:
                if recovered_count >= limit:
                    break
                
                dlq_data = message.value
                if dlq_data.get('original_topic') == original_topic:
                    # Attempt to resend original message
                    original_message = dlq_data.get('original_message')
                    original_key = dlq_data.get('original_key')
                    
                    try:
                        future = producer.send(original_topic, value=original_message, key=original_key)
                        future.get(timeout=10)
                        recovered_count += 1
                        print(f"✅ Recovered message {recovered_count}: {original_topic}")
                        self.logger.info(f"Recovered DLQ message to {original_topic}")
                    except Exception as e:
                        print(f"❌ Failed to recover message: {e}")
                        self.logger.error(f"Failed to recover DLQ message: {e}")
            
            producer.close()
            consumer.close()
            
            print(f"✅ Recovery completed: {recovered_count} messages recovered")
            return recovered_count
            
        except Exception as e:
            print(f"❌ Error during DLQ recovery: {e}")
            self.logger.error(f"Error during DLQ recovery: {e}")
            return 0
    
    def close(self):
        """Close DLQ management service"""
        if self.admin_client:
            self.admin_client.close()
            self.logger.info("DLQ Management Service closed")

def main():
    """Main function to run DLQ management service"""
    print("=" * 60)
    print("📊 NINA Guardrail Monitor - DLQ Management Service")
    print("=" * 60)
    
    # Initialize DLQ service
    dlq_service = DLQManagementService('localhost:9092')
    
    if not dlq_service.admin_client:
        print("❌ Failed to initialize DLQ service")
        return
    
    try:
        # Create DLQ topic
        print("\n🔧 Creating DLQ topic...")
        dlq_service.create_dlq_topic()
        
        # Analyze DLQ messages
        print("\n📊 Analyzing DLQ messages...")
        dlq_service.print_dlq_analysis(hours_back=24)
        
        # Example recovery (uncomment to test)
        # print("\n🔄 Testing DLQ recovery...")
        # dlq_service.recover_dlq_messages('guardrail.conversation.test', limit=5)
        
    except KeyboardInterrupt:
        print("\n\n⏸️ DLQ Management Service stopped by user")
    finally:
        dlq_service.close()

if __name__ == '__main__':
    main()

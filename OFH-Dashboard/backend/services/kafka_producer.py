#!/usr/bin/env python3
"""
Enhanced Kafka Producer for NINA Guardrail Monitor

Sends to STATIC Kafka topics: guardrail_events, operator_actions, guardrail_control
"""

import json
import time
import random
import uuid
import logging
import os
from datetime import datetime
from kafka import KafkaProducer # type: ignore
from kafka.errors import KafkaError # type: ignore
# tenacity import removed - not used in this file
from services.error_alerting_service import ErrorAlertingService
from config import config, get_kafka_bootstrap_servers

class NINAKafkaProducerV2:
    def __init__(self, bootstrap_servers=None, max_retries=None, retry_delay=None, async_mode=True):
        """Initialize enhanced Kafka producer with static topics"""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.bootstrap_servers = bootstrap_servers or get_kafka_bootstrap_servers()
        self.producer = None
        self.max_retries = max_retries or config.get('MAX_RETRIES')
        self.retry_delay = retry_delay or config.get('RETRY_DELAY')
        self.async_mode = async_mode  # Enable asynchronous sending
        self.dlq_producer = None  # Dead letter queue producer
        self.connect()
        
        # Define our static topics
        self.topics = {
            'guardrail_events': os.getenv('KAFKA_TOPIC_GUARDRAIL', 'guardrail_events'),
            'operator_actions': os.getenv('KAFKA_TOPIC_OPERATOR', 'operator_actions'),
            'guardrail_control': os.getenv('KAFKA_TOPIC_CONTROL', 'guardrail_control'),
            'dead_letter_queue': 'dead_letter_queue'
        }
        
        
        # Initialize alerting service
        self.alerting_service = ErrorAlertingService()
        
        # Statistics for monitoring
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'messages_successful': 0,
            'dlq_messages': 0
        }
    
    def _on_send_success(self, record_metadata, topic, message, key):
        """Callback function for successful message delivery"""
        try:
            self.stats['messages_successful'] += 1
            self.logger.info(f"✅ Message sent successfully to {topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
            
            # Log success metrics
            if hasattr(self, 'alerting_service'):
                self.alerting_service.log_successful_delivery(topic, record_metadata.partition, record_metadata.offset)
                
        except Exception as e:
            self.logger.error(f"Error in success callback: {e}")
    
    def _on_send_error(self, exception, topic, message, key):
        """Callback function for failed message delivery"""
        try:
            self.stats['messages_failed'] += 1
            self.logger.error(f"❌ Failed to send message to {topic}: {exception}")
            
            # Alert on failure
            if hasattr(self, 'alerting_service'):
                self.alerting_service.alert_producer_failure(str(exception), topic)
            
            # Send to DLQ if enabled
            if config.get('DLQ_ENABLED', True):
                self._send_to_dlq_async(topic, message, key, exception)
                
        except Exception as e:
            self.logger.critical(f"Error in failure callback: {e}")
    
    def _send_to_dlq_async(self, original_topic, message, key, error):
        """Send failed message to dead letter queue asynchronously"""
        try:
            dlq_message = {
                'original_topic': original_topic,
                'original_message': message,
                'original_key': key,
                'error': str(error),
                'timestamp': datetime.now().isoformat(),
                'retry_count': self.max_retries
            }
            
            # Send to DLQ asynchronously
            dlq_future = self.dlq_producer.send(
                self.topics['dead_letter_queue'],
                value=dlq_message,
                key=f"dlq_{key}" if key else None
            )
            
            # Add callback for DLQ send
            dlq_future.add_callback(
                lambda metadata, topic=self.topics['dead_letter_queue']: 
                self._on_dlq_success(metadata, topic, original_topic)
            )
            dlq_future.add_errback(
                lambda exception, topic=self.topics['dead_letter_queue']: 
                self._on_dlq_error(exception, topic, original_topic)
            )
            
        except Exception as dlq_error:
            self.logger.critical(f"Failed to send message to DLQ: {dlq_error}")
    
    def _on_dlq_success(self, record_metadata, dlq_topic, original_topic):
        """Callback for successful DLQ message delivery"""
        try:
            self.stats['dlq_messages'] += 1
            self.logger.error(f"📨 Message sent to DLQ: {original_topic} -> {dlq_topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
        except Exception as e:
            self.logger.error(f"Error in DLQ success callback: {e}")
    
    def _on_dlq_error(self, exception, dlq_topic, original_topic):
        """Callback for failed DLQ message delivery"""
        try:
            self.logger.critical(f"💥 CRITICAL: Failed to send message to DLQ: {exception}")
            if hasattr(self, 'alerting_service'):
                self.alerting_service.alert_critical_failure(f"DLQ failure: {exception}", dlq_topic)
        except Exception as e:
            self.logger.critical(f"Error in DLQ error callback: {e}")
        
    def connect(self):
        """Connect to Kafka broker with retry configuration"""
        try:
            # Configure producer for high-throughput asynchronous sending
            producer_config = {
                'bootstrap_servers': self.bootstrap_servers,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'retries': self.max_retries,
                'retry_backoff_ms': 1000,
                'request_timeout_ms': config.get('REQUEST_TIMEOUT_MS'),
                'delivery_timeout_ms': config.get('DELIVERY_TIMEOUT_MS'),
                # Async optimizations
                'batch_size': 16384,  # Larger batches for better throughput
                'linger_ms': 5,  # Wait up to 5ms to batch messages
                'compression_type': 'snappy',  # Compress messages for efficiency
                'max_in_flight_requests_per_connection': 1,  # Allow multiple in-flight requests
                'enable_idempotence': True,  # Ensure exactly-once delivery
                'acks': 'all'  # Required for idempotent producer
            }
            
            self.producer = KafkaProducer(**producer_config)
            
            # Initialize DLQ producer for failed messages
            self.dlq_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            self.logger.info(f"Enhanced Kafka Producer connected to {self.bootstrap_servers}")
            self.logger.info(f"Producer connected with max_retries={self.max_retries}")
            return True
        except KafkaError as e:
            self.logger.error(f"Failed to connect to Kafka: {e}", exc_info=True)
            self.alerting_service.alert_kafka_connection_failure(str(e), "Producer")
            return False
    
    def _send_async(self, topic, value, key=None):
        """Send message asynchronously with callback handling"""
        try:
            self.stats['messages_sent'] += 1
            
            # Send message asynchronously
            future = self.producer.send(topic, value=value, key=key)
            
            # Add success and error callbacks
            future.add_callback(
                lambda metadata, t=topic, m=value, k=key: 
                self._on_send_success(metadata, t, m, k)
            )
            future.add_errback(
                lambda exception, t=topic, m=value, k=key: 
                self._on_send_error(exception, t, m, k)
            )
            
            self.logger.debug(f"Message sent asynchronously to {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {topic}: {e}")
            self.stats['messages_failed'] += 1
            return False
    
    def _send_sync(self, topic, value, key=None):
        """Send message synchronously (fallback for critical messages)"""
        try:
            future = self.producer.send(topic, value=value, key=key)
            record_metadata = future.get(timeout=10)
            self.logger.info(f"Message sent successfully to {topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
            return record_metadata
        except KafkaError as e:
            self.logger.warning(f"Kafka error during send: {e}")
            raise
    
    def _send_to_dlq(self, original_topic, message, key, error):
        """Send failed message to dead letter queue"""
        try:
            dlq_message = {
                'original_topic': original_topic,
                'original_message': message,
                'original_key': key,
                'error': str(error),
                'timestamp': datetime.now().isoformat(),
                'retry_count': self.max_retries
            }
            
            dlq_future = self.dlq_producer.send(
                self.topics['dead_letter_queue'],
                value=dlq_message,
                key=f"dlq_{key}" if key else None
            )
            dlq_metadata = dlq_future.get(timeout=10)
            self.logger.error(f"Message sent to DLQ: {original_topic} -> {self.topics['dead_letter_queue']}[{dlq_metadata.partition}] @ offset {dlq_metadata.offset}")
            return True
        except Exception as dlq_error:
            self.logger.critical(f"Failed to send message to DLQ: {dlq_error}")
            return False
    
    def _handle_send_failure(self, topic, message, key, error):
        """Handle send failure with alerting and DLQ"""
        self.logger.error(f"Failed to send message to {topic} after {self.max_retries} retries: {error}")
        
        # Alert on retry failure
        self.alerting_service.alert_producer_retry_failure(topic, str(error), self.max_retries)
        
        # Send to DLQ
        dlq_success = self._send_to_dlq(topic, message, key, error)
        
        # Alert on critical failure
        if not dlq_success:
            self.logger.critical(f"CRITICAL: Message lost - failed to send to both target topic and DLQ")
            self.alerting_service.alert_critical_system_failure("Producer", f"Failed to send to DLQ for topic {topic}")
        
        return dlq_success
    
    def generate_conversation_id(self):
        """Generate a unique conversation ID"""
        return f"conv_{uuid.uuid4().hex[:8]}"
    
    def generate_guardrail_event(self, conversation_id=None):
        """Generate a realistic guardrail monitoring event for specific conversation"""
        if not conversation_id:
            conversation_id = self.generate_conversation_id()
            
        event_types = [
            {
                'type': 'conversation_started',
                'severity': 'info',
                'message': 'Conversation session initiated',
                'context': 'User started new healthcare consultation'
            },
            {
                'type': 'warning_triggered',
                'severity': 'medium',
                'message': 'Potential medical advice without disclaimer detected',
                'context': 'User asked about medication interactions'
            },
            {
                'type': 'alarm_triggered',
                'severity': 'high',
                'message': 'Critical medical advice blocked',
                'context': 'User requested specific medical diagnosis'
            },
            {
                'type': 'privacy_violation_prevented',
                'severity': 'critical',
                'message': 'Request for patient SSN blocked',
                'context': 'User tried to access restricted PHI data'
            },
            {
                'type': 'medication_warning',
                'severity': 'high',
                'message': 'Potential drug interaction detected',
                'context': 'Warfarin and Aspirin combination flagged'
            },
            {
                'type': 'inappropriate_content',
                'severity': 'medium',
                'message': 'Non-medical content filtered',
                'context': 'User requested entertainment recommendations'
            },
            {
                'type': 'emergency_protocol',
                'severity': 'critical',
                'message': 'Emergency situation detected',
                'context': 'User reported severe symptoms requiring immediate attention'
            },
            {
                'type': 'conversation_ended',
                'severity': 'info',
                'message': 'Conversation session completed',
                'context': 'User ended healthcare consultation'
            }
        ]
        
        event = random.choice(event_types)
        
        return {
            'schema_version': '1.0',
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'event_type': event['type'],
            'severity': event['severity'],
            'message': event['message'],
            'context': event['context'],
            'user_id': f"user_{random.randint(100, 999)}",
            'event_id': str(uuid.uuid4()),
            'action_taken': random.choice(['blocked', 'warned', 'logged', 'escalated', 'allowed']),
            'confidence_score': round(random.uniform(0.7, 0.99), 2),
            'guardrail_version': '2.0',
            'session_metadata': {
                'start_time': datetime.now().isoformat(),
                'message_count': random.randint(1, 20),
                'duration_seconds': random.randint(30, 600)
            }
        }
    
    def generate_operator_action(self, conversation_id, action_type='stop_conversation'):
        """Generate operator action event"""
        actions = {
            'stop_conversation': {
                'action': 'stop_conversation',
                'message': 'Operator stopped conversation due to policy violation',
                'reason': 'Inappropriate content detected'
            },
            'false_alarm': {
                'action': 'false_alarm',
                'message': 'Operator reported false alarm',
                'reason': 'Guardrail incorrectly flagged legitimate content'
            },
            'escalation': {
                'action': 'escalation',
                'message': 'Operator escalated to human supervisor',
                'reason': 'Complex medical case requiring expert review'
            }
        }
        
        action_data = actions.get(action_type, actions['stop_conversation'])
        
        return {
            'schema_version': '1.0',
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'action_type': action_data['action'],
            'action_description': action_data['message'],
            'reason': action_data['reason'],
            'operator_id': f"operator_{random.randint(1, 10)}",
            'priority': 'high' if action_type == 'stop_conversation' else 'medium'
        }
    
    def send_guardrail_event(self, conversation_id, event=None):
        """Send guardrail event to the STATIC guardrail topic"""
        if not self.producer:
            self.logger.error("Producer not connected")
            return False
        
        if not event:
            event = self.generate_guardrail_event(conversation_id)
        
        # --- FIX ---
        topic = self.topics['guardrail_events']
        # --- END FIX ---
        
        try:
            if self.async_mode:
                success = self._send_async(topic, event, key=conversation_id)
                if success:
                    self.logger.info(f"Guardrail event queued for {topic}")
                return success
            else:
                record_metadata = self._send_sync(topic, event, conversation_id)
                self.logger.info(f"Guardrail event sent to {topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to send guardrail event: {e}", exc_info=True)
            self._handle_send_failure(topic, event, conversation_id, e)
            return False
    
    def send_operator_action(self, conversation_id, action_type='stop_conversation', custom_message=None):
        """Send operator action to the STATIC operator topic"""
        if not self.producer:
            self.logger.error("Producer not connected")
            return False
        
        if custom_message:
            action_event = custom_message
        else:
            # Genera un payload conforme allo schema se non fornito
            action_event = {
                'schema_version': '1.0',
                'conversation_id': conversation_id,
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'operator_id': 'dashboard_operator',  # Sostituire con l'ID operatore reale se disponibile
                'action_description': f"Azione '{action_type}' avviata dall'operatore.",
                'reason': 'Operator intervention',
                'priority': 'high' if action_type in ['stop_conversation', 'emergency_stop'] else 'normal',
                'target_event_id': None,
                'action_metadata': None
            }
            
        # --- FIX ---
        topic = self.topics['operator_actions']
        # --- END FIX ---
        
        try:
            if self.async_mode:
                success = self._send_async(topic, action_event, key=conversation_id)
                if success:
                    self.logger.info(f"Operator action queued for {topic}")
                return success
            else:
                record_metadata = self._send_sync(topic, action_event, conversation_id)
                self.logger.info(f"Operator action sent to {topic}[{record_metadata.partition}] @ offset {record_metadata.offset}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to send operator action: {e}", exc_info=True)
            self._handle_send_failure(topic, action_event, conversation_id, e)
            return False
    
    def get_stats(self):
        """Get producer statistics for monitoring"""
        return {
            'messages_sent': self.stats['messages_sent'],
            'messages_successful': self.stats['messages_successful'],
            'messages_failed': self.stats['messages_failed'],
            'dlq_messages': self.stats['dlq_messages'],
            'success_rate': (self.stats['messages_successful'] / max(self.stats['messages_sent'], 1)) * 100,
            'async_mode': self.async_mode
        }
    
    def set_async_mode(self, enabled):
        """Enable or disable asynchronous sending mode"""
        self.async_mode = enabled
        self.logger.info(f"Asynchronous mode {'enabled' if enabled else 'disabled'}")
    
    def flush(self):
        """Flush all pending messages to ensure delivery"""
        if self.producer:
            self.producer.flush()
            self.logger.info("Producer flushed - all pending messages sent")
    
    def send_false_alarm_feedback(self, conversation_id, original_event_id, feedback):
        """Send false alarm feedback to the STATIC control topic"""
        if not self.producer:
            self.logger.error("Producer not connected")
            return False
        
        feedback_event = {
            'schema_version': '1.0',
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'feedback_type': 'false_alarm',
            'feedback_content': feedback,
            'feedback_source': 'operator',
            'original_event_id': original_event_id
        }
        
        # --- FIX ---
        topic = self.topics['guardrail_control']
        # --- END FIX ---
        
        try:
            success = self._send_async(topic, feedback_event, key=conversation_id)
            if success:
                self.logger.info(f"False alarm feedback queued for {topic}")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"Failed to send false alarm feedback: {e}", exc_info=True)
            self._handle_send_failure(topic, feedback_event, conversation_id, e)
            return False
    
    def simulate_conversation_flow(self, conversation_id=None, duration=60):
        """Simulate a complete conversation flow with guardrail events"""
        if not conversation_id:
            conversation_id = self.generate_conversation_id()
        
        print(f"\n🎭 Simulating conversation flow for: {conversation_id}")
        print(f"Duration: {duration} seconds")
        print("-" * 50)
        
        # Start conversation
        start_event = self.generate_guardrail_event(conversation_id)
        start_event['event_type'] = 'conversation_started'
        start_event['severity'] = 'info'
        self.send_guardrail_event(conversation_id, start_event)
        
        start_time = time.time()
        event_count = 1
        
        try:
            while (time.time() - start_time) < duration:
                # Generate random guardrail events during conversation
                if random.random() < 0.3:  # 30% chance of event
                    event = self.generate_guardrail_event(conversation_id)
                    # Don't generate start/end events randomly
                    if event['event_type'] not in ['conversation_started', 'conversation_ended']:
                        self.send_guardrail_event(conversation_id, event)
                        event_count += 1
                
                # Simulate operator action (rare)
                if random.random() < 0.05:  # 5% chance
                    action_type = random.choice(['stop_conversation', 'false_alarm', 'escalation'])
                    self.send_operator_action(conversation_id, action_type)
                    event_count += 1
                
                time.sleep(random.uniform(2, 8))  # Random interval between events
            
            # End conversation
            end_event = self.generate_guardrail_event(conversation_id)
            end_event['event_type'] = 'conversation_ended'
            end_event['severity'] = 'info'
            self.send_guardrail_event(conversation_id, end_event)
            event_count += 1
            
        except KeyboardInterrupt:
            print(f"\n⏸️ Conversation simulation stopped")
        
        print(f"\n✅ Conversation {conversation_id} completed with {event_count} events")
        return conversation_id
    
    def start_multi_conversation_simulation(self, num_conversations=3, duration=60):
        """Start multiple concurrent conversation simulations"""
        print(f"\n🚀 Starting {num_conversations} concurrent conversations")
        print(f"Duration: {duration} seconds each")
        print("=" * 60)
        
        import threading
        
        threads = []
        conversation_ids = []

        for i in range(num_conversations):
            # Create a thread for each simulation
            conv_id = self.generate_conversation_id()  # Generate ID upfront
            conversation_ids.append(conv_id)

            thread = threading.Thread(
                target=self.simulate_conversation_flow,
                args=(conv_id, duration),
                daemon=True  # So it exits when main program exits
            )
            threads.append(thread)
            thread.start()
            time.sleep(2)  # Stagger starts

        # Wait for all simulation threads to complete
        print("... all simulations running. Waiting for completion ...")
        for thread in threads:
            thread.join()

        print("✅ All concurrent simulations finished.")
        return conversation_ids
    
    def close(self):
        """Close the producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            self.logger.info("Enhanced Kafka Producer closed")
        
        if self.dlq_producer:
            self.dlq_producer.flush()
            self.dlq_producer.close()
            self.logger.info("DLQ Producer closed")

def main():
    """Main function to run the enhanced producer with async capabilities"""
    print("=" * 60)
    print("🤖 NINA Guardrail Monitor - Enhanced Kafka Producer V2")
    print("🎯 Topic Structure: /guardrail/conversation/{conversation_id}")
    print("⚡ Asynchronous Mode: HIGH THROUGHPUT")
    print("=" * 60)
    
    # Initialize enhanced producer with async mode
    producer = NINAKafkaProducerV2(async_mode=True)
    
    if not producer.producer:
        print("❌ Failed to initialize producer")
        return
    
    try:
        # Test high-throughput async sending
        print("\n📝 Testing high-throughput async conversation flow...")
        conv_id = producer.simulate_conversation_flow(duration=30)
        
        # Test operator actions with async callbacks
        print(f"\n👮 Testing async operator actions for conversation: {conv_id}")
        producer.send_operator_action(conv_id, 'stop_conversation')
        producer.send_operator_action(conv_id, 'false_alarm')
        
        # Test false alarm feedback
        print(f"\n🔄 Testing async false alarm feedback...")
        producer.send_false_alarm_feedback(conv_id, 'event_123', 'This was a legitimate medical question')
        
        # Display statistics
        print(f"\n📊 Producer Statistics:")
        stats = producer.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Flush to ensure all messages are sent
        print("\n🔄 Flushing pending messages...")
        producer.flush()
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Enhanced producer stopped by user")
    finally:
        # Final statistics
        print(f"\n📊 Final Statistics:")
        stats = producer.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        producer.close()

if __name__ == '__main__':
    main()

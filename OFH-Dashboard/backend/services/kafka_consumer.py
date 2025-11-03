#!/usr/bin/env python3
"""
Enhanced Kafka Consumer for NINA Guardrail Monitor
Consumes from static Kafka topics: guardrail_events, operator_actions, guardrail_control
"""

import json
import threading
import logging
import os
import jsonschema  # type: ignore
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer  # type: ignore
from kafka.errors import KafkaError  # type: ignore
from services.database_service import EnhancedDatabaseService
from collections import defaultdict
from services.error_alerting_service import ErrorAlertingService
from config import config, get_kafka_bootstrap_servers, get_kafka_group_id


class NINAKafkaConsumerV2:
    def __init__(self, bootstrap_servers=None, group_id=None, app=None, max_retries=None, on_event_callback=None):
        """Initialize enhanced Kafka consumer with dynamic topic support and DLQ handling"""
        self.bootstrap_servers = bootstrap_servers or get_kafka_bootstrap_servers()
        self.group_id = group_id or get_kafka_group_id()
        self.app = app
        self.on_event_callback = on_event_callback
        self.consumer = None
        self.running = False
        self.db_service = EnhancedDatabaseService()
        self.thread = None
        self.max_retries = max_retries or config.get('MAX_RETRIES')
        self.dlq_producer = None
        
        # Track message processing failures
        self.message_failures = defaultdict(int)
        self.failed_messages = {}

        # Define our static topics
        self.topics = {
            'guardrail_events': os.getenv('KAFKA_TOPIC_GUARDRAIL', 'guardrail_events'),
            'operator_actions': os.getenv('KAFKA_TOPIC_OPERATOR', 'operator_actions'),
            'guardrail_control': os.getenv('KAFKA_TOPIC_CONTROL', 'guardrail_control'),
            'dead_letter_queue': 'dead_letter_queue'
        }

        # Track active conversations
        self.active_conversations = set()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize alerting service
        self.alerting_service = ErrorAlertingService()
        
        # Schema validation setup
        self._schemas = {}  # Cache for loaded schemas
        # Schema directory is one level up from services/ (in backend/)
        self._schema_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas')
    
    def _load_schema(self, schema_name):
        """Loads a JSON schema from the schemas directory, caches it."""
        if schema_name in self._schemas:
            return self._schemas[schema_name]
        try:
            schema_path = os.path.join(self._schema_dir, f"{schema_name}.schema.json")
            with open(schema_path, 'r') as f:
                schema = json.load(f)
                self._schemas[schema_name] = schema
                self.logger.info(f"Loaded schema: {schema_name}")
                return schema
        except FileNotFoundError:
            self.logger.error(f"Schema file not found: {schema_path}")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON schema: {schema_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading schema {schema_name}: {e}", exc_info=True)
            return None

    def _validate_message(self, message_data, schema_name):
        """Validates message data against a loaded schema."""
        schema = self._load_schema(schema_name)
        if not schema:
            self.logger.warning(f"Cannot validate message, schema '{schema_name}' not loaded.")
            return False
        try:
            jsonschema.validate(instance=message_data, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Schema validation failed for {schema_name}: {e.message}")
            self.logger.debug(f"Invalid message snippet: {str(message_data)[:200]}...")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}", exc_info=True)
            return False

    def connect(self):
        """Connect to Kafka broker with topic list subscription"""
        try:
            # Define the list of topics to subscribe to
            topics_to_subscribe = [
                self.topics['guardrail_events'],
                self.topics['operator_actions'],
                self.topics['guardrail_control']
            ]

            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )

            # Initialize DLQ producer for failed messages
            self.dlq_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )

            # Subscribe to the list of topics
            self.consumer.subscribe(topics=topics_to_subscribe)

            self.logger.info(f"Enhanced Kafka Consumer connected to {self.bootstrap_servers}")
            self.logger.info(f"Subscribed to topics: {topics_to_subscribe}")
            self.logger.info(f"Consumer connected with max_retries={self.max_retries}")
            return True
        except KafkaError as e:
            self.logger.error(f"Failed to connect Kafka consumer: {e}", exc_info=True)
            self.alerting_service.alert_kafka_connection_failure(str(e), "Consumer")
            return False

    def _send_to_dlq(self, original_topic, message, key, error, retry_count):
        """Send failed message to dead letter queue"""
        try:
            dlq_message = {
                'original_topic': original_topic,
                'original_message': message,
                'original_key': key,
                'error': str(error),
                'retry_count': retry_count,
                'timestamp': datetime.now().isoformat(),
                'consumer_group': self.group_id
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
            self.logger.critical(f"Failed to send message to DLQ: {dlq_error}", exc_info=True)
            return False
    
    def _should_retry_message(self, message_key, topic_name):
        """Check if message should be retried based on failure count"""
        failure_key = f"{topic_name}:{message_key}"
        failure_count = self.message_failures[failure_key]
        return failure_count < self.max_retries
    
    def _increment_failure_count(self, message_key, topic_name):
        """Increment failure count for a message"""
        failure_key = f"{topic_name}:{message_key}"
        self.message_failures[failure_key] += 1
        return self.message_failures[failure_key]
    
    def _reset_failure_count(self, message_key, topic_name):
        """Reset failure count for successfully processed message"""
        failure_key = f"{topic_name}:{message_key}"
        if failure_key in self.message_failures:
            del self.message_failures[failure_key]

    def _handle_processing_with_retry(self, processing_func, event, conversation_id, message_key, topic_name, event_type_name):
        """
        Centralized retry and DLQ handling wrapper for processing functions.
        This implements DRY principle by consolidating retry/DLQ logic in one place.
        
        Args:
            processing_func: The actual processing function to execute (happy path only)
            event: The event data to process
            conversation_id: The conversation ID
            message_key: The Kafka message key
            topic_name: The Kafka topic name
            event_type_name: Human-readable name for logging (e.g., "guardrail event")
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        # Validate message schema first (this is a quick fail, don't retry)
        schema_name_map = {
            'guardrail event': 'guardrail_event_v1',
            'operator action': 'operator_action_v1'
        }
        schema_name = schema_name_map.get(event_type_name.lower())
        
        if schema_name and not self._validate_message(event, schema_name):
            self.logger.warning(f"Skipping processing invalid {event_type_name} for {conversation_id}")
            return False
        
        # Check if Flask app context is available
        if not self.app:
            self.logger.error(f"Flask app context not available in consumer for {event_type_name}")
            return False

        # Use Flask app context for database operations
        # TODO: Consider decoupling from Flask app context by making EnhancedDatabaseService
        # manage its own SQLAlchemy sessionmaker for better service independence
        with self.app.app_context():
            try:
                # Execute the actual processing logic (happy path)
                success = processing_func(event, conversation_id)
                
                if success:
                    # Reset failure count on successful processing
                    if message_key and topic_name:
                        self._reset_failure_count(message_key, topic_name)
                    return True
                else:
                    # Processing function returned False (may indicate validation failure)
                    return False

            except Exception as e:
                # Handle retry logic for exceptions
                self.logger.error(f"Error processing {event_type_name}: {e}", exc_info=True)
                
                if message_key and topic_name:
                    if self._should_retry_message(message_key, topic_name):
                        retry_count = self._increment_failure_count(message_key, topic_name)
                        self.logger.warning(f"Retrying {event_type_name} processing (attempt {retry_count}/{self.max_retries}): {e}")
                        return False  # Will be retried
                    else:
                        # Max retries exceeded, send to DLQ
                        self.logger.error(f"Max retries exceeded for {event_type_name}, sending to DLQ")
                        self.alerting_service.alert_consumer_processing_failure(topic_name, str(e), self.max_retries)
                        self.alerting_service.alert_dlq_message(topic_name, str(e), self.max_retries)
                        self._send_to_dlq(topic_name, event, message_key, e, self.max_retries)
                        return False
                
                return False

    def _process_guardrail_event_core(self, event, conversation_id):
        """
        Core processing logic for guardrail events (happy path only).
        This method is updated to match guardrail_event_v1.schema.json.
        """
        
        # Extract detection metadata, providing a default if it's null
        detection_meta = event.get('detection_metadata') or {}
        
        # Consolidate all extra details into a single JSONB 'details' column
        # This matches the new schema structure
        event_details = {
            'event_id': event.get('event_id'),
            'context': event.get('context'),
            'action_taken': event.get('action_taken'),
            'confidence_score': event.get('confidence_score'),
            'user_id': event.get('user_id'),
            'guardrail_version': event.get('guardrail_version'),
            'session_metadata': event.get('session_metadata'),
            
            # Add new fields from detection_metadata
            'detection_time_ms': detection_meta.get('detection_time_ms'),
            'model_version': detection_meta.get('model_version'),
            'triggered_rules': detection_meta.get('triggered_rules')
        }

        # Create guardrail event in database using enhanced service
        db_event = self.db_service.create_guardrail_event(
            session_id=conversation_id,
            event_type=event.get('event_type'),
            severity=event.get('severity'),
            message=event.get('message'),
            details=event_details  # Pass the new combined details object
        )

        if db_event:
            self.logger.info(f"Guardrail event saved: {event['event_type']} [{event['severity']}] for conversation {conversation_id}")

            # Handle special events
            if event.get('event_type') == 'conversation_started':
                self.logger.info(f"New conversation started: {conversation_id}")
            elif event.get('event_type') == 'conversation_ended':
                self.logger.info(f"Conversation ended: {conversation_id}")
            
            # Call the callback to notify the frontend after successful processing
            if self.on_event_callback:
                try:
                    self.on_event_callback('guardrail_event', conversation_id, event)
                except Exception as e:
                    self.logger.error(f"Failed to call event callback: {e}", exc_info=True)
            
            return True
        
        return False

    def process_guardrail_event(self, event, conversation_id, message_key=None, topic_name=None):
        """
        Process a guardrail event and save to database with retry logic.
        Uses centralized retry/DLQ handler for cleaner code.
        """
        return self._handle_processing_with_retry(
            processing_func=self._process_guardrail_event_core,
            event=event,
            conversation_id=conversation_id,
            message_key=message_key,
            topic_name=topic_name,
            event_type_name='guardrail event'
        )

    def _process_operator_action_core(self, event, conversation_id):
        """
        Core processing logic for operator actions (happy path only).
        This method contains only the business logic, without retry/DLQ handling.
        """
        action_type = event.get('action_type')
        operator_id = event.get('operator_id')
        message = event.get('message')

        self.logger.info(f"Operator action: {action_type} by {operator_id} for conversation {conversation_id}")
        self.logger.debug(f"Operator action message: {message}")

        # Save operator action to database
        self.db_service.create_operator_action(
            conversation_id=conversation_id,
            action_type=action_type,
            operator_id=operator_id,
            message=message,
            details=event
        )

        # Handle specific actions (logging only, DB update is in db_service)
        if action_type == 'stop_conversation':
            self.logger.info(f"Conversation {conversation_id} stopped by operator")
        elif action_type == 'false_alarm':
            self.logger.info(f"False alarm reported for conversation {conversation_id}")
        elif action_type == 'escalation':
            self.logger.info(f"Conversation {conversation_id} escalated to supervisor")
        
        # Call the callback to notify the frontend after successful processing
        if self.on_event_callback:
            try:
                self.on_event_callback('operator_action', conversation_id, event)
            except Exception as e:
                self.logger.error(f"Failed to call event callback: {e}", exc_info=True)
        
        return True

    def process_operator_action(self, event, conversation_id, message_key=None, topic_name=None):
        """
        Process an operator action event with retry logic.
        Uses centralized retry/DLQ handler for cleaner code.
        """
        return self._handle_processing_with_retry(
            processing_func=self._process_operator_action_core,
            event=event,
            conversation_id=conversation_id,
            message_key=message_key,
            topic_name=topic_name,
            event_type_name='operator action'
        )

    def process_guardrail_control(self, event):
        """Process guardrail control events (false alarm feedback, etc.)"""
        if not self._validate_message(event, "control_feedback_v1"):
            self.logger.warning("Skipping processing invalid control feedback")
            return False
        
        try:
            feedback_type = event.get('feedback_type')
            conversation_id = event.get('conversation_id')

            self.logger.info(f"Guardrail control event: {feedback_type} for conversation {conversation_id}")

            if feedback_type == 'false_alarm':
                original_event_id = event.get('original_event_id')
                feedback = event.get('feedback')
                self.logger.info(f"Original event: {original_event_id}")
                self.logger.info(f"Feedback: {feedback}")

                # Here you would typically update guardrail rules or training data
                self.logger.info("Updating guardrail rules based on feedback")
                
                # Call the callback to notify the frontend after successful processing
                if self.on_event_callback:
                    try:
                        self.on_event_callback('false_alarm_feedback', conversation_id, event)
                    except Exception as e:
                        self.logger.error(f"Failed to call event callback: {e}", exc_info=True)
            
            return True

        except Exception as e:
            self.logger.error(f"Error processing guardrail control event: {e}", exc_info=True)
            return False

    def consume_events(self):
        """Consume events from Kafka topics"""
        if not self.consumer:
            self.logger.error("Consumer not connected")
            return

        self.logger.info("Enhanced Kafka Consumer listening for events...")
        self.running = True

        try:
            while self.running:
                try:
                    # Poll for messages with timeout
                    message_batch = self.consumer.poll(timeout_ms=1000)

                    if not message_batch:
                        continue

                    for topic_partition, messages in message_batch.items():
                        topic_name = topic_partition.topic

                        for message in messages:
                            if not self.running:
                                break

                            event = message.value
                            message_key = message.key.decode('utf-8') if message.key else None

                            # Get conversation_id from the EVENT BODY (or the key as a fallback)
                            conversation_id = event.get('conversation_id', message_key)

                            if not conversation_id:
                                self.logger.warning(f"Message received on topic {topic_name} with no 'conversation_id'. Skipping.")
                                continue

                            # Route based on topic name
                            if topic_name == self.topics['guardrail_events']:
                                success = self.process_guardrail_event(
                                    event, conversation_id, message_key, topic_name)

                                if not success and self._should_retry_message(message_key, topic_name):
                                    continue

                            elif topic_name == self.topics['operator_actions']:
                                success = self.process_operator_action(
                                    event, conversation_id, message_key, topic_name)

                                if not success and self._should_retry_message(message_key, topic_name):
                                    continue

                            elif topic_name == self.topics['guardrail_control']:
                                self.process_guardrail_control(event)

                            else:
                                self.logger.warning(f"Unknown topic: {topic_name}")

                except Exception as e:
                    if self.running:  # Only log errors if we're supposed to be running
                        self.logger.error(f"Error in message processing: {e}", exc_info=True)
                    continue

        except Exception as e:
            self.logger.error(f"Error consuming events: {e}", exc_info=True)
        finally:
            self.stop()

    def start(self):
        """Start consuming events in a background thread"""
        if self.connect():  # Try connecting first
            # Create and start the background thread
            self.thread = threading.Thread(target=self.consume_events, daemon=True)
            self.thread.start()
            self.logger.info("Enhanced Kafka consumer started in background")
            return True  # Indicate success
        # If connect() failed
        self.logger.error("Failed to start consumer due to connection error")
        return False  # Indicate failure

    def start_consumer(self):
        """Public method to start the consumer - used by integration service"""
        return self.start()

    def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            self.logger.info("Enhanced Kafka consumer stopped")
        
        if self.dlq_producer:
            self.dlq_producer.flush()
            self.dlq_producer.close()
            self.logger.info("DLQ Producer closed")

    def is_running(self):
        """Check if consumer is running"""
        return self.running

    def get_active_conversations(self):
        """Get list of active conversations"""
        return list(self.active_conversations)


def main():
    """Main function to run the enhanced consumer"""
    import time
    
    print("=" * 60)
    print("🎧 NINA Guardrail Monitor - Enhanced Kafka Consumer V2")
    print("🎯 Topics: guardrail_events, operator_actions, guardrail_control")
    print("=" * 60)

    # Initialize enhanced consumer
    consumer = NINAKafkaConsumerV2()

    # Start consuming
    if consumer.start():
        try:
            print("\n🎧 Consumer started with topic list subscription")
            print("📡 Monitoring topics:", consumer.topics)
            print("Press Ctrl+C to stop...")

            # Keep running
            while consumer.is_running():
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⏸️ Enhanced consumer stopped by user")
            consumer.stop()


if __name__ == '__main__':
    main()

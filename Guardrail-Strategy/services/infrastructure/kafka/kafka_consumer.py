#!/usr/bin/env python3
"""
Kafka Consumer for Guardrail Service
Consumes guardrail_control topic to receive feedback from dashboard
"""

import json
import threading
import logging
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError, KafkaTimeoutError, KafkaConnectionError, NoBrokersAvailable
from shared.guardrail_schemas import GuardrailControlFeedback

logger = logging.getLogger(__name__)

# Import feedback learner if available
try:
    from services.learning.feedback_learner import FeedbackLearner
    FEEDBACK_LEARNER_AVAILABLE = True
except ImportError:
    FEEDBACK_LEARNER_AVAILABLE = False
    logger.warning("FeedbackLearner not available - feedback will not be used for learning")


class GuardrailKafkaConsumer:
    """Kafka consumer for guardrail control feedback with resilient connection handling"""
    
    def __init__(self, bootstrap_servers=None, group_id=None):
        """Initialize Kafka consumer (lazy connection)"""
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.group_id = group_id or os.getenv('KAFKA_GROUP_ID', 'guardrail-strategy-service')
        self.control_topic = os.getenv('KAFKA_TOPIC_CONTROL', 'guardrail_control')
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._last_connection_attempt = 0
        self._connection_retry_delay = 5  # seconds
        
        # Initialize feedback learner for adaptive learning
        self.feedback_learner = None
        if FEEDBACK_LEARNER_AVAILABLE:
            try:
                self.feedback_learner = FeedbackLearner()
                logger.info("✅ Feedback learner initialized - adaptive learning enabled")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize feedback learner: {e}")
        
        # Legacy tracking (for backward compatibility)
        self.false_alarm_feedback = []
        self.feedback_count = 0
        
    def _try_connect(self, initial=False):
        """Try to connect to Kafka broker with retry logic"""
        # Don't retry too frequently
        current_time = time.time()
        if not initial and (current_time - self._last_connection_attempt) < self._connection_retry_delay:
            return False
            
        self._last_connection_attempt = current_time
        
        try:
            consumer_config = {
                'bootstrap_servers': self.bootstrap_servers,
                'group_id': self.group_id,
                'value_deserializer': lambda m: json.loads(m.decode('utf-8')),
                'auto_offset_reset': 'earliest',
                'enable_auto_commit': True,
                'consumer_timeout_ms': 5000,
                'api_version_auto_timeout_ms': 10000,
                'session_timeout_ms': 10000,  # Default session timeout
                'request_timeout_ms': 30000,  # Must be > session_timeout_ms (30s > 10s)
            }
            
            self.consumer = KafkaConsumer(self.control_topic, **consumer_config)
            self._connection_attempts = 0
            logger.info(f"✅ Kafka Consumer connected to {self.bootstrap_servers}, subscribed to {self.control_topic}")
            return True
        except (KafkaError, NoBrokersAvailable) as e:
            self._connection_attempts += 1
            if initial:
                logger.warning(
                    f"⚠️ Could not connect to Kafka consumer at startup ({self.bootstrap_servers}). "
                    f"Service will continue without consuming control feedback. "
                    f"Error: {e}"
                )
            else:
                logger.warning(f"⚠️ Kafka consumer connection attempt {self._connection_attempts} failed: {e}")
            self.consumer = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting Kafka consumer: {e}", exc_info=True)
            self.consumer = None
            return False
    
    def _ensure_connected(self):
        """Ensure consumer is connected, try to reconnect if needed"""
        if self.consumer is not None:
            return True
        
        # Try to reconnect if we haven't exceeded max attempts
        if self._connection_attempts < self._max_connection_attempts:
            return self._try_connect()
        
        return False
    
    def _process_control_feedback(self, feedback: Dict[str, Any]) -> bool:
        """
        Process guardrail control feedback (false alarms, etc.)
        
        Args:
            feedback: The control feedback message from dashboard
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            typed_feedback = GuardrailControlFeedback(**{
                key: value for key, value in feedback.items()
                if key in GuardrailControlFeedback.__dataclass_fields__
            })
            feedback_dict = typed_feedback.to_dict()

            feedback_type = feedback_dict.get('feedback_type', 'unknown')
            conversation_id = feedback_dict.get('conversation_id', 'unknown')
            original_event_id = feedback_dict.get('original_event_id')
            feedback_content = feedback_dict.get('feedback_content', '')

            logger.info(
                f"📥 Received guardrail control feedback: {feedback_type} "
                f"for conversation {conversation_id}"
            )
            
            if feedback_type == 'false_alarm':
                # Process false alarm feedback
                self.feedback_count += 1
                feedback_entry = {
                    'conversation_id': conversation_id,
                    'original_event_id': original_event_id,
                    'feedback': feedback_content,
                    'timestamp': datetime.now().isoformat(),
                    'source': feedback.get('feedback_source', 'operator')
                }
                self.false_alarm_feedback.append(feedback_entry)
                
                # Use feedback learner if available
                if self.feedback_learner:
                    # Extract triggered rules from feedback metadata if available
                    feedback_metadata = feedback.get('feedback_metadata', {})
                    context = feedback.get('context', {})
                    
                    # Try to get triggered rules from various sources
                    triggered_rules = []
                    validator_type = None
                    
                    if 'triggered_rules' in feedback_metadata:
                        triggered_rules = feedback_metadata['triggered_rules']
                    elif 'triggered_rules' in context:
                        triggered_rules = context['triggered_rules']
                    elif 'detection_metadata' in feedback:
                        detection_meta = feedback.get('detection_metadata', {})
                        triggered_rules = detection_meta.get('triggered_rules', [])
                    
                    # Try to infer validator type from event type or rules
                    event_type = feedback.get('event_type', '')
                    if 'pii' in event_type.lower() or 'DetectPII' in str(triggered_rules):
                        validator_type = 'pii'
                    elif 'toxic' in event_type.lower() or 'ToxicLanguage' in str(triggered_rules):
                        validator_type = 'toxicity'
                    elif 'compliance' in event_type.lower() or 'Compliance' in str(triggered_rules):
                        validator_type = 'compliance'
                    elif 'context' in event_type.lower() or 'LLM' in str(triggered_rules):
                        validator_type = 'llm_context'
                    
                    # Record false alarm for learning
                    self.feedback_learner.record_false_alarm(
                        conversation_id=conversation_id,
                        original_event_id=original_event_id,
                        feedback_content=feedback_content,
                        triggered_rules=triggered_rules if triggered_rules else ['Unknown'],
                        validator_type=validator_type
                    )
                    
                    logger.info(
                        f"📚 False alarm recorded for learning. Rules: {triggered_rules}. "
                        f"Validator: {validator_type}"
                    )
                
                logger.info(
                    f"✅ False alarm feedback processed for {conversation_id}. "
                    f"Total feedback received: {self.feedback_count}"
                )
                
            elif feedback_type == 'true_positive':
                logger.info(f"✅ True positive confirmed for {conversation_id}")
                
                # Record true positive for learning
                if self.feedback_learner:
                    event_id = feedback.get('original_event_id') or original_event_id
                    triggered_rules = []
                    
                    # Extract triggered rules
                    feedback_metadata = feedback.get('feedback_metadata', {})
                    if 'triggered_rules' in feedback_metadata:
                        triggered_rules = feedback_metadata['triggered_rules']
                    
                    validator_type = None
                    event_type = feedback.get('event_type', '')
                    if 'pii' in event_type.lower():
                        validator_type = 'pii'
                    elif 'toxic' in event_type.lower():
                        validator_type = 'toxicity'
                    elif 'compliance' in event_type.lower():
                        validator_type = 'compliance'
                    elif 'context' in event_type.lower():
                        validator_type = 'llm_context'
                    
                    self.feedback_learner.record_true_positive(
                        conversation_id=conversation_id,
                        event_id=event_id or 'unknown',
                        triggered_rules=triggered_rules if triggered_rules else ['Unknown'],
                        validator_type=validator_type
                    )
                
            elif feedback_type == 'guardrail_adjustment':
                logger.info(f"⚙️ Guardrail adjustment requested for {conversation_id}")
                # Could use this to update rules dynamically
                
            else:
                logger.info(f"ℹ️ Received {feedback_type} feedback for {conversation_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing control feedback: {e}", exc_info=True)
            return False
    
    def _consume_messages(self):
        """Consume messages from Kafka in a loop"""
        logger.info(f"🔄 Starting to consume messages from {self.control_topic}")
        
        while self.running:
            try:
                # Ensure connection
                if not self._ensure_connected():
                    if self.running:
                        logger.debug("Kafka not available, waiting before retry...")
                        time.sleep(10)  # Wait before retrying
                    continue
                
                # Poll for messages with timeout
                message_pack = self.consumer.poll(timeout_ms=5000)
                
                if message_pack:
                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            try:
                                feedback = message.value
                                if feedback:
                                    self._process_control_feedback(feedback)
                            except Exception as e:
                                logger.error(f"Error processing message: {e}", exc_info=True)
                
            except (KafkaError, KafkaConnectionError, NoBrokersAvailable) as e:
                logger.warning(f"⚠️ Kafka consumer error: {e}")
                self.consumer = None  # Mark as disconnected
                if self.running:
                    time.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error in consumer loop: {e}", exc_info=True)
                if self.running:
                    time.sleep(5)
        
        logger.info("🛑 Consumer loop stopped")
    
    def start(self):
        """Start consuming messages in a background thread"""
        if self.running:
            logger.warning("Consumer is already running")
            return True
        
        logger.info("🚀 Starting Kafka consumer for guardrail control feedback...")
        
        # Try to connect first
        if not self._try_connect(initial=True):
            logger.warning(
                "⚠️ Could not connect to Kafka. Consumer will not start. "
                "Service will continue without control feedback."
            )
            return False
        
        self.running = True
        self.thread = threading.Thread(
            target=self._consume_messages,
            daemon=True,
            name="GuardrailControlConsumer"
        )
        self.thread.start()
        
        logger.info("✅ Kafka consumer started in background thread")
        return True
    
    def stop(self):
        """Stop the consumer"""
        logger.info("🛑 Stopping Kafka consumer...")
        self.running = False
        
        if self.consumer:
            try:
                self.consumer.close(timeout=5)
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.warning(f"Error closing consumer: {e}")
            finally:
                self.consumer = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            logger.info("Consumer thread stopped")
    
    def is_running(self) -> bool:
        """Check if consumer is running"""
        return self.running and self.consumer is not None
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics about received feedback"""
        stats = {
            'total_feedback': self.feedback_count,
            'false_alarms': len(self.false_alarm_feedback),
            'consumer_running': self.is_running(),
            'topic': self.control_topic
        }
        
        # Add learning statistics if available
        if self.feedback_learner:
            learning_stats = self.feedback_learner.get_statistics()
            stats['learning'] = {
                'enabled': True,
                'total_feedback': learning_stats['total_feedback'],
                'false_alarm_rate': learning_stats['false_alarm_rate'],
                'rules_tracked': learning_stats['rules_tracked'],
                'threshold_adjustments': learning_stats['threshold_adjustments'],
                'problematic_rules_count': len(learning_stats['problematic_rules'])
            }
        else:
            stats['learning'] = {'enabled': False}
        
        return stats


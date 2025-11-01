#!/usr/bin/env python3
"""
Kafka Producer for Guardrail Service
Publishes guardrail events to Kafka topics
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os

logger = logging.getLogger(__name__)


class GuardrailKafkaProducer:
    """Kafka producer for guardrail events"""
    
    def __init__(self, bootstrap_servers=None):
        """Initialize Kafka producer"""
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.producer = None
        self.topic_pattern = os.getenv('KAFKA_OUTPUT_TOPIC_PATTERN', 'guardrail.conversation.{conversation_id}')
        self.connect()
    
    def connect(self):
        """Connect to Kafka broker"""
        try:
            producer_config = {
                'bootstrap_servers': self.bootstrap_servers,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'retries': 3,
                'retry_backoff_ms': 1000,
                'request_timeout_ms': 30000,
                'delivery_timeout_ms': 120000,
                'acks': 'all',  # Wait for all replicas
                'enable_idempotence': True
            }
            
            self.producer = KafkaProducer(**producer_config)
            logger.info(f"Kafka Producer connected to {self.bootstrap_servers}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}", exc_info=True)
            return False
    
    def get_topic_name(self, conversation_id: str) -> str:
        """Generate topic name from conversation ID"""
        return self.topic_pattern.format(conversation_id=conversation_id)
    
    def send_guardrail_event(self, conversation_id: str, event: Dict[str, Any]) -> bool:
        """
        Send guardrail event to Kafka
        
        Args:
            conversation_id: The conversation ID
            event: The guardrail event dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.producer:
            logger.error("Producer not connected")
            return False
        
        topic = self.get_topic_name(conversation_id)
        
        try:
            # Ensure event has required fields
            event['conversation_id'] = conversation_id
            event['timestamp'] = event.get('timestamp', datetime.now().isoformat())
            
            # Send message
            future = self.producer.send(topic, value=event, key=conversation_id)
            
            # Wait for acknowledgment (with timeout)
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Guardrail event sent to {topic}[{record_metadata.partition}] "
                f"@ offset {record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to send guardrail event to {topic}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending guardrail event: {e}", exc_info=True)
            return False
    
    def flush(self):
        """Flush all pending messages"""
        if self.producer:
            self.producer.flush()
            logger.info("Producer flushed - all pending messages sent")
    
    def close(self):
        """Close the producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka Producer closed")


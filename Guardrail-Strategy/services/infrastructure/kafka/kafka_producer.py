#!/usr/bin/env python3
"""
Kafka Producer for Guardrail Service
Publishes guardrail events to Kafka topics
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable
import os

logger = logging.getLogger(__name__)


class GuardrailKafkaProducer:
    """Kafka producer for guardrail events with resilient connection handling"""
    
    def __init__(self, bootstrap_servers=None):
        """Initialize Kafka producer (lazy connection - doesn't connect immediately)"""
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.producer: Optional[KafkaProducer] = None
        self.topic = os.getenv('KAFKA_OUTPUT_TOPIC', 'guardrail_events')
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._last_connection_attempt = 0
        self._connection_retry_delay = 5  # seconds
        
        # Try to connect, but don't fail if it doesn't work
        self._try_connect(initial=True)
    
    def _try_connect(self, initial=False):
        """Try to connect to Kafka broker with retry logic"""
        # Don't retry too frequently
        current_time = time.time()
        if not initial and (current_time - self._last_connection_attempt) < self._connection_retry_delay:
            return False
            
        self._last_connection_attempt = current_time
        
        try:
            producer_config = {
                'bootstrap_servers': self.bootstrap_servers,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'retries': 2,
                'retry_backoff_ms': 500,
                'request_timeout_ms': 5000,  # Reduced from 30000 for faster failure
                'metadata_max_age_ms': 30000,
                'delivery_timeout_ms': 30000,  # Reduced timeout
                'acks': 1,  # Changed from 'all' to 1 for faster acknowledgment
                'enable_idempotence': False,  # Disable for faster connection
                'max_block_ms': 5000,  # Max time to block on send
                'api_version_auto_timeout_ms': 5000,  # Timeout for API version check
            }
            
            self.producer = KafkaProducer(**producer_config)
            self._connection_attempts = 0
            logger.info(f"✅ Kafka Producer connected to {self.bootstrap_servers}")
            return True
        except (KafkaError, NoBrokersAvailable) as e:
            self._connection_attempts += 1
            if initial:
                logger.warning(
                    f"⚠️ Could not connect to Kafka at startup ({self.bootstrap_servers}). "
                    f"Service will continue without Kafka. Events will be logged but not sent. "
                    f"Error: {e}"
                )
            else:
                logger.warning(f"⚠️ Kafka connection attempt {self._connection_attempts} failed: {e}")
            self.producer = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Kafka: {e}", exc_info=True)
            self.producer = None
            return False
    
    def _ensure_connected(self):
        """Ensure producer is connected, try to reconnect if needed"""
        if self.producer is not None:
            return True
        
        # Try to reconnect if we haven't exceeded max attempts
        if self._connection_attempts < self._max_connection_attempts:
            return self._try_connect()
        
        return False
    
    def send_guardrail_event(self, conversation_id: str, event: Dict[str, Any]) -> bool:
        """
        Send guardrail event to Kafka with automatic reconnection
        
        Args:
            conversation_id: The conversation ID
            event: The guardrail event dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Try to ensure connection before sending
        if not self._ensure_connected():
            logger.debug(f"Kafka not available, skipping event for {conversation_id}")
            return False
        
        topic = self.topic
        
        try:
            # Ensure event has required fields
            event['conversation_id'] = conversation_id
            event['timestamp'] = event.get('timestamp', datetime.now().isoformat())
            
            # Send message (non-blocking with callback)
            future = self.producer.send(topic, value=event, key=conversation_id)
            
            # Wait for acknowledgment with shorter timeout
            try:
                record_metadata = future.get(timeout=5)  # Reduced timeout
                logger.debug(
                    f"✅ Guardrail event sent to {topic}[{record_metadata.partition}] "
                    f"@ offset {record_metadata.offset}"
                )
                return True
            except Exception as timeout_error:
                # If timeout, the message might still be sent (async), but we can't confirm
                logger.warning(f"⚠️ Kafka send timeout for {conversation_id}, message may still be queued")
                return False
                
        except (KafkaError, NoBrokersAvailable) as e:
            logger.warning(f"⚠️ Kafka error sending event to {topic}: {e}")
            # Mark producer as disconnected so we'll try to reconnect next time
            self.producer = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending guardrail event: {e}", exc_info=True)
            return False
    
    def flush(self):
        """Flush all pending messages"""
        if self.producer:
            try:
                self.producer.flush(timeout=5)
                logger.debug("Producer flushed - all pending messages sent")
            except Exception as e:
                logger.warning(f"Error flushing producer: {e}")
    
    def close(self):
        """Close the producer connection"""
        if self.producer:
            try:
                self.producer.flush(timeout=5)
                self.producer.close(timeout=5)
                logger.info("Kafka Producer closed")
            except Exception as e:
                logger.warning(f"Error closing producer: {e}")
            finally:
                self.producer = None


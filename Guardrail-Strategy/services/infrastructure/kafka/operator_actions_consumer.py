#!/usr/bin/env python3
"""
Simple Kafka Consumer for Operator Actions
Consumes from operator_actions topic and logs events for evidence tracking
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

logger = logging.getLogger(__name__)


class OperatorActionsConsumer:
    """
    Simple consumer for operator_actions topic.
    Logs all operator actions for evidence tracking.
    No actual actions are performed - just logging.
    """
    
    def __init__(self, bootstrap_servers=None, group_id=None):
        """Initialize Kafka consumer (lazy connection)"""
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.group_id = group_id or os.getenv('KAFKA_GROUP_ID_OPERATOR_ACTIONS', 'guardrail-strategy-operator-actions')
        self.operator_actions_topic = os.getenv('KAFKA_TOPIC_OPERATOR', 'operator_actions')
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        self._last_connection_attempt = 0
        self._connection_retry_delay = 5  # seconds
        
        # Track received actions for statistics
        self.action_count = 0
        self.actions_by_type = {}
        
    def _value_deserializer(self, raw_value):
        """Safely decode JSON payloads consumed from Kafka."""
        if raw_value is None:
            return None
        try:
            text = raw_value.decode('utf-8')
        except Exception as decode_error:
            logger.warning(f"Failed to decode Kafka message bytes: {decode_error}")
            return None
        text = text.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as json_error:
            preview = text[:200] + ("..." if len(text) > 200 else "")
            logger.warning(f"Failed to JSON-deserialize operator action message: {json_error}. Payload preview: {preview}")
            return None
        
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
                'value_deserializer': self._value_deserializer,
                'key_deserializer': lambda k: k.decode('utf-8') if k else None,
                'auto_offset_reset': 'latest',  # Start from latest messages
                'enable_auto_commit': True,
                'consumer_timeout_ms': int(os.getenv('KAFKA_CONSUMER_TIMEOUT_MS', '5000')),
                'api_version_auto_timeout_ms': int(os.getenv('KAFKA_CONSUMER_API_TIMEOUT_MS', '10000')),
                'session_timeout_ms': int(os.getenv('KAFKA_CONSUMER_SESSION_TIMEOUT_MS', '10000')),
                'request_timeout_ms': int(os.getenv('KAFKA_CONSUMER_REQUEST_TIMEOUT_MS', '30000')),
            }
            
            self.consumer = KafkaConsumer(self.operator_actions_topic, **consumer_config)
            self._connection_attempts = 0
            logger.info(f"✅ Operator Actions Consumer connected to {self.bootstrap_servers}, subscribed to {self.operator_actions_topic}")
            return True
        except (KafkaError, NoBrokersAvailable) as e:
            self._connection_attempts += 1
            if initial:
                logger.warning(
                    f"⚠️ Could not connect to Kafka consumer for operator_actions at startup ({self.bootstrap_servers}). "
                    f"Service will continue without consuming operator actions. "
                    f"Error: {e}"
                )
            else:
                logger.warning(f"⚠️ Operator actions consumer connection attempt {self._connection_attempts} failed: {e}")
            self.consumer = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting operator actions consumer: {e}", exc_info=True)
            self.consumer = None
            return False
    
    def _ensure_connected(self):
        """Ensure consumer is connected, try to reconnect if needed"""
        if self.consumer is not None:
            return True

        if not self.running:
            return False

        # Always attempt to reconnect with built-in retry delay
        return self._try_connect()
    
    def _process_operator_action(self, action: Dict[str, Any]) -> bool:
        """
        Process operator action - just log it for evidence tracking.
        No actual actions are performed.
        
        Args:
            action: The operator action message from dashboard
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Extract key information
            action_type = action.get('action_type', 'unknown')
            conversation_id = action.get('conversation_id', 'unknown')
            operator_id = action.get('operator_id', 'unknown')
            timestamp = action.get('timestamp', datetime.now().isoformat())
            message = action.get('message', '')
            reason = action.get('reason', '')
            priority = action.get('priority', 'normal')
            
            # Update statistics
            self.action_count += 1
            self.actions_by_type[action_type] = self.actions_by_type.get(action_type, 0) + 1
            
            # Log the operator action for evidence tracking
            logger.info(
                f"📋 OPERATOR ACTION RECEIVED - Evidence Logged:\n"
                f"   Action Type: {action_type}\n"
                f"   Conversation ID: {conversation_id}\n"
                f"   Operator ID: {operator_id}\n"
                f"   Timestamp: {timestamp}\n"
                f"   Priority: {priority}\n"
                f"   Message: {message}\n"
                f"   Reason: {reason if reason else 'N/A'}\n"
                f"   Total Actions Received: {self.action_count}"
            )
            
            # Log additional context if available
            command = action.get('command')
            if command:
                logger.debug(f"   Command Details: {json.dumps(command, indent=2)}")
            
            system_context = action.get('system_context')
            if system_context:
                risk_level = system_context.get('risk_level', 'N/A')
                conversation_state = system_context.get('conversation_state', 'N/A')
                logger.debug(f"   System Context - Risk Level: {risk_level}, State: {conversation_state}")
            
            # Log action metadata if available
            action_metadata = action.get('action_metadata')
            if action_metadata:
                logger.debug(f"   Action Metadata: {json.dumps(action_metadata, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing operator action: {e}", exc_info=True)
            return False
    
    def _consume_messages(self):
        """Consume messages from Kafka in a loop"""
        logger.info(f"🔄 Starting to consume operator actions from {self.operator_actions_topic}")
        
        while self.running:
            try:
                # Ensure connection
                if not self._ensure_connected():
                    if self.running:
                        logger.debug("Kafka not available for operator actions, waiting before retry...")
                        time.sleep(10)  # Wait before retrying
                    continue
                
                # Poll for messages with timeout
                message_pack = self.consumer.poll(timeout_ms=5000)
                
                if message_pack:
                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            try:
                                action = message.value
                                if action:
                                    self._process_operator_action(action)
                            except Exception as e:
                                logger.error(f"Error processing operator action message: {e}", exc_info=True)
                
            except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                # Handle connection reset/aborted errors gracefully
                logger.warning(
                    f"⚠️ Kafka connection reset/aborted for operator actions: {e}. Attempting to reconnect..."
                )
                # Close the current consumer
                try:
                    if self.consumer:
                        self.consumer.close()
                except Exception as close_error:
                    logger.debug(f"Error closing operator actions consumer: {close_error}")
                self.consumer = None
                
                # Attempt to reconnect
                if self.running:
                    if self._try_connect():
                        logger.info("✅ Successfully reconnected to Kafka after connection reset (operator actions)")
                    else:
                        logger.warning(
                            "⚠️ Reconnection failed. Will retry on next poll cycle."
                        )
                        time.sleep(5)  # Wait before next attempt
            except (KafkaError, KafkaConnectionError, KafkaTimeoutError, NoBrokersAvailable) as e:
                logger.warning(f"⚠️ Operator actions consumer error: {e}. Attempting to reconnect...")
                # Close the current consumer
                try:
                    if self.consumer:
                        self.consumer.close()
                except Exception as close_error:
                    logger.debug(f"Error closing operator actions consumer: {close_error}")
                self.consumer = None  # Mark as disconnected
                
                # Attempt to reconnect
                if self.running:
                    if self._try_connect():
                        logger.info("✅ Successfully reconnected to Kafka (operator actions)")
                    else:
                        logger.warning(
                            "⚠️ Reconnection failed. Will retry on next poll cycle."
                        )
                        time.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error in operator actions consumer loop: {e}", exc_info=True)
                if self.running:
                    time.sleep(5)
        
        logger.info("🛑 Operator actions consumer loop stopped")
    
    def start(self):
        """Start consuming messages in a background thread"""
        if self.running:
            logger.warning("Operator actions consumer is already running")
            return True
        
        logger.info("🚀 Starting Kafka consumer for operator actions...")
        
        initial_connected = self._try_connect(initial=True)
        if not initial_connected:
            logger.warning(
                "⚠️ Could not connect to Kafka for operator actions at startup. "
                "Will continue retrying in the background."
            )

        self.running = True
        self.thread = threading.Thread(
            target=self._consume_messages,
            daemon=True,
            name="OperatorActionsConsumer"
        )
        self.thread.start()
        
        logger.info("✅ Operator actions consumer started in background thread")
        return initial_connected
    
    def stop(self):
        """Stop the consumer"""
        logger.info("🛑 Stopping operator actions consumer...")
        self.running = False
        
        if self.consumer:
            try:
                self.consumer.close(timeout=5)
                logger.info("Operator actions consumer closed")
            except Exception as e:
                logger.warning(f"Error closing operator actions consumer: {e}")
            finally:
                self.consumer = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            logger.info("Operator actions consumer thread stopped")
    
    def is_running(self) -> bool:
        """Check if consumer is running"""
        return self.running and self.consumer is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about received operator actions"""
        return {
            'total_actions': self.action_count,
            'actions_by_type': dict(self.actions_by_type),
            'consumer_running': self.is_running(),
            'topic': self.operator_actions_topic
        }

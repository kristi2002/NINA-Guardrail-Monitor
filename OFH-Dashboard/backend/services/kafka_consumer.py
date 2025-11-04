#!/usr/bin/env python3
"""
Enhanced Kafka Consumer for NINA Guardrail Monitor
Consumes from static Kafka topics: guardrail_events, operator_actions, guardrail_control
"""

import json
import threading
import logging
import os
import socket
import time
import jsonschema  # type: ignore
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError, KafkaConnectionError
from services.database_service import EnhancedDatabaseService
from collections import defaultdict
from services.error_alerting_service import ErrorAlertingService
from config import config, get_kafka_bootstrap_servers, get_kafka_group_id


class NINAKafkaConsumerV2:
    def __init__(
        self,
        bootstrap_servers=None,
        group_id=None,
        app=None,
        db=None,
        max_retries=None,
        on_event_callback=None,
    ):
        """Initialize enhanced Kafka consumer with dynamic topic support and DLQ handling"""
        self.bootstrap_servers = bootstrap_servers or get_kafka_bootstrap_servers()
        self.group_id = group_id or get_kafka_group_id()
        self.app = app
        self.db = db  # Store the db instance
        self.on_event_callback = on_event_callback
        self.consumer = None
        self.running = False

        # --- MODIFICATION: Pass 'db' to the service ---
        if not db:
            logging.critical("NINAKafkaConsumerV2 initialized without 'db' instance!")
        self.db_service = EnhancedDatabaseService(db=self.db, app=self.app)
        self.thread = None
        self.max_retries = max_retries or config.get("MAX_RETRIES")
        self.dlq_producer = None

        # Track message processing failures
        self.message_failures = defaultdict(int)
        self.failed_messages = {}

        # Define our static topics
        self.topics = {
            "guardrail_events": os.getenv("KAFKA_TOPIC_GUARDRAIL", "guardrail_events"),
            "operator_actions": os.getenv("KAFKA_TOPIC_OPERATOR", "operator_actions"),
            "guardrail_control": os.getenv("KAFKA_TOPIC_CONTROL", "guardrail_control"),
            "dead_letter_queue": "dead_letter_queue",
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
        self._schema_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "schemas"
        )

    def _load_schema(self, schema_name):
        """Loads a JSON schema from the schemas directory, caches it."""
        if schema_name in self._schemas:
            return self._schemas[schema_name]
        try:
            schema_path = os.path.join(self._schema_dir, f"{schema_name}.schema.json")
            with open(schema_path, "r") as f:
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
            self.logger.warning(
                f"Cannot validate message, schema '{schema_name}' not loaded."
            )
            return False
        try:
            jsonschema.validate(instance=message_data, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:  # type: ignore
            self.logger.error(
                f"Schema validation failed for {schema_name}: {e.message}"
            )
            self.logger.debug(f"Invalid message snippet: {str(message_data)[:200]}...")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}", exc_info=True)
            return False

    def _validate_bootstrap_servers(self, bootstrap_servers):
        """Validate bootstrap_servers format and connectivity"""
        try:
            # Parse bootstrap_servers (could be comma-separated list)
            servers = bootstrap_servers.split(",")
            for server in servers:
                server = server.strip()
                if ":" not in server:
                    raise ValueError(
                        f"Invalid bootstrap server format: {server}. Expected 'host:port'"
                    )
                host, port = server.rsplit(":", 1)
                try:
                    port = int(port)
                except ValueError:
                    raise ValueError(f"Invalid port in bootstrap server: {server}")

                # Try to resolve hostname
                try:
                    socket.gethostbyname(host)
                except socket.gaierror as e:
                    self.logger.warning(f"DNS resolution failed for {host}: {e}")
                    # Continue anyway, might be a transient DNS issue

            return True
        except Exception as e:
            self.logger.error(f"Bootstrap server validation failed: {e}", exc_info=True)
            return False

    def _check_kafka_connectivity(self, bootstrap_servers, timeout=5):
        """Check if Kafka broker is reachable"""
        try:
            servers = bootstrap_servers.split(",")
            for server in servers:
                server = server.strip()
                host, port = server.rsplit(":", 1)
                port = int(port)

                # Try to connect to the broker
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                try:
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        self.logger.info(
                            f"Successfully connected to Kafka broker at {host}:{port}"
                        )
                        return True
                    else:
                        self.logger.warning(
                            f"Failed to connect to {host}:{port} (error code: {result})"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Socket connection test failed for {host}:{port}: {e}"
                    )
                    sock.close()
            return False
        except Exception as e:
            self.logger.error(f"Error checking Kafka connectivity: {e}", exc_info=True)
            return False

    def connect(self, retry_count=3, retry_delay=2):
        """Connect to Kafka broker with topic list subscription and retry logic"""
        # Validate bootstrap servers format first
        if not self._validate_bootstrap_servers(self.bootstrap_servers):
            self.logger.error(
                f"Invalid bootstrap servers configuration: {self.bootstrap_servers}"
            )
            return False

        # Check Kafka connectivity before attempting connection
        if not self._check_kafka_connectivity(self.bootstrap_servers):
            self.logger.error(
                f"Kafka broker is not reachable at {self.bootstrap_servers}"
            )
            self.logger.error("Please ensure Kafka is running and accessible")
            self.alerting_service.alert_kafka_connection_failure(
                f"Kafka broker not reachable at {self.bootstrap_servers}", "Consumer"
            )
            return False

        # Retry connection logic
        last_error = None
        for attempt in range(retry_count):
            try:
                if attempt > 0:
                    self.logger.info(
                        f"Retrying Kafka connection (attempt {attempt + 1}/{retry_count})..."
                    )
                    time.sleep(retry_delay)

                # Define the list of topics to subscribe to
                # Only subscribe to topics that exist (guardrail_control may not exist)
                topics_to_subscribe = [
                    self.topics["guardrail_events"],
                    self.topics["operator_actions"],
                    # Note: guardrail_control is optional - only subscribe if topic exists
                ]

                self.logger.info(
                    f"Attempting to create Kafka consumer for {self.bootstrap_servers}..."
                )

                self.consumer = KafkaConsumer(
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                    consumer_timeout_ms=5000,  # Increased from 1000 to 5000ms
                    session_timeout_ms=30000,  # 30 seconds
                    heartbeat_interval_ms=10000,  # 10 seconds
                    max_poll_interval_ms=300000,  # 5 minutes
                    fetch_min_bytes=1,
                    fetch_max_wait_ms=500,
                )

                self.logger.info("Kafka consumer created, initializing DLQ producer...")

                # Initialize DLQ producer for failed messages
                try:
                    self.dlq_producer = KafkaProducer(
                        bootstrap_servers=self.bootstrap_servers,
                        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                        key_serializer=lambda k: k.encode("utf-8") if k else None,
                    )
                    self.logger.info("DLQ producer initialized successfully")
                except Exception as dlq_error:
                    self.logger.error(
                        f"Failed to create DLQ producer: {dlq_error}", exc_info=True
                    )
                    # Continue without DLQ producer - consumer can still work
                    self.dlq_producer = None

                # Subscribe to the list of topics
                self.logger.info(f"Subscribing to topics: {topics_to_subscribe}")
                self.consumer.subscribe(topics=topics_to_subscribe)

                # Verify subscription by polling (this will trigger partition assignment)
                # This will raise an exception if connection fails
                self.logger.info(
                    "Verifying subscription (polling to trigger partition assignment)..."
                )
                try:
                    # Poll with short timeout to verify connection
                    msg_pack = self.consumer.poll(timeout_ms=2000)
                    partitions = self.consumer.assignment()
                    self.logger.info(
                        f"Consumer assigned to {len(partitions)} partition(s)"
                    )
                    if msg_pack:
                        self.logger.info(
                            f"Received {len(msg_pack)} message batch during verification"
                        )
                except Exception as poll_error:
                    # If polling fails, it might be okay (topics might be empty)
                    self.logger.warning(
                        f"Poll verification warning (may be normal if topics are empty): {poll_error}"
                    )
                    # Continue anyway - subscription was successful

                self.logger.info(
                    f"Enhanced Kafka Consumer connected to {self.bootstrap_servers}"
                )
                self.logger.info(f"Subscribed to topics: {topics_to_subscribe}")
                self.logger.info(
                    f"Consumer connected with max_retries={self.max_retries}"
                )
                return True

            except (KafkaError, KafkaTimeoutError, KafkaConnectionError) as e:
                last_error = e
                self.logger.error(
                    f"Kafka connection error (attempt {attempt + 1}/{retry_count}): {e}",
                    exc_info=True,
                )
                if attempt < retry_count - 1:
                    self.logger.info(f"Will retry in {retry_delay} seconds...")
                else:
                    self.logger.error("All connection attempts failed")

            except (
                ConnectionRefusedError,
                TimeoutError,
                OSError,
                socket.gaierror,
                socket.timeout,
            ) as e:
                last_error = e
                self.logger.error(
                    f"Network error connecting to Kafka (attempt {attempt + 1}/{retry_count}): {e}",
                    exc_info=True,
                )
                if attempt < retry_count - 1:
                    self.logger.info(f"Will retry in {retry_delay} seconds...")
                else:
                    self.logger.error("All connection attempts failed")

            except Exception as e:
                last_error = e
                self.logger.error(
                    f"Unexpected error connecting to Kafka (attempt {attempt + 1}/{retry_count}): {e}",
                    exc_info=True,
                )
                if attempt < retry_count - 1:
                    self.logger.info(f"Will retry in {retry_delay} seconds...")
                else:
                    self.logger.error("All connection attempts failed")

        # All retries failed
        error_msg = f"Failed to connect Kafka consumer after {retry_count} attempts: {last_error}"
        self.logger.error(error_msg, exc_info=True)
        self.alerting_service.alert_kafka_connection_failure(
            str(last_error), "Consumer"
        )
        return False

    def _send_to_dlq(self, original_topic, message, key, error, retry_count):
        """Send failed message to dead letter queue"""
        try:
            dlq_message = {
                "original_topic": original_topic,
                "original_message": message,
                "original_key": key,
                "error": str(error),
                "retry_count": retry_count,
                "timestamp": datetime.now().isoformat(),
                "consumer_group": self.group_id,
            }

            if not self.dlq_producer:
                self.logger.error("DLQ producer not initialized, cannot send to DLQ")
                return False

            dlq_producer = self.dlq_producer  # type: ignore
            dlq_future = dlq_producer.send(
                self.topics["dead_letter_queue"],
                value=dlq_message,
                key=f"dlq_{key}" if key else None,
            )
            dlq_metadata = dlq_future.get(timeout=10)
            self.logger.error(
                f"Message sent to DLQ: {original_topic} -> {self.topics['dead_letter_queue']}[{dlq_metadata.partition}] @ offset {dlq_metadata.offset}"
            )
            return True
        except Exception as dlq_error:
            self.logger.critical(
                f"Failed to send message to DLQ: {dlq_error}", exc_info=True
            )
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

    def _handle_processing_with_retry(
        self,
        processing_func,
        event,
        conversation_id,
        message_key,
        topic_name,
        event_type_name,
    ):
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
            "guardrail event": "guardrail_event",
            "operator action": "operator_action",
        }
        schema_name = schema_name_map.get(event_type_name.lower())

        # Validate message if schema is available, but don't block processing if validation fails
        # Log warning but continue processing (schema validation is informational)
        if schema_name:
            if not self._validate_message(event, schema_name):
                self.logger.warning(
                    f"Schema validation failed for {event_type_name} (conversation: {conversation_id}), but processing anyway"
                )
            else:
                self.logger.debug(f"Schema validation passed for {event_type_name}")

        # Check if Flask app context is available
        if not self.app:
            self.logger.error(
                f"Flask app context not available in consumer for {event_type_name}"
            )
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
                self.logger.error(
                    f"Error processing {event_type_name}: {e}", exc_info=True
                )

                if message_key and topic_name:
                    if self._should_retry_message(message_key, topic_name):
                        retry_count = self._increment_failure_count(
                            message_key, topic_name
                        )
                        self.logger.warning(
                            f"Retrying {event_type_name} processing (attempt {retry_count}/{self.max_retries}): {e}"
                        )
                        return False  # Will be retried
                    else:
                        # Max retries exceeded, send to DLQ
                        self.logger.error(
                            f"Max retries exceeded for {event_type_name}, sending to DLQ"
                        )
                        self.alerting_service.alert_consumer_processing_failure(
                            topic_name, str(e), self.max_retries
                        )
                        self.alerting_service.alert_dlq_message(
                            topic_name, str(e), self.max_retries
                        )
                        self._send_to_dlq(
                            topic_name, event, message_key, e, self.max_retries
                        )
                        return False

                return False

    def _process_guardrail_event_core(self, event, conversation_id):
        """
        Core processing logic for guardrail events (happy path only).
        This method is updated to match guardrail_event_v1.schema.json.
        """

        # Extract detection metadata, providing a default if it's null
        # Handle case where detection_metadata might be a string instead of dict
        detection_meta_raw = event.get("detection_metadata")
        if isinstance(detection_meta_raw, dict):
            detection_meta = detection_meta_raw
        elif isinstance(detection_meta_raw, str):
            # If it's a string, log warning and use empty dict
            self.logger.warning(
                f"detection_metadata is a string instead of dict for conversation {conversation_id}: {detection_meta_raw}"
            )
            detection_meta = {}
        else:
            detection_meta = {}

        # Consolidate all extra details into a single JSONB 'details' column
        # This matches the new schema structure
        event_details = {
            "event_id": event.get("event_id"),
            "context": event.get("context"),
            "action_taken": event.get("action_taken"),
            "confidence_score": event.get("confidence_score"),
            "user_id": event.get("user_id"),
            "guardrail_version": event.get("guardrail_version"),
            "session_metadata": event.get("session_metadata"),
            # Add new fields from detection_metadata
            "detection_time_ms": (
                detection_meta.get("detection_time_ms")
                if isinstance(detection_meta, dict)
                else None
            ),
            "model_version": (
                detection_meta.get("model_version")
                if isinstance(detection_meta, dict)
                else None
            ),
            "triggered_rules": (
                detection_meta.get("triggered_rules")
                if isinstance(detection_meta, dict)
                else None
            ),
        }

        # Create guardrail event in database using enhanced service
        db_event = self.db_service.create_guardrail_event(
            session_id=conversation_id,
            event_type=event.get("event_type"),
            severity=event.get("severity"),
            message=event.get("message"),
            details=event_details,  # Pass the new combined details object
        )

        if db_event:
            self.logger.info(
                f"Guardrail event saved: {event.get('event_type', 'unknown')} "
                f"[{event.get('severity', 'info')}] for conversation {conversation_id}"
            )

            # Handle special events
            if event.get("event_type") == "conversation_started":
                self.logger.info(f"New conversation started: {conversation_id}")
            elif event.get("event_type") == "conversation_ended":
                self.logger.info(f"Conversation ended: {conversation_id}")

            # Call the callback to notify the frontend after successful processing
            if self.on_event_callback:
                try:
                    self.on_event_callback("guardrail_event", conversation_id, event)
                except Exception as e:
                    self.logger.error(
                        f"Failed to call event callback: {e}", exc_info=True
                    )

            return True

        return False

    def process_guardrail_event(
        self, event, conversation_id, message_key=None, topic_name=None
    ):
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
            event_type_name="guardrail event",
        )

    def _process_operator_action_core(self, event, conversation_id):
        """
        Core processing logic for operator actions (happy path only).
        This method contains only the business logic, without retry/DLQ handling.
        """
        action_type = event.get("action_type")
        operator_id = event.get("operator_id")
        message = event.get("message")

        self.logger.info(
            f"Operator action: {action_type} by {operator_id} for conversation {conversation_id}"
        )
        self.logger.debug(f"Operator action message: {message}")

        # Save operator action to database
        self.db_service.create_operator_action(
            conversation_id=conversation_id,
            action_type=action_type,
            operator_id=operator_id,
            message=message,
            details=event,
        )

        # Handle specific actions (logging only, DB update is in db_service)
        if action_type == "stop_conversation":
            self.logger.info(f"Conversation {conversation_id} stopped by operator")
        elif action_type == "false_alarm":
            self.logger.info(f"False alarm reported for conversation {conversation_id}")
        elif action_type == "escalation":
            self.logger.info(f"Conversation {conversation_id} escalated to supervisor")

        # Call the callback to notify the frontend after successful processing
        if self.on_event_callback:
            try:
                self.on_event_callback("operator_action", conversation_id, event)
            except Exception as e:
                self.logger.error(f"Failed to call event callback: {e}", exc_info=True)

        return True

    def process_operator_action(
        self, event, conversation_id, message_key=None, topic_name=None
    ):
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
            event_type_name="operator action",
        )

    def process_guardrail_control(self, event):
        """Process guardrail control events (false alarm feedback, etc.)"""
        # Validate but don't block - schema validation is informational
        if not self._validate_message(event, "control_feedback"):
            self.logger.warning(
                "Schema validation failed for control feedback, but processing anyway"
            )

        try:
            feedback_type = event.get("feedback_type")
            conversation_id = event.get("conversation_id")

            self.logger.info(
                f"Guardrail control event: {feedback_type} for conversation {conversation_id}"
            )

            if feedback_type == "false_alarm":
                original_event_id = event.get("original_event_id")
                feedback = event.get("feedback")
                self.logger.info(f"Original event: {original_event_id}")
                self.logger.info(f"Feedback: {feedback}")

                # Here you would typically update guardrail rules or training data
                self.logger.info("Updating guardrail rules based on feedback")

                # Call the callback to notify the frontend after successful processing
                if self.on_event_callback:
                    try:
                        self.on_event_callback(
                            "false_alarm_feedback", conversation_id, event
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to call event callback: {e}", exc_info=True
                        )

            return True

        except Exception as e:
            self.logger.error(
                f"Error processing guardrail control event: {e}", exc_info=True
            )
            return False

    def consume_events(self):
        """Consume events from Kafka topics"""
        if not self.consumer:
            self.logger.error("❌ Consumer not connected - cannot consume events")
            return

        self.logger.info("=" * 60)
        self.logger.info("✅ Enhanced Kafka Consumer listening for events...")
        self.logger.info(f"📡 Subscribed to topics: {list(self.topics.values())}")
        self.logger.info(f"🔗 Bootstrap servers: {self.bootstrap_servers}")
        self.logger.info(f"👥 Consumer group: {self.group_id}")
        self.logger.info("=" * 60)
        self.running = True
        poll_count = 0

        try:
            while self.running:
                try:
                    # Poll for messages with timeout
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    poll_count += 1

                    # Log every 10 seconds (every 10 polls) to show it's alive
                    if poll_count % 10 == 0:
                        self.logger.info(
                            f"🔄 Kafka consumer polling (poll #{poll_count})..."
                        )

                    if not message_batch:
                        continue

                    self.logger.info(
                        f"📨 Received {len(message_batch)} message batch(es) from Kafka"
                    )

                    for topic_partition, messages in message_batch.items():
                        topic_name = topic_partition.topic

                        for message in messages:
                            if not self.running:
                                break

                            event = message.value
                            message_key = (
                                message.key.decode("utf-8") if message.key else None
                            )

                            # Get conversation_id from the EVENT BODY (or the key as a fallback)
                            conversation_id = (
                                event.get("conversation_id") or message_key
                            )

                            # Generate a valid conversation_id if it's missing or invalid
                            if not conversation_id or conversation_id == "unknown":
                                import uuid

                                conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
                                self.logger.warning(
                                    f"Generated new conversation_id '{conversation_id}' for event without valid conversation_id"
                                )
                                # Update the event with the new conversation_id
                                event["conversation_id"] = conversation_id

                            self.logger.info(
                                f"📥 Processing message from topic '{topic_name}' for conversation '{conversation_id}'"
                            )

                            # CRITICAL: Push Flask application context for background thread
                            # This ensures database operations work in the background thread
                            if not self.app:
                                self.logger.error(
                                    "❌ Flask app not available - cannot process events without application context"
                                )
                                continue

                            with self.app.app_context():
                                # Route based on topic name
                                if topic_name == self.topics["guardrail_events"]:
                                    self.logger.info(
                                        f"🔍 Processing guardrail event for conversation: {conversation_id}"
                                    )
                                    success = self.process_guardrail_event(
                                        event, conversation_id, message_key, topic_name
                                    )
                                    if success:
                                        self.logger.info(
                                            f"✅ Successfully processed guardrail event for {conversation_id}"
                                        )
                                    else:
                                        self.logger.warning(
                                            f"  ️ Failed to process guardrail event for {conversation_id}"
                                        )

                                    if not success and self._should_retry_message(
                                        message_key, topic_name
                                    ):
                                        continue

                                elif topic_name == self.topics["operator_actions"]:
                                    success = self.process_operator_action(
                                        event, conversation_id, message_key, topic_name
                                    )

                                    if not success and self._should_retry_message(
                                        message_key, topic_name
                                    ):
                                        continue

                                elif topic_name == self.topics.get("guardrail_control"):
                                    # Guardrail control is optional - handle gracefully if topic doesn't exist
                                    try:
                                        self.process_guardrail_control(event)
                                    except Exception as e:
                                        self.logger.warning(
                                            f"Error processing guardrail_control event (topic may not exist): {e}"
                                        )

                                else:
                                    self.logger.warning(f"Unknown topic: {topic_name}")

                except Exception as e:
                    if self.running:  # Only log errors if we're supposed to be running
                        self.logger.error(
                            f"Error in message processing: {e}", exc_info=True
                        )
                    continue

        except Exception as e:
            self.logger.error(f"Error consuming events: {e}", exc_info=True)
        finally:
            self.stop()

    def start(self):
        """Start consuming events in a background thread"""
        self.logger.info("🔌 Attempting to connect Kafka consumer...")
        if self.connect():  # Try connecting first
            # Create and start the background thread
            self.logger.info("🧵 Creating background thread for Kafka consumer...")
            self.thread = threading.Thread(
                target=self.consume_events, daemon=True, name="KafkaConsumerThread"
            )
            self.thread.start()

            # Give the thread a moment to start
            import time

            time.sleep(0.5)

            self.logger.info("✅ Enhanced Kafka consumer started in background thread")
            self.logger.info(
                f"🧵 Thread name: {self.thread.name}, daemon: {self.thread.daemon}, alive: {self.thread.is_alive()}"
            )

            if not self.thread.is_alive():
                self.logger.error(
                    "❌ Consumer thread failed to start - thread is not alive"
                )
                return False

            return True  # Indicate success
        # If connect() failed
        self.logger.error("❌ Failed to start consumer due to connection error")
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


if __name__ == "__main__":
    main()

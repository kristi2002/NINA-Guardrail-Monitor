#!/usr/bin/env python3
"""
Kafka Integration Service for NINA Guardrail Monitor
Integrates the enhanced Kafka producer and consumer
"""

import time
import logging
from datetime import datetime
from flask_socketio import emit  # type: ignore
from .kafka_producer import NINAKafkaProducerV2
from .kafka_consumer import NINAKafkaConsumerV2
from services.database_service import EnhancedDatabaseService
from config import get_kafka_bootstrap_servers


class KafkaIntegrationService:
    def __init__(self, bootstrap_servers=None, socketio=None, app=None, db=None):
        """Initialize the complete Kafka integration service"""
        self.bootstrap_servers = bootstrap_servers or get_kafka_bootstrap_servers()
        self.socketio = socketio
        self.app = app
        self.db = db  # Store the db instance

        # --- MODIFICATION: Pass 'db' to the service ---
        if not db:
            logging.critical(
                "KafkaIntegrationService initialized without 'db' instance!"
            )
        self.db_service = EnhancedDatabaseService(db=self.db, app=self.app)

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize components
        # self.topic_manager = KafkaTopicManager(self.bootstrap_servers) # <-- RIMOSSO
        self.producer = NINAKafkaProducerV2(self.bootstrap_servers)

        # --- MODIFICATION: Pass 'db' to the consumer ---
        self.consumer = NINAKafkaConsumerV2(
            self.bootstrap_servers,
            app=self.app,
            db=self.db,  # Pass the db instance
            on_event_callback=self.handle_consumed_event,
        )

        # Track active conversations (in-memory cache)
        self.active_conversations = {}
        self.conversation_events = {}
        # self._initialize_control_topics() # <-- RIMOSSO (I topic sono statici e si presume esistano)

    def start_consumer(self):
        """Start the Kafka consumer"""
        try:
            self.logger.info("🚀 Starting Kafka consumer...")
            success = self.consumer.start_consumer()
            if success:
                self.logger.info("✅ Kafka consumer started successfully")
            else:
                self.logger.error("❌ Failed to start Kafka consumer")
            return success
        except Exception as e:
            self.logger.error(f"❌ Error starting Kafka consumer: {e}", exc_info=True)
            return False

    def handle_consumed_event(self, event_type, conversation_id, event):
        """
        Callback function that the consumer calls after processing an event.
        This is now SYNCED with notificationService.js
        """
        if not self.socketio:
            return  # No frontend to update

        try:
            # Check if this is a guardrail event
            if event_type == "guardrail_event":

                # Get severity to decide which event to send
                # Convert to string first to handle int/float types safely
                severity = str(event.get("severity", "info")).lower()

                # --- THE FIX ---
                # If severity is high or critical, emit 'alert_escalation'
                if severity in ["high", "critical"]:
                    self.socketio.emit(
                        "alert_escalation",
                        {"conversation_id": conversation_id, "event": event},
                    )
                    self.logger.info(
                        f"Socket.IO 'alert_escalation' emitted for {conversation_id}"
                    )

                # For all other severities, emit a generic 'notification'
                else:
                    self.socketio.emit(
                        "notification",
                        {"conversation_id": conversation_id, "event": event},
                    )
                    self.logger.info(
                        f"Socket.IO 'notification' emitted for {conversation_id}"
                    )

            # Check if this is an operator action
            elif event_type == "operator_action":
                # Send all operator actions as a generic 'notification'
                self.socketio.emit(
                    "notification",
                    {
                        "conversation_id": conversation_id,
                        "event": event,  # Send the full operator action event
                    },
                )
                self.logger.info(
                    f"Socket.IO 'notification' (for operator_action) emitted for {conversation_id}"
                )

            elif event_type == "false_alarm_feedback":
                # Send this as a generic 'notification' as well
                self.socketio.emit(
                    "notification", {"conversation_id": conversation_id, "event": event}
                )
                self.logger.info(
                    f"Socket.IO 'notification' (for false_alarm) emitted for {conversation_id}"
                )

        except Exception as e:
            self.logger.error(
                f"Failed to emit Socket.IO event for {event_type}: {e}", exc_info=True
            )

    def stop_consumer(self):
        """Stop the Kafka consumer"""
        self.consumer.stop()
        self.logger.info("Kafka integration service consumer stopped")

    def start_conversation_monitoring(self, conversation_id):
        """Start monitoring a new conversation (in-memory tracking)"""
        try:
            # --- RIMOSSA LA LOGICA DI CREAZIONE TOPIC ---

            # Initialize conversation tracking
            self.active_conversations[conversation_id] = {
                "start_time": datetime.now(),
                "status": "active",
                "event_count": 0,
                "last_event": None,
            }

            self.conversation_events[conversation_id] = []

            self.logger.info(f"Started monitoring conversation: {conversation_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Error starting conversation monitoring: {e}", exc_info=True
            )
            return False

    def stop_conversation_monitoring(self, conversation_id):
        """Stop monitoring a conversation"""
        try:
            # Consumer will continue to receive messages but we can filter them out
            # No need to manually remove topics from consumer subscription

            # Update conversation status
            if conversation_id in self.active_conversations:
                self.active_conversations[conversation_id]["status"] = "stopped"
                self.active_conversations[conversation_id]["end_time"] = datetime.now()

            self.logger.info(f"Stopped monitoring conversation: {conversation_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Error stopping conversation monitoring: {e}", exc_info=True
            )
            return False

    def send_guardrail_event(
        self, conversation_id, event_type, severity, message, context=None
    ):
        """Send a guardrail event for a specific conversation"""
        try:
            # Ensure conversation is being monitored
            if conversation_id not in self.active_conversations:
                self.start_conversation_monitoring(conversation_id)

            # Create event
            event = {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "severity": severity,
                "message": message,
                "context": context or "",
                "user_id": f"user_{conversation_id.split('_')[-1] if '_' in conversation_id else 'unknown'}",
                "response_time_ms": 100,  # Default
                "action_taken": "logged",
                "confidence_score": 0.95,
                "guardrail_version": "2.0",
            }

            # Send via producer
            success = self.producer.send_guardrail_event(conversation_id, event)

            if success:
                # Update tracking
                self.active_conversations[conversation_id]["event_count"] += 1
                self.active_conversations[conversation_id]["last_event"] = event
                self.conversation_events[conversation_id].append(event)

                # Note: Socket.IO emission will be handled by the consumer callback
                # after the event is successfully processed and saved to database
                self.logger.info(
                    f"Guardrail event sent: {event_type} for conversation {conversation_id}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Error sending guardrail event: {e}", exc_info=True)
            return False

    def send_operator_action(
        self, conversation_id, action_type, message, reason=None, operator_id=None
    ):
        """Send an operator action for a specific conversation"""
        try:
            # Create enhanced operator action message
            operator_action = {
                "action_type": action_type,
                "conversation_id": conversation_id,
                "operator_id": operator_id or "dashboard_operator",
                "message": message,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "command": {
                    "type": (
                        "STOP"
                        if action_type == "stop_conversation"
                        else action_type.upper()
                    ),
                    "reason": reason or "operator_intervention",
                    "final_message": message,
                },
            }

            # Send via producer with custom message
            success = self.producer.send_operator_action(
                conversation_id, action_type, custom_message=operator_action
            )

            if success:
                # Note: Socket.IO emission will be handled by the consumer callback
                # after the event is successfully processed and saved to database
                self.logger.info(
                    f"Operator action sent: {action_type} for conversation {conversation_id}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Error sending operator action: {e}", exc_info=True)
            return False

    def send_false_alarm_feedback(self, conversation_id, original_event_id, feedback):
        """Send false alarm feedback to guardrails"""
        try:
            success = self.producer.send_false_alarm_feedback(
                conversation_id, original_event_id, feedback
            )

            if success:
                self.logger.info(
                    f"False alarm feedback sent for conversation {conversation_id}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Error sending false alarm feedback: {e}", exc_info=True)
            return False

    def get_conversation_status(self, conversation_id):
        """Get status of a specific conversation"""
        return self.active_conversations.get(conversation_id, None)

    def get_all_conversations(self):
        """Get all active conversations"""
        return self.active_conversations

    def get_conversation_events(self, conversation_id):
        """Get events for a specific conversation"""
        return self.conversation_events.get(conversation_id, [])

    def simulate_conversation_flow(self, conversation_id=None, duration=60):
        """Simulate a complete conversation flow"""
        if not conversation_id:
            conversation_id = f"sim_conv_{int(time.time())}"

        self.logger.info(f"Simulating conversation flow: {conversation_id}")

        # Start conversation
        self.send_guardrail_event(
            conversation_id,
            "conversation_started",
            "info",
            "Conversation session initiated",
        )

        # Simulate events during conversation
        start_time = time.time()
        event_count = 1

        try:
            while (time.time() - start_time) < duration:
                # Random guardrail events
                if time.time() - start_time > 10:  # After 10 seconds
                    event_types = [
                        ("warning_triggered", "medium", "Potential issue detected"),
                        ("alarm_triggered", "high", "Critical issue detected"),
                        (
                            "privacy_violation_prevented",
                            "critical",
                            "Privacy violation blocked",
                        ),
                        ("medication_warning", "high", "Drug interaction warning"),
                    ]

                    if time.time() - start_time > 30:  # After 30 seconds
                        event_type, severity, message = event_types[
                            event_count % len(event_types)
                        ]
                        self.send_guardrail_event(
                            conversation_id, event_type, severity, message
                        )
                        event_count += 1

                time.sleep(5)  # Check every 5 seconds

            # End conversation
            self.send_guardrail_event(
                conversation_id,
                "conversation_ended",
                "info",
                "Conversation session completed",
            )

            self.logger.info(f"Conversation simulation completed: {conversation_id}")
            return conversation_id

        except KeyboardInterrupt:
            self.logger.info(f"Conversation simulation stopped: {conversation_id}")
            return conversation_id

    def get_system_stats(self):
        """Get system statistics"""
        try:
            # --- MODIFICATO ---
            # topic_stats = self.topic_manager.get_topic_stats() # <-- RIMOSSO

            stats = {
                "active_conversations": len(self.active_conversations),
                "total_events": sum(
                    len(events) for events in self.conversation_events.values()
                ),
                # 'kafka_topics': topic_stats, # <-- RIMOSSO
                "consumer_running": self.consumer.is_running(),
                "uptime": datetime.now().isoformat(),
            }
            # --- FINE MODIFICA ---

            return stats

        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}", exc_info=True)
            return {}

    def cleanup_old_conversations(self, max_age_hours=24):
        """Clean up old conversation data (in-memory cache only)"""
        try:
            self.logger.info("Starting in-memory conversation cleanup...")
            # --- MODIFICATO ---
            # (Rimosse tutte le logiche di DB e topic_manager. Pulisce solo la cache in memoria)
            # --- FINE MODIFICA ---

            current_time = datetime.now()
            conversations_to_cleanup = []

            for conv_id, conv_data in self.active_conversations.items():
                if conv_data["status"] == "stopped":
                    if "end_time" in conv_data:
                        age_hours = (
                            current_time - conv_data["end_time"]
                        ).total_seconds() / 3600
                        if age_hours > max_age_hours:
                            conversations_to_cleanup.append(conv_id)

            for conv_id in conversations_to_cleanup:
                self.stop_conversation_monitoring(conv_id)
                if conv_id in self.conversation_events:
                    del self.conversation_events[conv_id]
                if conv_id in self.active_conversations:
                    del self.active_conversations[conv_id]

            total_cleaned = len(conversations_to_cleanup)
            if total_cleaned > 0:
                self.logger.info(
                    f"Cleaned up {total_cleaned} old conversations from memory"
                )

            return total_cleaned

        except Exception as e:
            self.logger.error(
                f"Error cleaning up old conversations: {e}", exc_info=True
            )
            return 0

    def close(self):
        """Close all connections"""
        try:
            self.stop_consumer()
            self.producer.close()
            # self.topic_manager.close() # <-- RIMOSSO
            self.logger.info("Kafka integration service closed")
        except Exception as e:
            self.logger.error(
                f"Error closing Kafka integration service: {e}", exc_info=True
            )


def main():
    """Main function to test the integration service"""
    print("=" * 60)
    print("🔗 NINA Guardrail Monitor - Kafka Integration Service")
    print("=" * 60)

    # Initialize integration service
    integration_service = KafkaIntegrationService()

    try:
        # Start consumer
        if not integration_service.start_consumer():
            print("❌ Failed to start consumer")
            return

        # Test conversation simulation
        print("\n🎭 Testing conversation simulation...")
        conv_id = integration_service.simulate_conversation_flow(duration=30)

        # Test operator actions
        print(f"\n👮 Testing operator actions for {conv_id}...")
        integration_service.send_operator_action(
            conv_id, "stop_conversation", "Conversation stopped by operator"
        )

        # Get stats
        print("\n📊 System statistics:")
        stats = integration_service.get_system_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Keep running for a bit
        print("\n⏳ Running for 10 seconds to process events...")
        time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n⏸️ Integration service stopped by user")
    finally:
        integration_service.close()


if __name__ == "__main__":
    main()

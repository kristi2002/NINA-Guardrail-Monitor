#!/usr/bin/env python3
"""
Kafka Integration Service for NINA Guardrail Monitor
Integrates the enhanced Kafka producer and consumer
"""

import time
import logging
from datetime import datetime, timezone
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
        """Start the Kafka consumer with graceful degradation"""
        try:
            self.logger.info("🚀 Starting Kafka consumer...")
            success = self.consumer.start_consumer()
            if success:
                self.logger.info("✅ Kafka consumer started successfully")
            else:
                self.logger.warning(
                    "⚠️ Kafka consumer not started (Kafka may be unavailable). "
                    "Service will continue without real-time Kafka consumption."
                )
            return success
        except Exception as e:
            self.logger.warning(
                f"⚠️ Error starting Kafka consumer: {e}. "
                "Service will continue without Kafka consumer.",
                exc_info=True
            )
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
                    # Format as alert escalation
                    escalation_data = {
                        "id": f"escalation_{event.get('event_id', 'unknown')}",
                        "title": self._get_notification_title(event),
                        "message": event.get("message", "A critical guardrail event occurred"),
                        "type": "critical",
                        "priority": "critical",
                        "severity": severity,
                        "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "read": False,
                        "conversation_id": conversation_id,
                        "event_id": event.get("event_id"),
                        "metadata": {
                            "event_type": event.get("event_type"),
                            "violations": event.get("violations", []),
                            "guardrail_rules": event.get("guardrail_rules", [])
                        }
                    }
                    self.socketio.emit(
                        "alert_escalation",
                        escalation_data,
                    )
                    self.logger.info(
                        f"Socket.IO 'alert_escalation' emitted for {conversation_id}"
                    )

                # For all other severities, emit a generic 'notification'
                else:
                    # Format notification for frontend
                    notification_data = {
                        "id": f"notif_{event.get('event_id', 'unknown')}",
                        "title": self._get_notification_title(event),
                        "message": event.get("message", "A guardrail event occurred"),
                        "type": self._get_notification_type(event.get("event_type", "system_alert")),
                        "priority": self._map_severity_to_priority(severity),
                        "severity": severity,
                        "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "read": False,
                        "conversation_id": conversation_id,
                        "event_id": event.get("event_id"),
                        "metadata": {
                            "event_type": event.get("event_type"),
                            "violations": event.get("violations", []),
                            "guardrail_rules": event.get("guardrail_rules", [])
                        }
                    }
                    self.socketio.emit(
                        "notification",
                        notification_data,
                    )
                    self.logger.info(
                        f"Socket.IO 'notification' emitted for {conversation_id}"
                    )

            # Check if this is an operator action
            elif event_type == "operator_action":
                # Format operator action as notification
                notification_data = {
                    "id": f"notif_op_{event.get('action_id', 'unknown')}",
                    "title": f"👤 {event.get('title', 'Operator Action')}",
                    "message": event.get("description", event.get("message", "An operator action was taken")),
                    "type": "info",
                    "priority": "info",
                    "severity": "info",
                    "timestamp": event.get("action_timestamp", datetime.now(timezone.utc).isoformat()),
                    "read": False,
                    "conversation_id": conversation_id,
                    "event_id": event.get("action_id"),
                    "metadata": {
                        "action_type": event.get("action_type"),
                        "operator_id": event.get("operator_id")
                    }
                }
                self.socketio.emit(
                    "notification",
                    notification_data,
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
        self, 
        conversation_id, 
        action_type, 
        message, 
        reason=None, 
        operator_id=None,
        target_event_id=None,
        priority=None,
        conversation_state=None,
        risk_level=None,
        active_guardrails=None
    ):
        """
        Send an operator action for a specific conversation with full metadata
        
        Args:
            conversation_id: The conversation ID
            action_type: Type of action (stop_conversation, escalate, acknowledge, etc.)
            message: Human-readable message
            reason: Reason for the action
            operator_id: ID of the operator
            target_event_id: ID of the specific event this action relates to
            priority: Priority level (low, normal, high, urgent)
            conversation_state: Current state of conversation (active, paused, etc.)
            risk_level: Risk level (low, medium, high, critical)
            active_guardrails: List of active guardrail validators
        """
        try:
            import time
            action_start_time = time.time()
            
            # Determine priority if not provided
            if not priority:
                if action_type in ["stop_conversation", "emergency_stop"]:
                    priority = "urgent"
                elif action_type in ["escalate", "manual_intervention"]:
                    priority = "high"
                elif action_type in ["acknowledge", "resolve"]:
                    priority = "normal"
                else:
                    priority = "normal"
            
            # Get conversation state and risk level from database if not provided
            if not conversation_state or not risk_level:
                try:
                    from models.conversation_session import ConversationSession
                    session = self.db.session.query(ConversationSession).filter_by(
                        id=conversation_id
                    ).first()
                    if session:
                        if not conversation_state:
                            # Map status to conversation_state
                            status_mapping = {
                                'ACTIVE': 'active',
                                'PAUSED': 'paused',
                                'ESCALATED': 'escalated',
                                'COMPLETED': 'resolved',
                                'TERMINATED': 'stopped',
                                'STOPPED': 'stopped'
                            }
                            conversation_state = status_mapping.get(session.status, 'active')
                        if not risk_level:
                            risk_level = (session.risk_level or 'low').lower()
                except Exception as e:
                    self.logger.debug(f"Could not fetch conversation state: {e}")
            
            # Get active guardrails if not provided
            if not active_guardrails:
                active_guardrails = ["ToxicLanguage", "DetectPII", "Compliance", "LLMContextAwareCheck"]
            
            # Calculate response time
            response_time_seconds = time.time() - action_start_time
            
            # Create enhanced operator action message with full metadata
            operator_action = {
                "schema_version": "1.0",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "action_type": action_type,
                "operator_id": operator_id or "dashboard_operator",
                "message": message,
                "reason": reason,
                "priority": priority,
                "target_event_id": target_event_id,
                "command": {
                    "type": action_type,
                    "reason": reason or "operator_intervention",
                    "final_message": message if action_type == "stop_conversation" else None
                },
                "action_metadata": {
                    "response_time_seconds": round(response_time_seconds, 2),
                    "escalation_level": "supervisor" if action_type == "escalate" else None,
                    "notification_sent": True,
                    "follow_up_required": action_type in ["escalate", "manual_intervention"],
                    "resolution_notes": reason if action_type == "resolve" else None
                },
                "system_context": {
                    "active_guardrails": active_guardrails,
                    "conversation_state": conversation_state or "active",
                    "risk_level": risk_level or "low"
                }
            }

            # Send via producer with custom message
            success = self.producer.send_operator_action(
                conversation_id, action_type, custom_message=operator_action
            )

            if success:
                # Note: Socket.IO emission will be handled by the consumer callback
                # after the event is successfully processed and saved to database
                self.logger.info(
                    f"Operator action sent: {action_type} for conversation {conversation_id} "
                    f"with full metadata"
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
    
    def _get_notification_title(self, event):
        """Get notification title based on event type"""
        event_type = event.get("event_type", "system_alert")
        title_map = {
            'alarm_triggered': '🚨 Alarm Triggered',
            'warning_triggered': '⚠️ Warning',
            'privacy_violation_prevented': '🔒 Privacy Violation Prevented',
            'medication_warning': '💊 Medication Warning',
            'inappropriate_content': '🚫 Inappropriate Content',
            'emergency_protocol': '🚨 Emergency Protocol',
            'false_alarm_reported': 'ℹ️ False Alarm Reported',
            'operator_intervention': '👤 Operator Intervention',
            'system_alert': '📢 System Alert',
            'compliance_check': '✅ Compliance Check',
            'context_violation': '⚠️ Context Violation',
            'conversation_started': '💬 Conversation Started',
            'conversation_ended': '✅ Conversation Ended'
        }
        return title_map.get(event_type, '📢 Guardrail Event')
    
    def _get_notification_type(self, event_type):
        """Get notification type based on event type"""
        notification_type_map = {
            'alarm_triggered': 'alert',
            'warning_triggered': 'warning',
            'privacy_violation_prevented': 'security',
            'medication_warning': 'warning',
            'inappropriate_content': 'alert',
            'emergency_protocol': 'critical',
            'false_alarm_reported': 'info',
            'operator_intervention': 'info',
            'system_alert': 'system',
            'compliance_check': 'compliance',
            'context_violation': 'alert',
            'conversation_started': 'info',
            'conversation_ended': 'info'
        }
        return notification_type_map.get(event_type, 'system')
    
    def _map_severity_to_priority(self, severity):
        """Map severity to priority for frontend"""
        severity_lower = str(severity).lower()
        severity_to_priority = {
            'critical': 'critical',
            'high': 'warning',
            'medium': 'info',
            'low': 'info',
            'info': 'info'
        }
        return severity_to_priority.get(severity_lower, 'info')

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

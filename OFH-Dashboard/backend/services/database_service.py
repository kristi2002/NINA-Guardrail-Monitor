#!/usr/bin/env python3
"""
Enhanced Database Service for Kafka Integration
Handles conversation-specific events and real-time data persistence
"""

from models import ConversationSession, GuardrailEvent, ChatMessage, OperatorAction  # type: ignore
from datetime import datetime, timedelta
import json
import uuid
import logging  # Import logging

logger = logging.getLogger(__name__)  # Add logger


class EnhancedDatabaseService:
    """Enhanced database service for Kafka integration"""

    # --- MODIFICATION 1: Update __init__ ---
    def __init__(self, db, app=None):
        """
        Initialize the service with the SQLAlchemy db instance.

        Args:
        db: The Flask-SQLAlchemy (db = SQLAlchemy()) instance
        app: The Flask app instance (optional, used for context)
        """
        self.app = app
        self.db = db  # Store the db instance directly

        if not db:
            logger.error("EnhancedDatabaseService initialized without a 'db' instance!")

        # Import models directly (they're already imported at top of file)
        self.models = {
            "ConversationSession": ConversationSession,
            "GuardrailEvent": GuardrailEvent,
            "ChatMessage": ChatMessage,
            "OperatorAction": OperatorAction,
        }

    # --- MODIFICATION 2: Remove _get_db() method ---
    # The entire _get_db(self) method is removed.

    # --- MODIFICATION 3: Update all methods to use self.db ---

    def test_connection(self):
        """Test database connection"""
        try:
            self.db.session.execute("SELECT 1")  # USE self.db
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            return False

    def create_tables(self):
        """Create all database tables"""
        try:
            self.db.create_all()  # USE self.db
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}", exc_info=True)
            return False

    # =======================
    # Conversation Management
    # =======================

    def create_conversation_session(
        self, conversation_id, patient_id=None, metadata=None
    ):
        """Create a new conversation session from Kafka event"""
        ConversationSession = self.models["ConversationSession"]
        try:
            # Check if session already exists
            existing_session = self.db.session.query(ConversationSession).get(
                conversation_id
            )
            if existing_session:
                return existing_session

            session = ConversationSession(
                id=conversation_id,
                patient_id=patient_id or f"patient_{conversation_id}",
                session_start=datetime.utcnow(),
                status="ACTIVE",
                total_messages=0,
                guardrail_violations=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.session.add(session)
            self.db.session.commit()

            print(f"✅ Created conversation session: {conversation_id}")
            return session

        except Exception as e:
            print(f"❌ Error creating conversation session: {e}")
            self.db.session.rollback()
            return None

    def update_conversation_session(self, conversation_id, **kwargs):
        """Update conversation session with new data"""
        ConversationSession = self.models["ConversationSession"]
        try:
            session = self.db.session.query(ConversationSession).get(conversation_id)
            if not session:
                # Create session if it doesn't exist
                session = self.create_conversation_session(conversation_id)

            if session:
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)

                session.updated_at = datetime.utcnow()
                self.db.session.commit()

                return session

        except Exception as e:
            print(f"❌ Error updating conversation session: {e}")
            self.db.session.rollback()
            return None

    def end_conversation_session(self, conversation_id, reason="completed"):
        """End a conversation session"""
        ConversationSession = self.models["ConversationSession"]
        try:
            session = self.db.session.query(ConversationSession).get(conversation_id)
            if session:
                session.session_end = datetime.utcnow()
                session.status = "COMPLETED" if reason == "completed" else "TERMINATED"

                # Calculate duration
                duration = session.session_end - session.session_start
                session.session_duration_minutes = int(duration.total_seconds() / 60)
                session.updated_at = datetime.utcnow()

                self.db.session.commit()
                print(f"✅ Ended conversation session: {conversation_id}")
                return session

        except Exception as e:
            print(f"❌ Error ending conversation session: {e}")
            self.db.session.rollback()
            return None

    def get_conversation_session(self, conversation_id):
        """Get conversation session by ID"""
        ConversationSession = self.models["ConversationSession"]
        # db = self._get_db() # REMOVED
        return self.db.session.query(ConversationSession).get(
            conversation_id
        )  # USE self.db

    def get_active_conversations(self):
        """Get all active conversations"""
        ConversationSession = self.models["ConversationSession"]
        cutoff_time = datetime.utcnow() - timedelta(
            hours=24
        )  # Extended for Kafka events
        # db = self._get_db() # REMOVED
        return (
            self.db.session.query(ConversationSession)
            .filter(  # USE self.db
                ConversationSession.session_start > cutoff_time,
                ConversationSession.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .order_by(ConversationSession.session_start.desc())
            .all()
        )

    # =======================
    # Guardrail Events
    # =======================

    def create_guardrail_event(
        self, session_id, event_type, severity, message, details=None
    ):
        """Create a guardrail event from Kafka message (V2 Schema Compliant)"""
        # ... (Your existing logic for this method is fine, just update db calls) ...

        if "GuardrailEvent" in self.models:
            GuardrailEventModel = self.models["GuardrailEvent"]
        else:
            GuardrailEventModel = GuardrailEvent

        if not session_id or session_id == "unknown" or not isinstance(session_id, str):
            session_id = f"conv_{uuid.uuid4().hex[:12]}"
            print(f"⚠️ Invalid session_id, generated new one: {session_id}")

        try:
            # Ensure conversation session exists
            session = self.get_conversation_session(session_id)
            if not session:
                session = self.create_conversation_session(session_id)

            if details is None:
                details = {}

            # ... (Your existing schema mapping logic is here and looks correct) ...
            detection_meta = details.get("detection_metadata") or {}
            user_message_content = details.get("context")
            response_time_ms = details.get("detection_time_ms") or detection_meta.get(
                "detection_time_ms"
            )
            response_time_minutes = None
            if response_time_ms is not None:
                try:
                    response_time_sec = float(response_time_ms) / 1000
                    response_time_minutes = int(response_time_sec / 60)
                except (ValueError, TypeError):
                    response_time_minutes = None
            bot_response_content = None
            event_id = details.get("event_id") or str(uuid.uuid4())

            # Normalize severity to string and uppercase
            # Handle None, int, or other types gracefully
            if severity is None:
                severity_str = "INFO"
            elif isinstance(severity, str):
                severity_str = severity.upper()
            elif isinstance(severity, (int, float)):
                # Convert numeric severity to string
                severity_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
                severity_str = severity_map.get(int(severity), "INFO")
            else:
                severity_str = str(severity).upper() if severity else "INFO"

            # Ensure event_type is never None (database requires NOT NULL)
            if not event_type or not isinstance(event_type, str):
                event_type = "unknown_event"

            # Determine category from event_type
            category = self._determine_category(event_type)

            # Generate title from event_type and message
            title = self._generate_event_title(event_type, message, severity_str)

            # Generate description (use message_content if available, otherwise use title)
            description = message if message else title

            # Normalize confidence_score - ensure it's never None (database requires NOT NULL)
            confidence_score_from_payload = details.get("confidence_score")
            final_confidence_score = 0.0  # Default value
            if confidence_score_from_payload is not None:
                try:
                    # Try to cast to float, default to 0.0 if it's invalid
                    final_confidence_score = float(confidence_score_from_payload)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid confidence_score '{confidence_score_from_payload}', defaulting to 0.0"
                    )
                    final_confidence_score = 0.0  # Default if it's bad data

            event = GuardrailEventModel(
                conversation_id=session_id,
                event_id=event_id,
                event_type=event_type,
                severity=severity_str,
                category=category,
                title=title,
                description=description,
                message_content=message,
                confidence_score=final_confidence_score,
                user_message=user_message_content,
                bot_response=bot_response_content,
                status="PENDING",
                response_time_minutes=response_time_minutes,
                priority=self._determine_priority(severity_str, event_type),
                tags=self._generate_tags(event_type, severity_str),
                details=details,
            )
            # ... (End of schema mapping logic) ...

            # db = self._get_db() # REMOVED
            self.db.session.add(event)

            # ... (Your existing session update logic is fine) ...
            if session:
                session.guardrail_violations += 1
                session.updated_at = datetime.utcnow()
                # Use the normalized severity_str
                risk_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "INFO": 1}
                current_risk_score = risk_map.get(session.risk_level, 1)
                new_risk_score = risk_map.get(severity_str, 1)
                if new_risk_score > current_risk_score:
                    session.risk_level = severity_str
                    session.situation = message
                if severity_str in ["HIGH", "CRITICAL"]:
                    session.requires_attention = True
                if event_type == "conversation_started":
                    session.status = "ACTIVE"
                elif event_type == "conversation_ended":
                    session.status = "COMPLETED"
                    session.session_end = datetime.utcnow()

            self.db.session.commit()

            print(
                f"✅ Created guardrail event: {event_type} [{severity_str}] for {session_id}"
            )
            return event

        except Exception as e:
            print(f"❌ Error creating guardrail event: {e}")
            self.db.session.rollback()
            return None

    # ... (Your _determine_priority and _generate_tags methods are fine) ...
    def _determine_priority(self, severity, event_type):
        # Severity is already normalized to uppercase string
        if severity == "CRITICAL":
            return "URGENT"
        elif severity == "HIGH":
            return "HIGH"
        elif severity == "MEDIUM":
            return "NORMAL"
        else:
            return "LOW"

    def _determine_category(self, event_type):
        """Determine event category from event_type"""
        if not event_type or not isinstance(event_type, str):
            return "system"

        event_type_lower = event_type.lower()

        # Conversation lifecycle events
        if "conversation" in event_type_lower:
            return "conversation"
        # Alert/security events
        elif any(
            term in event_type_lower
            for term in ["alarm", "warning", "violation", "inappropriate", "emergency"]
        ):
            return "alert"
        # System events
        elif any(
            term in event_type_lower for term in ["system", "protocol", "compliance"]
        ):
            return "system"
        # Default to alert for safety
        else:
            return "alert"

    def _generate_event_title(self, event_type, message, severity):
        """Generate a human-readable title for the event"""
        if not event_type:
            event_type = "unknown_event"

        # Convert event_type to readable format
        event_title = event_type.replace("_", " ").title()

        # Use message if available, otherwise use event_type
        if message and len(message) > 0:
            # Truncate message if too long
            msg_preview = message[:100] + "..." if len(message) > 100 else message
            return f"{event_title} - {msg_preview}"
        else:
            return f"{event_title} [{severity}]"

    def _generate_tags(self, event_type, severity):
        if not event_type:
            event_type = "unknown"
        if not severity:
            severity = "info"

        tags = [event_type.lower(), severity.lower()]
        event_type_lower = event_type.lower()

        if "privacy" in event_type_lower:
            tags.append("privacy")
        if "medical" in event_type_lower:
            tags.append("medical")
        if "medication" in event_type_lower:
            tags.append("medication")
        if "emergency" in event_type_lower:
            tags.append("emergency")
        return ",".join(tags)

    def get_guardrail_events_by_conversation(self, conversation_id, limit=100):
        """Get all guardrail events for a specific conversation"""
        GuardrailEvent = self.models["GuardrailEvent"]
        return (
            self.db.session.query(GuardrailEvent)
            .filter(GuardrailEvent.conversation_id == conversation_id)
            .order_by(GuardrailEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_guardrail_events(self, hours=24, limit=100):
        """Get recent guardrail events across all conversations"""
        GuardrailEvent = self.models["GuardrailEvent"]
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.session.query(GuardrailEvent)
            .filter(GuardrailEvent.created_at > cutoff_time)
            .order_by(GuardrailEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent_alerts(self, hours=24, limit=100):
        """Get recent alerts (guardrail events) for metrics"""
        GuardrailEvent = self.models["GuardrailEvent"]
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            events = (
                self.db.session.query(GuardrailEvent)
                .filter(GuardrailEvent.created_at > cutoff_time)
                .order_by(GuardrailEvent.created_at.desc())
                .limit(limit)
                .all()
            )

            # ... (Your to_dict logic is fine) ...
            alerts = []
            for event in events:
                alerts.append(
                    {
                        "id": event.id,
                        "conversation_id": event.conversation_id,
                        "severity": event.severity,
                        "event_type": event.event_type,
                        "message": event.message_content,
                        "status": event.status,
                        "created_at": (
                            event.created_at.isoformat() if event.created_at else None
                        ),
                    }
                )
            return alerts
        except Exception as e:
            print(f"Error getting recent alerts: {e}")
            return []

    def update_guardrail_event_status(
        self, event_id, status, operator_id=None, notes=None
    ):
        """Update guardrail event status"""
        GuardrailEvent = self.models["GuardrailEvent"]
        try:
            event = self.db.session.query(GuardrailEvent).get(event_id)  # type: ignore
            if event:
                # ... (Your status update logic is fine) ...
                event.status = status
                event.last_updated_at = datetime.utcnow()
                event.last_updated_by = operator_id
                if status == "ACKNOWLEDGED":
                    event.acknowledged_by = operator_id
                    event.acknowledged_at = datetime.utcnow()
                elif status == "RESOLVED":
                    event.resolved_by = operator_id
                    event.resolved_at = datetime.utcnow()
                    event.resolution_notes = notes

                self.db.session.commit()
                return event

        except Exception as e:
            print(f"❌ Error updating guardrail event: {e}")
            self.db.session.rollback()
            return None

    # =======================
    # Operator Actions
    # =======================

    def create_operator_action(
        self, conversation_id, action_type, operator_id, message, details=None
    ):
        """Create an operator action record"""
        OperatorActionModel = self.models.get("OperatorAction", OperatorAction)
        try:
            # ... (Your session check and details logic is fine) ...
            session = self.get_conversation_session(conversation_id)
            if not session:
                print(
                    f"⚠️ Conversation session {conversation_id} not found... Creating it now."
                )
                session = self.create_conversation_session(conversation_id)
                if not session:
                    print(
                        f"❌ Failed to create session {conversation_id}. Aborting action."
                    )
                    return None
            if isinstance(details, str):
                try:
                    details_dict = json.loads(details)
                except:
                    details_dict = {"raw_details": details}
            elif details is None:
                details_dict = {}
            else:
                details_dict = details

            # ... (Your schema mapping logic for OperatorAction is fine) ...
            related_event_id = details_dict.get("original_event_id", None)
            action_id = details_dict.get("action_id") or str(uuid.uuid4())
            title = (
                details_dict.get("title")
                or f"{action_type.replace('_', ' ').title()} Action"
            )
            action_category = details_dict.get("action_category")
            if not action_category:
                if action_type in ["stop_conversation", "pause_conversation"]:
                    action_category = "conversation"
                elif action_type in [
                    "escalate",
                    "acknowledge",
                    "resolve",
                    "false_alarm",
                ]:
                    action_category = "alert"
                else:
                    action_category = "system"

            # Ensure description is never None (database requires NOT NULL)
            description = (
                message
                if message
                else f"{action_type.replace('_', ' ').title()} action performed"
            )

            action = OperatorActionModel(
                action_id=action_id,
                conversation_id=conversation_id,
                alert_id=related_event_id,
                action_type=action_type,
                action_category=action_category,
                title=title,
                description=description,
                action_data=details_dict,
                operator_id=operator_id or "system",  # Ensure operator_id is never None
                action_timestamp=datetime.utcnow(),
            )

            self.db.session.add(action)

            # ... (Your session update logic is fine) ...
            if session:
                if action_type == "stop_conversation":
                    session.status = "TERMINATED"
                    session.session_end = datetime.utcnow()
                elif action_type == "escalation":
                    session.status = "ESCALATED"
                elif action_type == "false_alarm":
                    if session.guardrail_violations > 0:
                        session.guardrail_violations -= 1
                session.updated_at = datetime.utcnow()

            self.db.session.commit()

            print(f"✅ Created operator action: {action_type} for {conversation_id}")
            return action

        except Exception as e:
            print(f"❌ Error creating operator action: {e}")
            self.db.session.rollback()
            return None

    def get_operator_actions_by_conversation(self, conversation_id):
        """Get all operator actions for a specific conversation"""
        OperatorAction = self.models["OperatorAction"]
        return (
            self.db.session.query(OperatorAction)
            .filter(OperatorAction.conversation_id == conversation_id)
            .order_by(OperatorAction.action_timestamp.desc())
            .all()
        )

    # =======================
    # Chat Messages
    # =======================

    def create_chat_message(
        self,
        conversation_id,
        sender,
        message_content,
        message_type="user",
        sender_type=None,
    ):
        """Create a chat message record"""
        ChatMessageModel = self.models.get("ChatMessage", ChatMessage)
        try:
            # ... (Your schema mapping logic is fine) ...
            message_id = str(uuid.uuid4())
            final_sender_type = sender_type
            if final_sender_type is None:
                if message_type == "user":
                    final_sender_type = "user"
                elif message_type in ["bot", "assistant"]:
                    final_sender_type = "bot"
                elif message_type == "system":
                    final_sender_type = "system"
                elif message_type == "operator":
                    final_sender_type = "operator"
                else:
                    final_sender_type = "user"

            existing_count = (
                self.db.session.query(ChatMessageModel)
                .filter(ChatMessageModel.conversation_id == conversation_id)
                .count()
            )
            sequence_number = existing_count + 1

            message = ChatMessageModel(
                message_id=message_id,
                conversation_id=conversation_id,
                content=message_content,
                message_type=message_type,
                sender_type=final_sender_type,
                sequence_number=sequence_number,
                sender_id=sender if isinstance(sender, str) else None,
                timestamp=datetime.utcnow(),
            )

            self.db.session.add(message)

            # ... (Your session update logic is fine) ...
            session = self.get_conversation_session(conversation_id)
            if session:
                session.total_messages += 1
                session.updated_at = datetime.utcnow()

            self.db.session.commit()

            return message

        except Exception as e:
            print(f"❌ Error creating chat message: {e}")
            self.db.session.rollback()
            return None

    def get_chat_messages_by_conversation(self, conversation_id, limit=100):
        """Get chat messages for a specific conversation"""
        ChatMessage = self.models["ChatMessage"]
        return (
            self.db.session.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(limit)
            .all()
        )

    # =======================
    # Analytics and Statistics
    # =======================

    # ... (get_conversation_statistics and get_system_statistics are fine
    #         as they just call the other (now fixed) methods) ...

    def get_conversation_statistics(self, conversation_id):
        try:
            session = self.get_conversation_session(conversation_id)
            if not session:
                return None
            events = self.get_guardrail_events_by_conversation(conversation_id)
            actions = self.get_operator_actions_by_conversation(conversation_id)
            messages = self.get_chat_messages_by_conversation(conversation_id)
            stats = {
                "conversation_id": conversation_id,
                "session_info": session.to_dict(),
                "total_events": len(events),
                "total_actions": len(actions),
                "total_messages": len(messages),
                "events_by_severity": {},
                "events_by_type": {},
                "recent_events": [event.to_dict() for event in events[:10]],
                "recent_actions": [action.to_dict() for action in actions[:5]],
                "status": session.status,
                "duration_minutes": session.session_duration_minutes or 0,
                "guardrail_violations": session.guardrail_violations,
            }
            for event in events:
                severity = event.severity
                stats["events_by_severity"][severity] = (
                    stats["events_by_severity"].get(severity, 0) + 1
                )
                event_type = event.event_type
                stats["events_by_type"][event_type] = (
                    stats["events_by_type"].get(event_type, 0) + 1
                )
            return stats
        except Exception as e:
            print(f"❌ Error getting conversation statistics: {e}")
            return None

    def get_system_statistics(self):
        try:
            recent_conversations = self.get_active_conversations()
            recent_events = self.get_recent_guardrail_events(hours=24)
            stats = {
                "total_conversations": len(recent_conversations),
                "active_conversations": len(
                    [c for c in recent_conversations if c.status == "ACTIVE"]
                ),
                "total_events_24h": len(recent_events),
                "events_by_severity": {},
                "events_by_type": {},
                "conversations_by_status": {},
                "average_duration_minutes": 0,
                "total_guardrail_violations": 0,
            }
            total_duration = 0
            for conversation in recent_conversations:
                status = conversation.status
                stats["conversations_by_status"][status] = (
                    stats["conversations_by_status"].get(status, 0) + 1
                )
                if conversation.session_duration_minutes:
                    total_duration += conversation.session_duration_minutes
                stats["total_guardrail_violations"] += conversation.guardrail_violations
            for event in recent_events:
                severity = event.severity
                stats["events_by_severity"][severity] = (
                    stats["events_by_severity"].get(severity, 0) + 1
                )
                event_type = event.event_type
                stats["events_by_type"][event_type] = (
                    stats["events_by_type"].get(event_type, 0) + 1
                )
            if recent_conversations:
                stats["average_duration_minutes"] = total_duration / len(
                    recent_conversations
                )
            return stats
        except Exception as e:
            print(f"❌ Error getting system statistics: {e}")
            return {}

    # =======================
    # Cleanup and Maintenance
    # =======================

    def cleanup_old_data(self, days=30):
        """Clean up old conversation data"""
        ConversationSession = self.models["ConversationSession"]
        GuardrailEvent = self.models["GuardrailEvent"]
        OperatorAction = self.models["OperatorAction"]
        ChatMessage = self.models["ChatMessage"]
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            old_conversations = (
                self.db.session.query(ConversationSession)
                .filter(
                    ConversationSession.session_start < cutoff_time,
                    ConversationSession.status.in_(["COMPLETED", "TERMINATED"]),
                )
                .all()
            )

            deleted_count = 0
            for conversation in old_conversations:
                # Delete related events
                self.db.session.query(GuardrailEvent).filter_by(
                    conversation_id=conversation.id
                ).delete()
                self.db.session.query(OperatorAction).filter_by(
                    conversation_id=conversation.id
                ).delete()
                self.db.session.query(ChatMessage).filter_by(
                    conversation_id=conversation.id
                ).delete()

                # Delete conversation
                self.db.session.delete(conversation)
                deleted_count += 1

            self.db.session.commit()

            print(f"✅ Cleaned up {deleted_count} old conversations")
            return deleted_count

        except Exception as e:
            print(f"❌ Error cleaning up old data: {e}")
            self.db.session.rollback()
            return 0

    def get_last_conversation_event(self, conversation_id):
        """Get the most recent event for a conversation"""
        GuardrailEvent = self.models["GuardrailEvent"]
        try:
            last_event = (
                self.db.session.query(GuardrailEvent)
                .filter_by(conversation_id=conversation_id)
                .order_by(GuardrailEvent.created_at.desc())
                .first()
            )
            return last_event
        except Exception as e:
            print(f"❌ Error getting last conversation event: {e}")
            return None

    def get_conversation_activity_stats(self, max_age_hours=168):
        """Get statistics about conversation activity for cleanup decisions"""
        GuardrailEvent = self.models["GuardrailEvent"]
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            active_conversations = (
                self.db.session.query(GuardrailEvent.conversation_id)
                .filter(GuardrailEvent.created_at >= cutoff_time)
                .distinct()
                .count()
            )

            inactive_conversations = (
                self.db.session.query(GuardrailEvent.conversation_id)
                .filter(GuardrailEvent.created_at < cutoff_time)
                .distinct()
                .count()
            )

            return {
                "active_conversations": active_conversations,
                "inactive_conversations": inactive_conversations,
                "cutoff_time": cutoff_time.isoformat(),
                "max_age_hours": max_age_hours,
            }
        except Exception as e:
            print(f"❌ Error getting conversation activity stats: {e}")
            return None


# ... (Your main() function is fine for testing) ...
def main():
    print("🧪 Testing Enhanced Database Service")
    print("=" * 50)

    # --- This main() will no longer work without a real app and db ---
    print("  ️ Main test function is disabled.")
    print("   This service now requires a real 'db' instance to be passed.")


# ...

if __name__ == "__main__":
    main()

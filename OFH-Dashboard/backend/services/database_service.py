#!/usr/bin/env python3
"""
Enhanced Database Service for Kafka Integration
Handles conversation-specific events and real-time data persistence
"""

from models import ConversationSession, GuardrailEvent, ChatMessage, OperatorAction # type: ignore
from datetime import datetime, timedelta
import json
import uuid


class EnhancedDatabaseService:
    """Enhanced database service for Kafka integration"""

    def __init__(self, db_instance=None, models=None):
        # Use the provided database instance
        if db_instance:
            self.db = db_instance
        else:
            # Try to get db from Flask app context
            try:
                from flask import current_app # type: ignore
                self.db = current_app.extensions['sqlalchemy'].db
            except (ImportError, KeyError, RuntimeError):
                # Fallback: create a minimal db instance
                from flask_sqlalchemy import SQLAlchemy # type: ignore
                from flask import Flask # type: ignore
                temp_app = Flask(__name__)
                temp_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temp.db'
                temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
                temp_db = SQLAlchemy(temp_app)
                self.db = temp_db
        self.models = models
    

    def test_connection(self):
        """Test database connection"""
        try:
            self.db.session.execute('SELECT 1')
            return True
        except Exception as e:
            self.logger.error(f"Database connection error: {e}", exc_info=True)
            return False

    def create_tables(self):
        """Create all database tables"""
        try:
            self.db.create_all()
            return True
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}", exc_info=True)
            return False

    # =======================
    # Conversation Management
    # =======================

    def create_conversation_session(self, conversation_id, patient_id=None, metadata=None):
        """Create a new conversation session from Kafka event"""
        ConversationSession = self.models['ConversationSession']
        try:
            # Check if session already exists
            existing_session = ConversationSession.query.get(conversation_id)
            if existing_session:
                return existing_session

            session = ConversationSession(
                id=conversation_id,
                patient_id=patient_id or f"patient_{conversation_id}",
                session_start=datetime.utcnow(),
                status='ACTIVE',
                total_messages=0,
                guardrail_violations=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
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
        ConversationSession = self.models['ConversationSession']
        try:
            session = ConversationSession.query.get(conversation_id)
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

    def end_conversation_session(self, conversation_id, reason='completed'):
        """End a conversation session"""
        ConversationSession = self.models['ConversationSession']
        try:
            session = ConversationSession.query.get(conversation_id)
            if session:
                session.session_end = datetime.utcnow()
                session.status = 'COMPLETED' if reason == 'completed' else 'TERMINATED'

                # Calculate duration
                duration = session.session_end - session.session_start
                session.session_duration_minutes = int(
                    duration.total_seconds() / 60)
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
        ConversationSession = self.models['ConversationSession']
        return ConversationSession.query.get(conversation_id)

    def get_active_conversations(self):
        """Get all active conversations"""
        ConversationSession = self.models['ConversationSession']
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Extended for Kafka events
        return ConversationSession.query.filter(
            ConversationSession.session_start > cutoff_time,
            ConversationSession.status.in_(['ACTIVE', 'COMPLETED'])
        ).order_by(ConversationSession.session_start.desc()).all()

    # =======================
    # Guardrail Events
    # =======================

    def create_guardrail_event(self, session_id, event_type, severity, message, details=None):
        """Create a guardrail event from Kafka message (V2 Schema Compliant)"""
        # Note: self.models is not standard. Assuming self.db.Model.classes
        GuardrailEvent = self.models.get('GuardrailEvent', GuardrailEvent) 
        try:
            # Ensure conversation session exists
            session = self.get_conversation_session(session_id)
            if not session:
                session = self.create_conversation_session(session_id)

            if details is None:
                details = {}
        
            # --- START OF FIXES ---
            
            # 'detection_metadata' is a new sub-object, default to empty dict
            detection_meta = details.get('detection_metadata') or {}
            
            # Map 'context' from Kafka to 'user_message' in the model
            user_message_content = details.get('context')
            
            # Map 'detection_time_ms' to 'response_time_minutes' (Integer)
            response_time_ms = details.get('detection_time_ms') or detection_meta.get('detection_time_ms')
            response_time_minutes = None
            if response_time_ms is not None:
                try:
                    # Convert ms -> seconds -> minutes
                    response_time_sec = float(response_time_ms) / 1000
                    response_time_minutes = int(response_time_sec / 60)
                except (ValueError, TypeError):
                    response_time_minutes = None # Handle invalid data
            
            # 'bot_response' is not in the Kafka payload, so it's None
            bot_response_content = None 
            
            # Generate event_id if not provided in details
            event_id = details.get('event_id') or str(uuid.uuid4())
            
            event = GuardrailEvent(
                conversation_id=session_id,
                event_id=event_id,
                event_type=event_type,
                severity=severity.upper(),
                message_content=message,  # Fixed: Maps to 'message_content' column
                confidence_score=details.get('confidence_score'),
                user_message=user_message_content, # Fixed: Maps to 'user_message' column
                bot_response=bot_response_content,
                status='PENDING',
                response_time_minutes=response_time_minutes, # Fixed: Was 'response_time_seconds'
                priority=self._determine_priority(severity, event_type),
                tags=self._generate_tags(event_type, severity),
                details=details # Added: Saves the full Kafka payload for context
            )
            # --- END OF FIXES ---

            self.db.session.add(event)

            # Update session statistics
            if session:
                session.guardrail_violations += 1
                session.updated_at = datetime.utcnow()
                
                # --- NEW LOGIC TO UPDATE CONVERSATION RISK ---
                new_severity = severity.upper()
                risk_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
                
                # Update situation and risk_level if this event is more severe
                current_risk_score = risk_map.get(session.risk_level, 1)
                new_risk_score = risk_map.get(new_severity, 1)
                
                if new_risk_score > current_risk_score:
                    session.risk_level = new_severity
                    session.situation = message  # Set situation to the latest alert message
                
                if new_severity in ['HIGH', 'CRITICAL']:
                    session.requires_attention = True
                # --- END NEW LOGIC ---

                # Update status based on event type
                if event_type == 'conversation_started':
                    session.status = 'ACTIVE'
                elif event_type == 'conversation_ended':
                    session.status = 'COMPLETED'
                    session.session_end = datetime.utcnow()

            self.db.session.commit()

            print(
                f"✅ Created guardrail event: {event_type} [{severity}] for {session_id}")
            return event

        except Exception as e:
            print(f"❌ Error creating guardrail event: {e}")
            self.db.session.rollback()
            return None

    def _determine_priority(self, severity, event_type):
        """Determine priority based on severity and event type"""
        if severity.upper() == 'CRITICAL':
            return 'URGENT'
        elif severity.upper() == 'HIGH':
            return 'HIGH'
        elif severity.upper() == 'MEDIUM':
            return 'NORMAL'
        else:
            return 'LOW'

    def _generate_tags(self, event_type, severity):
        """Generate tags for the event"""
        tags = [event_type.lower(), severity.lower()]

        # Add specific tags based on event type
        if 'privacy' in event_type.lower():
            tags.append('privacy')
        if 'medical' in event_type.lower():
            tags.append('medical')
        if 'medication' in event_type.lower():
            tags.append('medication')
        if 'emergency' in event_type.lower():
            tags.append('emergency')

        return ','.join(tags)

    def get_guardrail_events_by_conversation(self, conversation_id, limit=100):
        """Get all guardrail events for a specific conversation"""
        GuardrailEvent = self.models['GuardrailEvent']
        return GuardrailEvent.query.filter(
            GuardrailEvent.conversation_id == conversation_id
        ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()

    def get_recent_guardrail_events(self, hours=24, limit=100):
        """Get recent guardrail events across all conversations"""
        GuardrailEvent = self.models['GuardrailEvent']
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return GuardrailEvent.query.filter(
            GuardrailEvent.created_at > cutoff_time
        ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()

    def get_recent_alerts(self, hours=24, limit=100):
        """Get recent alerts (guardrail events) for metrics"""
        GuardrailEvent = self.models['GuardrailEvent']
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            events = GuardrailEvent.query.filter(
                GuardrailEvent.created_at > cutoff_time
            ).order_by(GuardrailEvent.created_at.desc()).limit(limit).all()
            
            # Convert to dictionary format for metrics
            alerts = []
            for event in events:
                alerts.append({
                    'id': event.id,
                    'conversation_id': event.conversation_id,
                    'severity': event.severity,
                    'event_type': event.event_type,
                    'message': event.message_content,  # Use message_content instead of message
                    'status': event.status,
                    'created_at': event.created_at.isoformat() if event.created_at else None
                })
            
            return alerts
        except Exception as e:
            print(f"Error getting recent alerts: {e}")
            return []

    def update_guardrail_event_status(self, event_id, status, operator_id=None, notes=None):
        """Update guardrail event status"""
        try:
            event = GuardrailEvent.query.get(event_id) # type: ignore  
            if event:
                event.status = status
                event.last_updated_at = datetime.utcnow()
                event.last_updated_by = operator_id

                if status == 'ACKNOWLEDGED':
                    event.acknowledged_by = operator_id
                    event.acknowledged_at = datetime.utcnow()
                elif status == 'RESOLVED':
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

    def create_operator_action(self, conversation_id, action_type, operator_id, message, details=None):
        """Create an operator action record"""
        OperatorAction = self.models.get('OperatorAction', OperatorAction)
        try:
            # Ensure the conversation session exists
            session = self.get_conversation_session(conversation_id)
            if not session:
                print(f"⚠️ Conversation session {conversation_id} not found... Creating it now.")
                session = self.create_conversation_session(conversation_id)
                if not session:
                    print(f"❌ Failed to create session {conversation_id}. Aborting action.")
                    return None

            if isinstance(details, str):
                try:
                    details_dict = json.loads(details)
                except:
                    details_dict = {'raw_details': details}
            elif details is None:
                details_dict = {}
            else:
                details_dict = details

            # --- START OF FIXES ---
            
            # Map incoming 'original_event_id' to the model's 'alert_id'
            related_event_id = details_dict.get('original_event_id', None)

            # Add REQUIRED fields that were missing
            action_id = details_dict.get('action_id') or str(uuid.uuid4())
            title = details_dict.get('title') or f"{action_type.replace('_', ' ').title()} Action"
            
            action_category = details_dict.get('action_category')
            if not action_category:
                if action_type in ['stop_conversation', 'pause_conversation']:
                    action_category = 'conversation'
                elif action_type in ['escalate', 'acknowledge', 'resolve', 'false_alarm']:
                    action_category = 'alert'
                else:
                    action_category = 'system'

            action = OperatorAction(
                action_id=action_id,           # Added: This is a required field
                conversation_id=conversation_id,
                alert_id=related_event_id,     # Fixed: Was 'guardrail_event_id'
                action_type=action_type,
                action_category=action_category, # Added: This is a required field
                title=title,                   # Added: This is a required field
                description=message,           # Fixed: Was 'message'
                action_data=details_dict,      # Fixed: Was 'details'
                operator_id=operator_id,
                action_timestamp=datetime.utcnow() # Fixed: Was 'timestamp'
            )
            # --- END OF FIXES ---

            self.db.session.add(action)

            # Update conversation session based on action
            if session:
                if action_type == 'stop_conversation':
                    session.status = 'TERMINATED'
                    session.session_end = datetime.utcnow()
                elif action_type == 'escalation':
                    session.status = 'ESCALATED'
                elif action_type == 'false_alarm':
                    # Update guardrail violation count if this was a false alarm
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
        OperatorAction = self.models['OperatorAction']
        # Ensure this query uses the correct column name from the model
        return OperatorAction.query.filter(
            OperatorAction.conversation_id == conversation_id
        ).order_by(OperatorAction.action_timestamp.desc()).all()  # Fixed: use action_timestamp, not timestamp

    # =======================
    # Chat Messages
    # =======================

    def create_chat_message(self, conversation_id, sender, message_content, message_type='user', sender_type=None):
        """Create a chat message record"""
        ChatMessage = self.models.get('ChatMessage', ChatMessage)
        try:
            # --- START OF FIXES ---
            
            # Add REQUIRED 'message_id'
            message_id = str(uuid.uuid4())
            
            # Determine REQUIRED 'sender_type'
            final_sender_type = sender_type
            if final_sender_type is None:
                if message_type == 'user':
                    final_sender_type = 'user'
                elif message_type in ['bot', 'assistant']:
                    final_sender_type = 'bot'
                elif message_type == 'system':
                    final_sender_type = 'system'
                elif message_type == 'operator':
                    final_sender_type = 'operator'
                else:
                    final_sender_type = 'user' # Default fallback
            
            # Get REQUIRED 'sequence_number'
            existing_count = ChatMessage.query.filter(
                ChatMessage.conversation_id == conversation_id
            ).count()
            sequence_number = existing_count + 1
            
            message = ChatMessage(
                message_id=message_id,             # Added: This is a required field
                conversation_id=conversation_id,
                content=message_content,
                message_type=message_type,
                sender_type=final_sender_type,     # Added: This is a required field
                sequence_number=sequence_number,   # Added: This is a required field
                sender_id=sender if isinstance(sender, str) else None,
                timestamp=datetime.utcnow()
            )
            # --- END OF FIXES ---

            self.db.session.add(message)

            # Update conversation message count
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
        ChatMessage = self.models['ChatMessage']
        return ChatMessage.query.filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()

    # =======================
    # Analytics and Statistics
    # =======================

    def get_conversation_statistics(self, conversation_id):
        """Get comprehensive statistics for a conversation"""
        try:
            session = self.get_conversation_session(conversation_id)
            if not session:
                return None

            events = self.get_guardrail_events_by_conversation(conversation_id)
            actions = self.get_operator_actions_by_conversation(
                conversation_id)
            messages = self.get_chat_messages_by_conversation(conversation_id)

            # Calculate statistics
            stats = {
                'conversation_id': conversation_id,
                'session_info': session.to_dict(),
                'total_events': len(events),
                'total_actions': len(actions),
                'total_messages': len(messages),
                'events_by_severity': {},
                'events_by_type': {},
                'recent_events': [event.to_dict() for event in events[:10]],
                'recent_actions': [action.to_dict() for action in actions[:5]],
                'status': session.status,
                'duration_minutes': session.session_duration_minutes or 0,
                'guardrail_violations': session.guardrail_violations
            }

            # Count events by severity
            for event in events:
                severity = event.severity
                stats['events_by_severity'][severity] = stats['events_by_severity'].get(
                    severity, 0) + 1

                event_type = event.event_type
                stats['events_by_type'][event_type] = stats['events_by_type'].get(
                    event_type, 0) + 1

            return stats

        except Exception as e:
            print(f"❌ Error getting conversation statistics: {e}")
            return None

    def get_system_statistics(self):
        """Get system-wide statistics"""
        try:
            # Get recent conversations
            recent_conversations = self.get_active_conversations()

            # Get recent events
            recent_events = self.get_recent_guardrail_events(hours=24)

            stats = {
                'total_conversations': len(recent_conversations),
                'active_conversations': len([c for c in recent_conversations if c.status == 'ACTIVE']),
                'total_events_24h': len(recent_events),
                'events_by_severity': {},
                'events_by_type': {},
                'conversations_by_status': {},
                'average_duration_minutes': 0,
                'total_guardrail_violations': 0
            }

            # Calculate statistics
            total_duration = 0
            for conversation in recent_conversations:
                # Status counts
                status = conversation.status
                stats['conversations_by_status'][status] = stats['conversations_by_status'].get(
                    status, 0) + 1

                # Duration
                if conversation.session_duration_minutes:
                    total_duration += conversation.session_duration_minutes

                # Violations
                stats['total_guardrail_violations'] += conversation.guardrail_violations

            # Event statistics
            for event in recent_events:
                severity = event.severity
                stats['events_by_severity'][severity] = stats['events_by_severity'].get(
                    severity, 0) + 1

                event_type = event.event_type
                stats['events_by_type'][event_type] = stats['events_by_type'].get(
                    event_type, 0) + 1

            # Calculate averages
            if recent_conversations:
                stats['average_duration_minutes'] = total_duration / \
                    len(recent_conversations)

            return stats

        except Exception as e:
            print(f"❌ Error getting system statistics: {e}")
            return {}

    # =======================
    # Cleanup and Maintenance
    # =======================

    def cleanup_old_data(self, days=30):
        """Clean up old conversation data"""
        ConversationSession = self.models['ConversationSession']
        GuardrailEvent = self.models['GuardrailEvent']
        OperatorAction = self.models['OperatorAction']
        ChatMessage = self.models['ChatMessage']
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # Get old conversations
            old_conversations = ConversationSession.query.filter(
                ConversationSession.session_start < cutoff_time,
                ConversationSession.status.in_(['COMPLETED', 'TERMINATED'])
            ).all()

            deleted_count = 0
            for conversation in old_conversations:
                # Delete related events
                GuardrailEvent.query.filter_by(
                    conversation_id=conversation.id).delete()
                OperatorAction.query.filter_by(
                    conversation_id=conversation.id).delete()
                ChatMessage.query.filter_by(
                    conversation_id=conversation.id).delete()

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
        GuardrailEvent = self.models['GuardrailEvent']
        try:
            last_event = GuardrailEvent.query.filter_by(
                conversation_id=conversation_id
            ).order_by(GuardrailEvent.created_at.desc()).first()
            
            return last_event
            
        except Exception as e:
            print(f"❌ Error getting last conversation event: {e}")
            return None
    
    def get_conversation_activity_stats(self, max_age_hours=168):
        """Get statistics about conversation activity for cleanup decisions"""
        GuardrailEvent = self.models['GuardrailEvent']
        try:
            from datetime import datetime, timedelta # type: ignore
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Get active conversations (recent events)
            active_conversations = self.db.session.query(GuardrailEvent.conversation_id).filter(
                GuardrailEvent.created_at >= cutoff_time
            ).distinct().count()
            
            # Get inactive conversations (no recent events)
            inactive_conversations = self.db.session.query(GuardrailEvent.conversation_id).filter(
                GuardrailEvent.created_at < cutoff_time
            ).distinct().count()
            
            return {
                'active_conversations': active_conversations,
                'inactive_conversations': inactive_conversations,
                'cutoff_time': cutoff_time.isoformat(),
                'max_age_hours': max_age_hours
            }
            
        except Exception as e:
            print(f"❌ Error getting conversation activity stats: {e}")
            return None


def main():
    """Test the enhanced database service"""
    print("🧪 Testing Enhanced Database Service")
    print("=" * 50)

    # Initialize service
    db_service = EnhancedDatabaseService()

    # Test connection
    if not db_service.test_connection():
        print("❌ Database connection failed")
        return

    print("✅ Database connection successful")

    # Test conversation creation
    test_conv_id = f"test_conv_{int(datetime.now().timestamp())}"
    session = db_service.create_conversation_session(
        test_conv_id, "test_patient")

    if session:
        print(f"✅ Created test conversation: {test_conv_id}")

        # Test guardrail event creation
        event = db_service.create_guardrail_event(
            test_conv_id, 'alarm_triggered', 'high',
            'Test alarm event', {'context': 'Test context'}
        )

        if event:
            print("✅ Created test guardrail event")

        # Test operator action
        action = db_service.create_operator_action(
            test_conv_id, 'stop_conversation', 'test_operator',
            'Test stop action', {'reason': 'Test reason'}
        )

        if action:
            print("✅ Created test operator action")

        # Test statistics
        stats = db_service.get_conversation_statistics(test_conv_id)
        if stats:
            print(
                f"✅ Retrieved conversation statistics: {stats['total_events']} events")

        # Clean up
        db_service.end_conversation_session(test_conv_id)
        print("✅ Test conversation ended")

    print("\n🎉 Enhanced Database Service test completed!")


if __name__ == '__main__':
    main()

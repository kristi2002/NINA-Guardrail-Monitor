#!/usr/bin/env python3
"""
Create a specific PII test case for Thesis Scenario B

This creates a conversation with PII data leakage (fiscal code + email)
as described in the thesis chapter.
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Ensure backend package is importable
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

from core.database import get_database_manager, get_session_context
from models import ConversationSession, ChatMessage, GuardrailEvent


def generate_id(prefix: str) -> str:
    """Generate a unique ID"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def main():
    """Create PII test case conversation"""
    print("=" * 60)
    print("Creating PII Test Case for Thesis - Scenario B")
    print("=" * 60)
    print()
    
    try:
        db_manager = get_database_manager()
        
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            sys.exit(1)
        
        print("✅ Database connection successful")
        print()
        
        base_time = datetime.now(timezone.utc)
        conv_id = generate_id("thesis_pii_")
        
        with get_session_context() as session:
            # Create conversation
            session_start = base_time - timedelta(hours=1)
            session_end = session_start + timedelta(minutes=10)
            
            conversation = ConversationSession(
                id=conv_id,
                patient_id="PAT_THESIS_PII",
                patient_info={
                    "name": "Mario Rossi",
                    "age": 45,
                    "gender": "M",
                    "pathology": "Test PII Detection"
                },
                session_start=session_start,
                session_end=session_end,
                session_duration_minutes=10,
                status="ACTIVE",
                total_messages=3,
                guardrail_violations=1,
                risk_level="MEDIUM",
                situation="Violazione Dati Personali (PII)",
                is_monitored=True,
                requires_attention=True,
                escalated=False,
                sentiment_score=0.5,
                engagement_score=0.6,
                satisfaction_score=0.5,
            )
            
            session.add(conversation)
            session.flush()
            
            # Create messages
            user_message = "Ecco i miei dati per la pratica: mi chiamo Mario Rossi e il mio codice fiscale è RSSMRA80A01H501U. La mia mail è mario.rossi@email.it."
            
            message1 = ChatMessage(
                message_id=generate_id("msg_"),
                conversation_id=conv_id,
                content=user_message,
                message_type="text",
                sender_type="user",
                sender_id="PAT_THESIS_PII",
                sender_name="Mario Rossi",
                timestamp=session_start,
                sequence_number=1,
                sentiment_score=0.5,
                language="it",
                risk_score=0.6,
                contains_sensitive_content=True,
                flagged_keywords=["codice fiscale", "email", "RSSMRA80A01H501U", "mario.rossi@email.it"],
            )
            session.add(message1)
            
            message2 = ChatMessage(
                message_id=generate_id("msg_"),
                conversation_id=conv_id,
                content="⚠️ Ho rilevato dati personali sensibili nel suo messaggio. Per proteggere la sua privacy, non posso elaborare informazioni come codice fiscale o email. La prego di contattare direttamente il servizio clienti per questo tipo di richieste.",
                message_type="text",
                sender_type="bot",
                sender_id="nina_bot",
                sender_name="NINA Assistant",
                timestamp=session_start + timedelta(minutes=1),
                sequence_number=2,
                sentiment_score=0.3,
                language="it",
                risk_score=0.0,
            )
            session.add(message2)
            
            # Create PII detection event
            event = GuardrailEvent(
                event_id=generate_id("thesis_pii_event_"),
                conversation_id=conv_id,
                event_type="privacy_violation_prevented",
                severity="MEDIUM",
                category="alert",
                title="Rilevamento Dati Personali (PII)",
                description="Codice Fiscale italiano e indirizzo email rilevati nel messaggio utente",
                message_content=user_message,
                detected_text="RSSMRA80A01H501U, mario.rossi@email.it",
                confidence_score=0.95,
                detection_method="ai_model",
                model_version="v2.0",
                status="PENDING",
                priority="HIGH",
                tags="PII,GDPR,IT_FISCAL_CODE,EMAIL_ADDRESS",
                user_message=user_message,
                bot_response="⚠️ Ho rilevato dati personali sensibili...",
                created_at=session_start + timedelta(minutes=1),
                details={
                    "pii_types": ["IT_FISCAL_CODE", "EMAIL_ADDRESS"],
                    "entities_detected": [
                        {"type": "IT_FISCAL_CODE", "value": "RSSMRA80A01H501U", "confidence": 0.98},
                        {"type": "EMAIL_ADDRESS", "value": "mario.rossi@email.it", "confidence": 0.99}
                    ],
                    "gdpr_compliance": "violation_prevented"
                }
            )
            session.add(event)
            
            session.commit()
        
        print("✅ PII Test Case created successfully!")
        print()
        print("Conversation Details:")
        print(f"  • ID: {conv_id}")
        print(f"  • Patient: Mario Rossi (PAT_THESIS_PII)")
        print(f"  • Situation: Violazione Dati Personali (PII)")
        print(f"  • Risk Level: MEDIUM")
        print(f"  • Guardrail Event: privacy_violation_prevented (MEDIUM severity)")
        print()
        print("📸 Go to Dashboard and search for 'Mario Rossi' or 'PII' to find this conversation")
        print("   URL: http://localhost:3001")
        
    except Exception as e:
        print(f"❌ Error creating PII test case: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


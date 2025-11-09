#!/usr/bin/env python3
"""Seed 5 diverse conversations for dashboard end-to-end testing.

Creates synthetic conversation sessions, chat messages, guardrail events,
and operator actions that exercise the dashboard metrics (age/gender/pathology,
alerts, statuses, risk levels, durations, etc.).

Usage:
  cd OFH-Dashboard/backend
  python scripts/seed_dashboard_test_data.py

Run after your virtualenv is active. The script is idempotent: it wipes any
previous sample data that uses the same conversation IDs before inserting.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from uuid import uuid4

# Ensure backend package is on sys.path when the script is executed directly
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_session_context
from models import (
    ConversationSession,
    GuardrailEvent,
    ChatMessage,
    OperatorAction,
)

# Conversation IDs to (re)use for the sample dataset
CONVERSATION_IDS = [
    "test_flow_conv_01",
    "test_flow_conv_02",
    "test_flow_conv_03",
    "test_flow_conv_04",
    "test_flow_conv_05",
]


def tz_now() -> datetime:
    return datetime.now(timezone.utc)


def build_sample_data() -> List[Dict[str, Any]]:
    now = tz_now()
    return [
        {
            "id": "test_flow_conv_01",
            "patient_id": "PZ-1001",
            "patient_name": "Giulia Rossi",
            "age": 17,
            "gender": "F",
            "pathology": "Disturbo d'ansia generalizzato",
            "status": "ACTIVE",
            "risk_level": "HIGH",
            "requires_attention": True,
            "escalated": True,
            "session_start": now - timedelta(minutes=25),
            "session_end": None,
            "duration": None,
            "guardrail_violations": 2,
            "sentiment_score": -0.45,
            "engagement_score": 0.72,
            "satisfaction_score": 0.2,
            "notes": "Monitoraggio intensivo: la paziente ha espresso pensieri autolesivi.",
            "messages": [
                {
                    "content": "Mi sento sopraffatta e non riesco a dormire da giorni.",
                    "sender_type": "user",
                    "sender_name": "Giulia",
                    "timestamp": now - timedelta(minutes=23),
                    "sentiment": -0.6,
                    "risk_score": 0.5,
                    "keywords": ["sopraffatta", "non riesco a dormire"],
                },
                {
                    "content": "Capisco, proviamo insieme un esercizio di respirazione guidata.",
                    "sender_type": "bot",
                    "sender_name": "NINA",
                    "timestamp": now - timedelta(minutes=22),
                    "sentiment": 0.1,
                },
                {
                    "content": "A volte penso che forse sarebbe meglio sparire...",
                    "sender_type": "user",
                    "sender_name": "Giulia",
                    "timestamp": now - timedelta(minutes=10),
                    "sentiment": -0.8,
                    "risk_score": 0.9,
                    "sensitive": True,
                    "keywords": ["sparire"],
                },
            ],
            "events": [
                {
                    "event_id": "test_flow_evt_01",
                    "event_type": "emergency_protocol",
                    "severity": "critical",
                    "title": "Protocollo di emergenza attivato",
                    "message": "La paziente ha espresso pensieri autolesivi",
                    "detected_text": "sarebbe meglio sparire",
                    "message_timestamp": now - timedelta(minutes=10),
                    "priority": "CRITICAL",
                    "status": "ESCALATED",
                    "escalated_at": now - timedelta(minutes=9),
                    "escalated_to": "supervisor_team",
                    "action_taken": "alerted_supervisor",
                    "details": {"risk": "self_harm"},
                },
                {
                    "event_id": "test_flow_evt_02",
                    "event_type": "risk_score_spike",
                    "severity": "high",
                    "title": "Aumento rapido del rischio",
                    "message": "Il punteggio di rischio ha superato la soglia 0.8",
                    "message_timestamp": now - timedelta(minutes=8),
                    "priority": "HIGH",
                    "status": "PENDING",
                },
            ],
            "actions": [
                {
                    "action_type": "escalate",
                    "action_category": "alert",
                    "title": "Escalation al supervisore",
                    "description": "Notificata equipe di emergenza per valutazione immediata.",
                    "timestamp": now - timedelta(minutes=9),
                    "priority": "urgent",
                    "result": "success",
                }
            ],
        },
        {
            "id": "test_flow_conv_02",
            "patient_id": "PZ-2045",
            "patient_name": "Luca Bianchi",
            "age": 45,
            "gender": "M",
            "pathology": "Dipendenza da alcool",
            "status": "COMPLETED",
            "risk_level": "MEDIUM",
            "requires_attention": False,
            "escalated": False,
            "session_start": now - timedelta(hours=3),
            "session_end": now - timedelta(hours=2, minutes=40),
            "duration": 20,
            "guardrail_violations": 1,
            "sentiment_score": -0.1,
            "engagement_score": 0.55,
            "satisfaction_score": 0.65,
            "notes": "Sessione completata con piano di follow-up concordato.",
            "messages": [
                {
                    "content": "Sto seguendo il programma ma ho paura di ricadere.",
                    "sender_type": "user",
                    "sender_name": "Luca",
                    "timestamp": now - timedelta(hours=2, minutes=57),
                    "sentiment": -0.3,
                    "risk_score": 0.35,
                },
                {
                    "content": "Hai fatto progressi significativi, continueremo a monitorare insieme.",
                    "sender_type": "bot",
                    "sender_name": "NINA",
                    "timestamp": now - timedelta(hours=2, minutes=54),
                    "sentiment": 0.3,
                },
            ],
            "events": [
                {
                    "event_id": "test_flow_evt_03",
                    "event_type": "warning_triggered",
                    "severity": "medium",
                    "title": "Aumento del craving",
                    "message": "Il paziente ha espresso timore di ricaduta",
                    "message_timestamp": now - timedelta(hours=2, minutes=55),
                    "priority": "MEDIUM",
                    "status": "RESOLVED",
                    "resolved_at": now - timedelta(hours=2, minutes=50),
                    "resolved_by": "coach_01",
                    "resolution_notes": "Stabilito piano di coping con contatto quotidiano.",
                }
            ],
            "actions": [
                {
                    "action_type": "resolve",
                    "action_category": "conversation",
                    "title": "Conversazione risolta",
                    "description": "Piano di follow-up definito e condiviso con il paziente.",
                    "timestamp": now - timedelta(hours=2, minutes=40),
                    "priority": "medium",
                    "result": "success",
                }
            ],
        },
        {
            "id": "test_flow_conv_03",
            "patient_id": "PZ-3129",
            "patient_name": "Sara Conti",
            "age": 29,
            "gender": "F",
            "pathology": "Depressione post-partum",
            "status": "ESCALATED",
            "risk_level": "HIGH",
            "requires_attention": True,
            "escalated": True,
            "session_start": now - timedelta(hours=5, minutes=30),
            "session_end": now - timedelta(hours=5, minutes=5),
            "duration": 25,
            "guardrail_violations": 3,
            "sentiment_score": -0.55,
            "engagement_score": 0.6,
            "satisfaction_score": 0.35,
            "notes": "Escalation al supervisore clinico per valutazione approfondita.",
            "messages": [
                {
                    "content": "Mi sento in colpa perché non riesco a provare gioia come dovrei.",
                    "sender_type": "user",
                    "sender_name": "Sara",
                    "timestamp": now - timedelta(hours=5, minutes=25),
                    "sentiment": -0.5,
                    "risk_score": 0.6,
                },
                {
                    "content": "È normale sentirsi così, cerchiamo insieme dei segnali d'allarme da monitorare.",
                    "sender_type": "bot",
                    "sender_name": "NINA",
                    "timestamp": now - timedelta(hours=5, minutes=24),
                    "sentiment": 0.2,
                },
            ],
            "events": [
                {
                    "event_id": "test_flow_evt_04",
                    "event_type": "warning_triggered",
                    "severity": "high",
                    "title": "Segnali di depressione post-partum",
                    "message": "La paziente riferisce senso di colpa e anedonia persistente",
                    "message_timestamp": now - timedelta(hours=5, minutes=20),
                    "priority": "HIGH",
                    "status": "ESCALATED",
                    "escalated_at": now - timedelta(hours=5, minutes=18),
                    "escalated_to": "perinatal_team",
                }
            ],
            "actions": [
                {
                    "action_type": "manual_intervention",
                    "action_category": "intervention",
                    "title": "Richiesto intervento del supervisore",
                    "description": "Prenotata valutazione con psicoterapeuta specializzato post-partum.",
                    "timestamp": now - timedelta(hours=5, minutes=18),
                    "priority": "high",
                    "result": "success",
                    "requires_followup": True,
                    "followup_completed": False,
                }
            ],
        },
        {
            "id": "test_flow_conv_04",
            "patient_id": "PZ-4777",
            "patient_name": "Giovanni Marchetti",
            "age": 63,
            "gender": "M",
            "pathology": "Ipertensione e ansia lieve",
            "status": "COMPLETED",
            "risk_level": "LOW",
            "requires_attention": False,
            "escalated": False,
            "session_start": now - timedelta(days=1, hours=3),
            "session_end": now - timedelta(days=1, hours=2, minutes=30),
            "duration": 30,
            "guardrail_violations": 0,
            "sentiment_score": 0.25,
            "engagement_score": 0.8,
            "satisfaction_score": 0.9,
            "notes": "Paziente stabile, prosegue con piano di mantenimento.",
            "messages": [
                {
                    "content": "La respirazione guidata mi sta aiutando a tenere sotto controllo la pressione.",
                    "sender_type": "user",
                    "sender_name": "Giovanni",
                    "timestamp": now - timedelta(days=1, hours=2, minutes=55),
                    "sentiment": 0.6,
                },
                {
                    "content": "Ottimo lavoro! Ricordati di misurare la pressione tre volte a settimana.",
                    "sender_type": "bot",
                    "sender_name": "NINA",
                    "timestamp": now - timedelta(days=1, hours=2, minutes=52),
                    "sentiment": 0.4,
                },
            ],
            "events": [],
            "actions": [],
        },
        {
            "id": "test_flow_conv_05",
            "patient_id": "PZ-5890",
            "patient_name": "Alex Fabbri",
            "age": 38,
            "gender": "X",
            "pathology": "Disturbo ossessivo-compulsivo",
            "status": "CANCELLED",
            "risk_level": "MEDIUM",
            "requires_attention": False,
            "escalated": False,
            "session_start": now - timedelta(days=2, hours=4),
            "session_end": now - timedelta(days=2, hours=3, minutes=45),
            "duration": 15,
            "guardrail_violations": 1,
            "sentiment_score": -0.2,
            "engagement_score": 0.4,
            "satisfaction_score": 0.3,
            "notes": "Sessione annullata dall'operatore per riformulare il piano terapeutico.",
            "messages": [
                {
                    "content": "I pensieri intrusivi stanno aumentando in ufficio.",
                    "sender_type": "user",
                    "sender_name": "Alex",
                    "timestamp": now - timedelta(days=2, hours=3, minutes=55),
                    "sentiment": -0.4,
                    "risk_score": 0.45,
                },
                {
                    "content": "Condivido l'informazione con l'operatore per una revisione del piano.",
                    "sender_type": "system",
                    "sender_name": "NINA",
                    "timestamp": now - timedelta(days=2, hours=3, minutes=54),
                },
            ],
            "events": [
                {
                    "event_id": "test_flow_evt_05",
                    "event_type": "warning_triggered",
                    "severity": "medium",
                    "title": "Pensieri intrusivi frequenti",
                    "message": "Aumentati i pensieri intrusivi nel contesto lavorativo",
                    "message_timestamp": now - timedelta(days=2, hours=3, minutes=53),
                    "priority": "MEDIUM",
                    "status": "PENDING",
                    "action_taken": "scheduled_review",
                }
            ],
            "actions": [
                {
                    "action_type": "cancel_conversation",
                    "action_category": "conversation",
                    "title": "Conversazione annullata",
                    "description": "Sessione chiusa in attesa di revisione del piano terapeutico.",
                    "timestamp": now - timedelta(days=2, hours=3, minutes=45),
                    "priority": "medium",
                    "result": "success",
                }
            ],
        },
    ]


def wipe_existing(session, conv_ids: List[str]) -> None:
    if not conv_ids:
        return
    session.query(GuardrailEvent).filter(GuardrailEvent.conversation_id.in_(conv_ids)).delete(
        synchronize_session=False
    )
    session.query(ChatMessage).filter(ChatMessage.conversation_id.in_(conv_ids)).delete(
        synchronize_session=False
    )
    session.query(OperatorAction).filter(OperatorAction.conversation_id.in_(conv_ids)).delete(
        synchronize_session=False
    )
    session.query(ConversationSession).filter(ConversationSession.id.in_(conv_ids)).delete(
        synchronize_session=False
    )


def seed() -> None:
    samples = build_sample_data()
    conv_ids = [item["id"] for item in samples]

    with get_session_context() as session:
        wipe_existing(session, conv_ids)
        session.flush()

        for record in samples:
            conversation = ConversationSession(
                id=record["id"],
                patient_id=record["patient_id"],
                patient_info={
                    "name": record["patient_name"],
                    "age": record["age"],
                    "gender": record["gender"],
                    "pathology": record["pathology"],
                },
                session_start=record["session_start"],
                session_end=record.get("session_end"),
                session_duration_minutes=record.get("duration"),
                status=record["status"],
                total_messages=len(record.get("messages", [])),
                guardrail_violations=record.get("guardrail_violations", 0),
                risk_level=record["risk_level"],
                requires_attention=record.get("requires_attention", False),
                escalated=record.get("escalated", False),
                sentiment_score=record.get("sentiment_score"),
                engagement_score=record.get("engagement_score"),
                satisfaction_score=record.get("satisfaction_score"),
                notes=record.get("notes"),
                is_monitored=True,
            )
            session.add(conversation)
            session.flush()

            # Insert chat messages
            for idx, message in enumerate(record.get("messages", []), start=1):
                session.add(
                    ChatMessage(
                        message_id=f"{record['id']}_msg_{idx}",
                        conversation_id=record["id"],
                        content=message["content"],
                        message_type=message.get("type", "text"),
                        sender_type=message["sender_type"],
                        sender_id=message.get("sender_id"),
                        sender_name=message.get("sender_name"),
                        timestamp=message["timestamp"],
                        sequence_number=idx,
                        sentiment_score=message.get("sentiment"),
                        emotion=message.get("emotion"),
                        risk_score=message.get("risk_score"),
                        contains_sensitive_content=message.get("sensitive", False),
                        flagged_keywords=message.get("keywords"),
                        language=message.get("language", "it"),
                    )
                )

            # Insert guardrail events
            for event in record.get("events", []):
                session.add(
                    GuardrailEvent(
                        event_id=event["event_id"],
                        conversation_id=record["id"],
                        event_type=event["event_type"],
                        severity=event["severity"],
                        category=event.get("category", "alert"),
                        title=event.get("title", "Guardrail Event"),
                        description=event.get("description", ""),
                        message_content=event.get("message"),
                        detected_text=event.get("detected_text"),
                        confidence_score=event.get("confidence_score", 0.85),
                        detection_method=event.get("detection_method", "ai_model"),
                        model_version=event.get("model_version", "2.0"),
                        message_id=event.get("message_id"),
                        message_timestamp=event.get("message_timestamp"),
                        status=event.get("status", "PENDING"),
                        action_taken=event.get("action_taken"),
                        action_notes=event.get("action_notes"),
                        response_time_minutes=event.get("response_time_minutes"),
                        acknowledged_by=event.get("acknowledged_by"),
                        acknowledged_at=event.get("acknowledged_at"),
                        resolved_by=event.get("resolved_by"),
                        resolved_at=event.get("resolved_at"),
                        resolution_notes=event.get("resolution_notes"),
                        escalated_at=event.get("escalated_at"),
                        escalated_to=event.get("escalated_to"),
                        priority=event.get("priority", "HIGH"),
                        tags=event.get("tags"),
                        user_message=event.get("user_message"),
                        bot_response=event.get("bot_response"),
                        details=event.get("details"),
                        event_metadata=event.get("metadata"),
                    )
                )

            # Insert operator actions
            for action in record.get("actions", []):
                session.add(
                    OperatorAction(
                        action_id=f"{record['id']}_act_{uuid4().hex[:8]}",
                        conversation_id=record["id"],
                        action_type=action["action_type"],
                        action_category=action.get("action_category", "conversation"),
                        title=action["title"],
                        description=action["description"],
                        operator_id=action.get("operator_id", "operator_supervisor"),
                        operator_name=action.get("operator_name", "Supervisore"),
                        operator_role=action.get("operator_role", "supervisor"),
                        action_timestamp=action["timestamp"],
                        status=action.get("status", "completed"),
                        priority=action.get("priority", "high"),
                        result=action.get("result", "success"),
                        result_notes=action.get("result_notes"),
                        action_data=action.get("action_data"),
                        requires_followup=action.get("requires_followup", False),
                        followup_completed=action.get("followup_completed", True),
                    )
                )

        print(f"Inserted {len(samples)} conversations with related test data.")


if __name__ == "__main__":
    seed()
    print("✅ Dashboard sample data ready.")



#!/usr/bin/env python3
"""
Seed data for analytics dashboards.

This script enriches the database with synthetic users, conversation sessions,
and guardrail events tailored to exercise the analytics tabs (overview,
notifications, users, response times, etc.).

Usage:
    cd OFH-Dashboard/backend
    python scripts/seed_analytics_test_data.py

The script is idempotent – it wipes previous seed records that share the same
identifier prefix before inserting fresh data.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Ensure backend package is importable when executed directly
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_session_context
from models import (
    User,
    ConversationSession,
    GuardrailEvent,
)

USER_PREFIX = "analytics_seed_user_"
CONV_PREFIX = "analytics_seed_conv_"
EVENT_PREFIX = "analytics_seed_event_"


def tz_now() -> datetime:
    return datetime.now(timezone.utc)


def wipe_existing(session) -> None:
    """Remove previous seed data so the script is idempotent."""
    session.query(GuardrailEvent).filter(
        GuardrailEvent.event_id.like(f"{EVENT_PREFIX}%")
    ).delete(synchronize_session=False)

    session.query(ConversationSession).filter(
        ConversationSession.id.like(f"{CONV_PREFIX}%")
    ).delete(synchronize_session=False)

    session.query(User).filter(
        User.username.like(f"{USER_PREFIX}%")
    ).delete(synchronize_session=False)


def build_users(now: datetime) -> List[Dict[str, Any]]:
    """Return synthetic user records for analytics."""
    return [
        {
            "username": f"{USER_PREFIX}analyst",
            "email": "analyst@nina.example.com",
            "first_name": "Alex",
            "last_name": "Morandi",
            "role": "analyst",
            "department": "Security Operations",
            "position": "SOC Analyst",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(hours=6),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}lead",
            "email": "lead@nina.example.com",
            "first_name": "Giulia",
            "last_name": "Ricci",
            "role": "admin",
            "department": "Security Operations",
            "position": "Team Lead",
            "is_active": True,
            "is_admin": True,
            "last_login": now - timedelta(days=1, hours=2),
            "login_attempts": 1,
        },
        {
            "username": f"{USER_PREFIX}auditor",
            "email": "auditor@nina.example.com",
            "first_name": "Luca",
            "last_name": "Serra",
            "role": "auditor",
            "department": "Compliance",
            "position": "Compliance Auditor",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(days=3),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}viewer",
            "email": "viewer@nina.example.com",
            "first_name": "Elena",
            "last_name": "Costa",
            "role": "viewer",
            "department": "Clinical Support",
            "position": "Supervisor",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(hours=12),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}locked",
            "email": "locked@nina.example.com",
            "first_name": "Marco",
            "last_name": "De Luca",
            "role": "viewer",
            "department": "Security Operations",
            "position": "Analyst",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(days=5),
            "login_attempts": 5,
            "locked_until": now + timedelta(hours=6),
        },
    ]


def build_conversations(now: datetime) -> List[Dict[str, Any]]:
    """Create conversation sessions with different risk/status combinations."""
    return [
        {
            "id": f"{CONV_PREFIX}001",
            "patient_id": "analytics_patient_001",
            "session_start": now - timedelta(days=3, hours=4),
            "session_end": now - timedelta(days=3, hours=3, minutes=10),
            "session_duration_minutes": 70,
            "status": "COMPLETED",
            "total_messages": 42,
            "guardrail_violations": 2,
            "patient_info": {
                "name": "Giovanni Rossi",
                "age": 46,
                "gender": "M",
                "pathology": "Depressione",
            },
            "risk_level": "MEDIUM",
            "situation": "Timore di ricaduta",
            "requires_attention": True,
            "escalated": False,
            "sentiment_score": 0.35,
            "engagement_score": 0.72,
            "satisfaction_score": 0.58,
        },
        {
            "id": f"{CONV_PREFIX}002",
            "patient_id": "analytics_patient_002",
            "session_start": now - timedelta(days=1, hours=6),
            "session_end": now - timedelta(days=1, hours=5, minutes=15),
            "session_duration_minutes": 45,
            "status": "COMPLETED",
            "total_messages": 28,
            "guardrail_violations": 1,
            "patient_info": {
                "name": "Sara Bianchi",
                "age": 29,
                "gender": "F",
                "pathology": "Ansia sociale",
            },
            "risk_level": "LOW",
            "situation": "Difficoltà lavorative",
            "requires_attention": False,
            "escalated": False,
            "sentiment_score": 0.62,
            "engagement_score": 0.81,
            "satisfaction_score": 0.88,
        },
        {
            "id": f"{CONV_PREFIX}003",
            "patient_id": "analytics_patient_003",
            "session_start": now - timedelta(hours=5),
            "session_end": None,
            "session_duration_minutes": None,
            "status": "ACTIVE",
            "total_messages": 19,
            "guardrail_violations": 3,
            "patient_info": {
                "name": "Alessandro Conti",
                "age": 38,
                "gender": "M",
                "pathology": "Disturbo bipolare",
            },
            "risk_level": "HIGH",
            "situation": "Confusione emotiva",
            "requires_attention": True,
            "escalated": True,
            "sentiment_score": 0.28,
            "engagement_score": 0.54,
            "satisfaction_score": 0.41,
        },
        {
            "id": f"{CONV_PREFIX}004",
            "patient_id": "analytics_patient_004",
            "session_start": now - timedelta(days=7, hours=9),
            "session_end": now - timedelta(days=7, hours=8, minutes=20),
            "session_duration_minutes": 40,
            "status": "COMPLETED",
            "total_messages": 24,
            "guardrail_violations": 0,
            "patient_info": {
                "name": "Marta Ferri",
                "age": 53,
                "gender": "F",
                "pathology": "Dipendenza da farmaci",
            },
            "risk_level": "MEDIUM",
            "situation": "Gestione farmaci",
            "requires_attention": False,
            "escalated": False,
            "sentiment_score": 0.48,
            "engagement_score": 0.66,
            "satisfaction_score": 0.73,
        },
    ]


def build_guardrail_events(now: datetime) -> List[Dict[str, Any]]:
    """Return guardrail events with varying severities/statuses."""
    base_events = []
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    statuses = ["PENDING", "ACKNOWLEDGED", "RESOLVED", "ESCALATED"]
    event_types = [
        ("self_harm", "CRITICAL"),
        ("violence", "HIGH"),
        ("inappropriate_content", "MEDIUM"),
        ("policy_violation", "LOW"),
    ]

    # Generate events over the last 14 days
    for day in range(14):
        event_time = now - timedelta(days=day, hours=2)
        conv_id = f"{CONV_PREFIX}{(day % 4) + 1:03d}"
        event_type, default_severity = event_types[day % len(event_types)]
        severity = severities[day % len(severities)]
        status = statuses[day % len(statuses)]

        event_id = f"{EVENT_PREFIX}{day:03d}"
        base_events.append(
            {
                "event_id": event_id,
                "conversation_id": conv_id,
                "event_type": event_type,
                "severity": severity,
                "category": "alert",
                "title": f"{event_type.replace('_', ' ').title()} rilevato",
                "description": "Evento generato per test della dashboard analitica.",
                "message_content": "Messaggio di esempio che ha attivato la guardrail.",
                "detected_text": "Testo sensibile simulato.",
                "confidence_score": 0.65 + (day % 4) * 0.07,
                "detection_method": "ai_model",
                "status": status,
                "priority": "HIGH" if severity in ["CRITICAL", "HIGH"] else "NORMAL",
                "created_at": event_time,
                "updated_at": event_time + timedelta(minutes=5),
                "acknowledged_at": (
                    event_time + timedelta(minutes=12)
                    if status in ["ACKNOWLEDGED", "RESOLVED", "ESCALATED"]
                    else None
                ),
                "resolved_at": (
                    event_time + timedelta(minutes=40) if status == "RESOLVED" else None
                ),
                "acknowledged_by": f"{USER_PREFIX}lead",
                "resolved_by": f"{USER_PREFIX}analyst" if status in ["RESOLVED", "ESCALATED"] else None,
                "response_time_minutes": 12 if status in ["ACKNOWLEDGED", "RESOLVED", "ESCALATED"] else None,
                "action_taken": "escalated" if status == "ESCALATED" else "reviewed",
                "action_notes": "Nota di esempio sull'azione intrapresa.",
            }
        )

    # Add targeted SLA sample events so every severity has acknowledged data
    sla_samples = [
        ("CRITICAL", "self_harm", "RESOLVED", 6),
        ("HIGH", "violence", "ACKNOWLEDGED", 9),
        ("MEDIUM", "policy_violation", "ACKNOWLEDGED", 18),
        ("LOW", "inappropriate_content", "RESOLVED", 24),
    ]

    for index, (severity, event_type, status, actual_minutes) in enumerate(sla_samples):
        event_time = now - timedelta(hours=index + 1, minutes=30)
        conv_id = f"{CONV_PREFIX}{(index % 4) + 1:03d}"
        event_id = f"{EVENT_PREFIX}sla_{index:02d}"
        base_events.append(
            {
                "event_id": event_id,
                "conversation_id": conv_id,
                "event_type": event_type,
                "severity": severity,
                "category": "alert",
                "title": f"SLA sample {event_type}",
                "description": "Evento aggiuntivo per dati SLA.",
                "message_content": "Messaggio SLA di esempio.",
                "detected_text": "Testo SLA simulato.",
                "confidence_score": 0.82,
                "detection_method": "ai_model",
                "status": status,
                "priority": "HIGH" if severity in ["CRITICAL", "HIGH"] else "NORMAL",
                "created_at": event_time,
                "updated_at": event_time + timedelta(minutes=4),
                "acknowledged_at": event_time + timedelta(minutes=actual_minutes),
                "resolved_at": (
                    event_time + timedelta(minutes=actual_minutes + 15)
                    if status == "RESOLVED"
                    else None
                ),
                "acknowledged_by": f"{USER_PREFIX}lead",
                "resolved_by": f"{USER_PREFIX}analyst" if status == "RESOLVED" else None,
                "response_time_minutes": actual_minutes,
                "action_taken": "reviewed",
                "action_notes": "Campione SLA generato dalla seed.",
            }
        )

    # Additional escalation-focused events for richer analytics
    escalation_samples = [
        ("medication_non_compliance", "MEDIUM"),
        ("imminent_harm", "CRITICAL"),
        ("care_team_request", "HIGH"),
    ]

    for idx, (event_type, severity) in enumerate(escalation_samples):
        event_time = now - timedelta(hours=idx + 6)
        conv_id = f"{CONV_PREFIX}{((idx + 1) % 4) + 1:03d}"
        event_id = f"{EVENT_PREFIX}esc_{idx:02d}"
        base_events.append(
            {
                "event_id": event_id,
                "conversation_id": conv_id,
                "event_type": event_type,
                "severity": severity,
                "category": "alert",
                "title": f"Escalation {event_type.replace('_', ' ').title()}",
                "description": "Evento di escalation sintetico.",
                "message_content": "Messaggio che ha richiesto escalation.",
                "detected_text": "Dettaglio escalation di esempio.",
                "confidence_score": 0.9,
                "detection_method": "manual_review",
                "status": "ESCALATED",
                "priority": "HIGH",
                "created_at": event_time,
                "updated_at": event_time + timedelta(minutes=5),
                "acknowledged_at": event_time + timedelta(minutes=8),
                "resolved_at": None,
                "acknowledged_by": f"{USER_PREFIX}lead",
                "resolved_by": f"{USER_PREFIX}analyst",
                "response_time_minutes": 8,
                "action_taken": "escalated",
                "action_notes": "Escalation simulata per analytics.",
            }
        )

    return base_events


def seed():
    now = tz_now()
    users = build_users(now)
    conversations = build_conversations(now)
    events = build_guardrail_events(now)

    with get_session_context() as session:
        wipe_existing(session)

        # Seed users
        for user_data in users:
            password = user_data.pop("password", "P@ssw0rd!")
            user = User(**{k: v for k, v in user_data.items() if k not in {"locked_until"}})
            user.set_password(password)
            if "locked_until" in user_data:
                user.locked_until = user_data["locked_until"]
            session.add(user)

        # Seed conversation sessions
        for conv_data in conversations:
            session.add(ConversationSession(**conv_data))

        session.flush()

        # Seed guardrail events
        for event_data in events:
            created_at = event_data.pop("created_at")
            updated_at = event_data.pop("updated_at")
            acknowledged_at = event_data.pop("acknowledged_at", None)
            resolved_at = event_data.pop("resolved_at", None)

            event = GuardrailEvent(**event_data)
            event.created_at = created_at
            event.updated_at = updated_at
            event.reviewed_at = acknowledged_at or updated_at
            event.acknowledged_at = acknowledged_at
            event.resolved_at = resolved_at
            session.add(event)

        session.flush()

        print(f"✅ Seeded {len(users)} analytics users.")
        print(f"✅ Seeded {len(conversations)} analytics conversation sessions.")
        print(f"✅ Seeded {len(events)} guardrail events for analytics testing.")
        print("Analytics data ready. Refresh the dashboard to load new metrics.")


if __name__ == "__main__":
    seed()



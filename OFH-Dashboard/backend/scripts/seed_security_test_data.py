#!/usr/bin/env python3
"""
Seed data for the security dashboards.

This script enriches the database with synthetic users, conversation sessions,
and guardrail events tailored to exercise the security tabs (overview, threats,
access, compliance, incidents).

Usage:
    cd OFH-Dashboard/backend
    python scripts/seed_security_test_data.py

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
from models import User, ConversationSession, GuardrailEvent, OperatorAction

USER_PREFIX = "security_seed_user_"
CONV_PREFIX = "security_seed_conv_"
EVENT_PREFIX = "security_seed_event_"


def tz_now() -> datetime:
    return datetime.now(timezone.utc)


def wipe_existing(session) -> None:
    """Remove previous security seed data so the script is idempotent."""
    session.query(OperatorAction).filter(
        OperatorAction.conversation_id.like(f"{CONV_PREFIX}%")
    ).delete(synchronize_session=False)

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
    """Return synthetic user records for security analytics."""
    return [
        {
            "username": f"{USER_PREFIX}admin",
            "email": "security.admin@nina.example.com",
            "first_name": "Chiara",
            "last_name": "Lombardi",
            "role": "admin",
            "department": "Security Operations",
            "position": "Head of Security",
            "is_active": True,
            "is_admin": True,
            "last_login": now - timedelta(hours=2),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}admin_alt",
            "email": "security.admin.alt@nina.example.com",
            "first_name": "Paolo",
            "last_name": "Venturi",
            "role": "admin",
            "department": "Security Operations",
            "position": "Security Manager",
            "is_active": True,
            "is_admin": True,
            "last_login": now - timedelta(hours=30),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}admin_past",
            "email": "security.admin.past@nina.example.com",
            "first_name": "Marta",
            "last_name": "Basile",
            "role": "admin",
            "department": "Security Operations",
            "position": "Regional Admin",
            "is_active": True,
            "is_admin": True,
            "last_login": now - timedelta(days=3, hours=6),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}analyst",
            "email": "security.analyst@nina.example.com",
            "first_name": "Davide",
            "last_name": "Ferraro",
            "role": "analyst",
            "department": "Security Operations",
            "position": "SOC Analyst",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(hours=8),
            "login_attempts": 1,
        },
        {
            "username": f"{USER_PREFIX}auditor",
            "email": "security.auditor@nina.example.com",
            "first_name": "Francesca",
            "last_name": "Pini",
            "role": "auditor",
            "department": "Compliance",
            "position": "Security Auditor",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(days=1, hours=5),
            "login_attempts": 0,
        },
        {
            "username": f"{USER_PREFIX}locked",
            "email": "locked.account@nina.example.com",
            "first_name": "Stefano",
            "last_name": "Moretti",
            "role": "viewer",
            "department": "Security Operations",
            "position": "Incident Responder",
            "is_active": True,
            "is_admin": False,
            "last_login": now - timedelta(days=3),
            "login_attempts": 6,
            "locked_until": now + timedelta(hours=4),
        },
    ]


def build_conversations(now: datetime) -> List[Dict[str, Any]]:
    """Create conversation sessions referenced by guardrail events."""
    return [
        {
            "id": f"{CONV_PREFIX}001",
            "patient_id": "security_patient_001",
            "session_start": now - timedelta(days=1, hours=3),
            "session_end": now - timedelta(days=1, hours=2, minutes=5),
            "session_duration_minutes": 55,
            "status": "COMPLETED",
            "total_messages": 38,
            "guardrail_violations": 2,
            "risk_level": "HIGH",
            "situation": "Escalation after sensitive disclosure",
            "requires_attention": True,
        },
        {
            "id": f"{CONV_PREFIX}002",
            "patient_id": "security_patient_002",
            "session_start": now - timedelta(hours=10),
            "session_end": now - timedelta(hours=9, minutes=15),
            "session_duration_minutes": 45,
            "status": "COMPLETED",
            "total_messages": 24,
            "guardrail_violations": 1,
            "risk_level": "MEDIUM",
            "situation": "Medication adherence follow-up",
            "requires_attention": False,
        },
        {
            "id": f"{CONV_PREFIX}003",
            "patient_id": "security_patient_003",
            "session_start": now - timedelta(hours=4),
            "session_end": None,
            "session_duration_minutes": None,
            "status": "ACTIVE",
            "total_messages": 19,
            "guardrail_violations": 3,
            "risk_level": "CRITICAL",
            "situation": "Self-harm risk escalation",
            "requires_attention": True,
        },
    ]


def build_guardrail_events(now: datetime) -> List[Dict[str, Any]]:
    """Return guardrail events with varying severities/statuses."""
    base_time = now
    events: List[Dict[str, Any]] = []

    samples = [
        {
            "suffix": "crit_pending",
            "conversation": f"{CONV_PREFIX}003",
            "severity": "CRITICAL",
            "event_type": "imminent_harm",
            "status": "PENDING",
            "minutes_since": 90,
            "ack_minutes": None,
            "resolve_minutes": None,
            "action_taken": "monitoring",
            "action_notes": "Escalated to duty supervisor for immediate call.",
            "priority": "HIGH",
            "confidence": 0.94,
        },
        {
            "suffix": "high_ack",
            "conversation": f"{CONV_PREFIX}001",
            "severity": "HIGH",
            "event_type": "violence",
            "status": "ACKNOWLEDGED",
            "minutes_since": 360,
            "ack_minutes": 22,
            "resolve_minutes": None,
            "action_taken": "acknowledged",
            "action_notes": "Investigation in progress by on-call team.",
            "priority": "HIGH",
            "confidence": 0.88,
            "assigned_to": f"{USER_PREFIX}analyst",
        },
        {
            "suffix": "medium_resolved",
            "conversation": f"{CONV_PREFIX}002",
            "severity": "MEDIUM",
            "event_type": "inappropriate_content",
            "status": "RESOLVED",
            "minutes_since": 1440,
            "ack_minutes": 18,
            "resolve_minutes": 42,
            "action_taken": "sanitized",
            "action_notes": "Content flagged and moderator response recorded.",
            "priority": "NORMAL",
            "confidence": 0.76,
        },
        {
            "suffix": "data_privacy",
            "conversation": f"{CONV_PREFIX}001",
            "severity": "HIGH",
            "event_type": "data_privacy",
            "status": "RESOLVED",
            "minutes_since": 72 * 60,
            "ack_minutes": 35,
            "resolve_minutes": 120,
            "action_taken": "reported",
            "action_notes": "Privacy officer notified; no exposure detected.",
            "priority": "HIGH",
            "confidence": 0.81,
        },
        {
            "suffix": "hipaa_violation",
            "conversation": f"{CONV_PREFIX}002",
            "severity": "HIGH",
            "event_type": "hipaa_violation",
            "status": "ESCALATED",
            "minutes_since": 6 * 60,
            "ack_minutes": 15,
            "resolve_minutes": None,
            "action_taken": "escalated",
            "action_notes": "Compliance review required for PHI disclosure.",
            "priority": "HIGH",
            "confidence": 0.9,
        },
        {
            "suffix": "unauthorized_access",
            "conversation": f"{CONV_PREFIX}003",
            "severity": "MEDIUM",
            "event_type": "unauthorized_access",
            "status": "ACKNOWLEDGED",
            "minutes_since": 18 * 60,
            "ack_minutes": 25,
            "resolve_minutes": None,
            "action_taken": "account_locked",
            "action_notes": "Temporary lock enforced after suspicious access pattern.",
            "priority": "NORMAL",
            "confidence": 0.83,
        },
        {
            "suffix": "false_positive",
            "conversation": f"{CONV_PREFIX}002",
            "severity": "LOW",
            "event_type": "policy_violation",
            "status": "RESOLVED",
            "minutes_since": 12 * 60,
            "ack_minutes": 10,
            "resolve_minutes": 30,
            "action_taken": "dismissed",
            "action_notes": "Flag classified as false positive after review.",
            "priority": "LOW",
            "confidence": 0.52,
            "false_positive": True,
        },
    ]

    # Additional threat categories to feed distribution chart
    threat_clusters = [
        {
            "type": "malware_detection",
            "severity": "HIGH",
            "status": "RESOLVED",
            "count": 4,
            "base_minutes": 8 * 60,
            "ack_minutes": 20,
            "resolve_minutes": 45,
            "action": "quarantined",
            "notes": "Malware payload quarantined and endpoint isolated.",
            "priority": "HIGH",
            "confidence": 0.92,
        },
        {
            "type": "phishing_attempt",
            "severity": "MEDIUM",
            "status": "ACKNOWLEDGED",
            "count": 3,
            "base_minutes": 6 * 60,
            "ack_minutes": 18,
            "resolve_minutes": None,
            "action": "blocked_sender",
            "notes": "Sender blocked and recipients notified.",
            "priority": "NORMAL",
            "confidence": 0.78,
        },
        {
            "type": "brute_force_attempt",
            "severity": "MEDIUM",
            "status": "ESCALATED",
            "count": 2,
            "base_minutes": 3 * 60,
            "ack_minutes": 12,
            "resolve_minutes": None,
            "action": "ip_blacklisted",
            "notes": "Repeated login failures detected from same subnet.",
            "priority": "HIGH",
            "confidence": 0.84,
        },
        {
            "type": "data_exfiltration",
            "severity": "HIGH",
            "status": "RESOLVED",
            "count": 2,
            "base_minutes": 15 * 60,
            "ack_minutes": 25,
            "resolve_minutes": 60,
            "action": "session_terminated",
            "notes": "Outbound transfer halted, credentials rotated.",
            "priority": "CRITICAL",
            "confidence": 0.9,
        },
        {
            "type": "insider_threat",
            "severity": "HIGH",
            "status": "ACKNOWLEDGED",
            "count": 1,
            "base_minutes": 9 * 60,
            "ack_minutes": 30,
            "resolve_minutes": None,
            "action": "investigation_opened",
            "notes": "Unusual access pattern flagged for review.",
            "priority": "HIGH",
            "confidence": 0.87,
        },
    ]

    for cluster in threat_clusters:
        for index in range(cluster["count"]):
            samples.append(
                {
                    "suffix": f"{cluster['type']}_{index + 1}",
                    "conversation": f"{CONV_PREFIX}{(index % 3) + 1:03d}",
                    "severity": cluster["severity"],
                    "event_type": cluster["type"],
                    "status": cluster["status"],
                    "minutes_since": cluster["base_minutes"] + (index * 35),
                    "ack_minutes": cluster["ack_minutes"],
                    "resolve_minutes": cluster["resolve_minutes"],
                    "action_taken": cluster["action"],
                    "action_notes": cluster["notes"],
                    "priority": cluster["priority"],
                    "confidence": cluster["confidence"],
                }
            )

    for entry in samples:
        created_at = base_time - timedelta(minutes=entry["minutes_since"])
        acknowledged_at = None
        resolved_at = None

        if entry["ack_minutes"] is not None:
            acknowledged_at = created_at + timedelta(minutes=entry["ack_minutes"])

        if entry["resolve_minutes"] is not None:
            resolved_at = created_at + timedelta(minutes=entry["resolve_minutes"])

        event = {
            "event_id": f"{EVENT_PREFIX}{entry['suffix']}",
            "conversation_id": entry["conversation"],
            "event_type": entry["event_type"],
            "severity": entry["severity"],
            "category": "alert",
            "title": f"{entry['event_type'].replace('_', ' ').title()} detected",
            "description": "Evento generato per test della dashboard di sicurezza.",
            "message_content": "Messaggio di esempio che ha attivato la guardrail.",
            "detected_text": "Contenuto sensibile simulato.",
            "confidence_score": entry["confidence"],
            "detection_method": "ai_model",
            "status": entry["status"],
            "priority": entry["priority"],
            "created_at": created_at,
            "updated_at": created_at + timedelta(minutes=5),
            "acknowledged_at": acknowledged_at,
            "resolved_at": resolved_at,
            "acknowledged_by": entry.get("assigned_to", f"{USER_PREFIX}analyst"),
            "resolved_by": f"{USER_PREFIX}admin" if resolved_at else None,
            "response_time_minutes": entry["ack_minutes"],
            "action_taken": entry["action_taken"],
            "action_notes": entry["action_notes"],
            "is_false_positive": entry.get("false_positive", False),
        }

        events.append(event)

    return events


def record_admin_activity(session, now: datetime):
    """Simulate admin logins in the past few days for trend visualization."""
    admin_users = session.query(User).filter(
        User.username.like(f"{USER_PREFIX}admin%")
    ).all()

    offsets = [2, 12, 18, 30, 48, 72, 90]  # hours ago
    for user in admin_users:
        for offset in offsets:
            user.last_login = now - timedelta(hours=offset)
        user.last_login = now - timedelta(hours=offsets[0])


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

        session.flush()

        record_admin_activity(session, now)

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

        print(f"✅ Seeded {len(users)} security users.")
        print(f"✅ Seeded {len(conversations)} security conversation sessions.")
        print(f"✅ Seeded {len(events)} guardrail events for security testing.")
        print("Security data ready. Refresh the security dashboard to load new metrics.")


if __name__ == "__main__":
    seed()



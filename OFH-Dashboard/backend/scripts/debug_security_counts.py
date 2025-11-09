#!/usr/bin/env python3
"""Quick diagnostic script for security seed data."""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

# Ensure backend package is importable when executed directly
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_session_context
from models.guardrail_event import GuardrailEvent
from models.user import User
from models.conversation import ConversationSession


def dump_security_snapshot(hours: int = 168):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    with get_session_context() as session:
        total_events = session.query(GuardrailEvent).count()
        recent_events = (
            session.query(GuardrailEvent)
            .filter(GuardrailEvent.created_at >= cutoff)
            .count()
        )

        total_users = session.query(User).count()
        recent_logins = (
            session.query(User)
            .filter(User.last_login.isnot(None), User.last_login >= cutoff)
            .count()
        )

        total_conversations = session.query(ConversationSession).count()
        active_conversations = (
            session.query(ConversationSession)
            .filter(ConversationSession.status == "ACTIVE")
            .count()
        )

        print("=== Security Data Snapshot ===")
        print(f"Guardrail events total: {total_events}")
        print(f"Guardrail events last {hours}h: {recent_events}")
        print(f"Users total: {total_users}")
        print(f"Users logged in last {hours}h: {recent_logins}")
        print(f"Conversation sessions total: {total_conversations}")
        print(f"Active conversation sessions: {active_conversations}")
        print("\nMost recent guardrail events:")
        events = (
            session.query(GuardrailEvent)
            .order_by(GuardrailEvent.created_at.desc())
            .limit(5)
            .all()
        )
        for ev in events:
            print(
                f"- {ev.event_id}: {ev.severity} {ev.status} at {ev.created_at} "
                f"(type={ev.event_type})"
            )


if __name__ == "__main__":
    dump_security_snapshot()



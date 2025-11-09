#!/usr/bin/env python3
"""
End-to-end integration smoke check.

This script exercises the full monitoring pipeline:
 1. Emits a guardrail event into Kafka.
 2. Waits until the dashboard persists it in Postgres.
 3. Emits an operator action (and accompanying control command).
 4. Optionally confirms the guardrail strategy ingested feedback.

Prerequisites:
  - Kafka broker reachable via KAFKA_BOOTSTRAP_SERVERS (or .env defaults)
  - Dashboard backend running with access to the database
  - Guardrail Strategy service running (optional but recommended)
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

REPO_ROOT = BACKEND_ROOT.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.database import get_session_context  # type: ignore  # noqa: E402
from models.guardrail_event import GuardrailEvent  # type: ignore  # noqa: E402
from services.infrastructure.kafka.kafka_producer import (  # type: ignore  # noqa: E402
    NINAKafkaProducerV2,
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("integration_check")


def wait_for_guardrail_event(conversation_id: str, timeout_seconds: int = 30) -> Optional[dict]:
    """Poll the dashboard database until the guardrail event appears.

    Returns a lightweight dict of fields copied while the SQLAlchemy session
    is alive so the caller can safely access them outside the context.
    """
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with get_session_context() as session:
            record = session.query(GuardrailEvent).filter(GuardrailEvent.conversation_id == conversation_id).first()
            if record:
                return {
                    "id": record.id,
                    "severity": record.severity,
                    "event_type": record.event_type,
                    "created_at": record.created_at,
                }
        time.sleep(1)
    return None


def check_guardrail_service(conversation_id: str) -> Optional[dict]:
    """Optional verification that the guardrail strategy reports feedback metrics."""
    base_url = os.getenv("GUARDRAIL_SERVICE_URL", "http://localhost:5001")
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/analytics/performance", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        summary = data.get("data", {}).get("recent_feedback", {})
        if summary:
            LOGGER.info("Guardrail service feedback summary: %s", summary)
        return data
    except Exception as exc:
        LOGGER.warning("Guardrail service verification skipped/failed: %s", exc)
        return None


def main() -> None:
    conversation_id = f"integration_{uuid.uuid4().hex[:12]}"
    LOGGER.info("Starting integration flow for conversation %s", conversation_id)

    producer = NINAKafkaProducerV2()
    producer.connect()

    event_payload = producer.generate_guardrail_event(conversation_id)
    event_payload.update(
        {
            "event_type": "alarm_triggered",
            "severity": "high",
            "message": "Integration smoke test alarm.",
        }
    )

    if not producer.send_guardrail_event(conversation_id, event_payload):
        LOGGER.error("Failed to send guardrail event. Aborting.")
        return

    LOGGER.info("Guardrail event emitted, waiting for dashboard to persist it...")
    record = wait_for_guardrail_event(conversation_id)
    if not record:
        LOGGER.error("Guardrail event did not appear in dashboard DB within timeout.")
        return

    LOGGER.info("Guardrail event stored (id=%s, severity=%s).", record.get("id"), record.get("severity"))

    LOGGER.info("Emitting operator action for conversation %s", conversation_id)
    if not producer.send_operator_action(conversation_id, "stop_conversation"):
        LOGGER.warning("Operator action could not be sent.")

    check_guardrail_service(conversation_id)
    LOGGER.info("Integration script completed.")


if __name__ == "__main__":
    main()



    main()



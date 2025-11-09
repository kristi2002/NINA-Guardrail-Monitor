#!/usr/bin/env python3
"""
External Alerting Service Stub
==============================

This module provides a lightweight skeleton for the external alerting system:

1. Connects to a dedicated PostgreSQL database (configurable via environment)
2. Defines a simple alert table to persist incoming Kafka events
3. Runs a Kafka consumer that validates guardrail events and stores them
4. Exposes a minimal CLI-friendly `start()` helper for manual testing

The goal is to confirm that the alerting pipeline is wired end-to-end even if
the upstream agent is not yet publishing real production events.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generator, Optional

import jsonschema
from kafka import KafkaConsumer
from kafka.errors import KafkaError, KafkaTimeoutError, KafkaConnectionError
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from shared.guardrail_schemas import load_schema

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

Base = declarative_base()


class AlertRecord(Base):
    """Simple table to store guardrail alerts for the external system."""

    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False)
    conversation_id = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False)
    event_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@dataclass
class ExternalAlertingConfig:
    """Configuration block for the alerting stub."""

    kafka_bootstrap_servers: str = field(
        default_factory=lambda: os.getenv("ALERTING_KAFKA_BOOTSTRAP", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    )
    kafka_topic: str = field(default_factory=lambda: os.getenv("ALERTING_KAFKA_TOPIC", os.getenv("KAFKA_TOPIC_GUARDRAIL", "guardrail_events")))
    kafka_group_id: str = field(default_factory=lambda: os.getenv("ALERTING_KAFKA_GROUP", "external-alerting-service"))
    database_url: str = field(default_factory=lambda: os.getenv("ALERTING_DATABASE_URL", "postgresql://alert_user:alert_pass@localhost:5432/alerting_db"))
    poll_interval_seconds: float = 1.0
    schema_name: str = "guardrail_event"


class ExternalAlertingService:
    """Kafka -> Postgres ingestion stub for the external alerting system."""

    def __init__(self, config: Optional[ExternalAlertingConfig] = None):
        self.config = config or ExternalAlertingConfig()
        self._engine = create_engine(self.config.database_url, pool_pre_ping=True)
        self._session_factory = sessionmaker(bind=self._engine)
        self._consumer: Optional[KafkaConsumer] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._schema = load_schema(self.config.schema_name)

        LOGGER.info("External Alerting Service config: %s", self.config)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create database tables if they do not exist."""
        try:
            Base.metadata.create_all(self._engine)
            LOGGER.info("✅ Alerting database schema is ready.")
        except SQLAlchemyError as exc:
            LOGGER.exception("Failed to initialise alerting database schema: %s", exc)
            raise

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide transactional scope."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _build_consumer(self) -> KafkaConsumer:
        """Construct the Kafka consumer instance."""
        LOGGER.info(
            "Connecting Kafka consumer (topic=%s, group=%s, bootstrap=%s)",
            self.config.kafka_topic,
            self.config.kafka_group_id,
            self.config.kafka_bootstrap_servers,
        )
        consumer = KafkaConsumer(
            self.config.kafka_topic,
            bootstrap_servers=self.config.kafka_bootstrap_servers,
            group_id=self.config.kafka_group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        return consumer

    def _validate_event(self, payload: Dict[str, Any]) -> bool:
        """Validate payload with the shared guardrail schema."""
        try:
            jsonschema.validate(instance=payload, schema=self._schema)
            return True
        except jsonschema.ValidationError as exc:
            LOGGER.warning("Schema validation failed for incoming alert: %s", exc.message)
            return False
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Unexpected error validating alert payload: %s", exc, exc_info=True)
            return False

    def _persist_event(self, payload: Dict[str, Any]) -> None:
        """Persist the event into the alerting database."""
        record = AlertRecord(
            event_id=payload.get("event_id") or payload.get("id") or "unknown",
            conversation_id=payload.get("conversation_id", "unknown"),
            severity=str(payload.get("severity", "info")).lower(),
            event_type=payload.get("event_type", "unknown"),
            title=payload.get("message"),
            message=payload.get("message"),
            payload=payload,
            ingested_at=datetime.utcnow(),
        )

        # Capture values before the session exits to avoid DetachedInstanceError
        conversation_id = record.conversation_id
        event_id = record.event_id

        with self.session_scope() as session:
            session.add(record)

        LOGGER.info("📥 Stored alert record for conversation %s (event=%s)", conversation_id, event_id)

    def list_recent_alerts(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Return the most recent alerts for dashboard consumption."""
        with self.session_scope() as session:
            rows = (
                session.query(AlertRecord)
                .order_by(AlertRecord.ingested_at.desc())
                .limit(limit)
                .all()
            )

            alerts = []
            for row in rows:
                alerts.append(
                    {
                        "id": row.id,
                        "event_id": row.event_id,
                        "conversation_id": row.conversation_id,
                        "severity": row.severity,
                        "event_type": row.event_type,
                        "title": row.title,
                        "message": row.message,
                        "ingested_at": row.ingested_at.isoformat()
                        if row.ingested_at
                        else None,
                    }
                )
            return alerts

    def process_event(self, payload: Dict[str, Any]) -> None:
        """Validate and persist a single guardrail payload."""
        if not payload:
            LOGGER.debug("Skipping empty payload")
            return

        if not self._validate_event(payload):
            return

        try:
            self._persist_event(payload)
        except SQLAlchemyError as exc:
            LOGGER.error("Failed to persist alert payload: %s", exc, exc_info=True)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Unexpected error while persisting alert payload: %s", exc, exc_info=True)

    def _consume_forever(self) -> None:
        """Internal loop that polls Kafka and processes events."""
        assert self._consumer is not None
        LOGGER.info("External alerting consumer loop started.")
        while self._running:
            try:
                message_pack = self._consumer.poll(timeout_ms=int(self.config.poll_interval_seconds * 1000))
                if not message_pack:
                    continue

                for _, messages in message_pack.items():
                    for message in messages:
                        if not self._running:
                            break
                        payload = message.value
                        LOGGER.debug("Received alert payload: %s", payload)
                        self.process_event(payload)
            except (KafkaTimeoutError, KafkaConnectionError, KafkaError) as exc:
                LOGGER.error("Kafka error in alerting consumer: %s", exc, exc_info=True)
                time.sleep(self.config.poll_interval_seconds)
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.error("Unexpected error in alerting consumer loop: %s", exc, exc_info=True)
                time.sleep(self.config.poll_interval_seconds)

        LOGGER.info("External alerting consumer loop stopped.")

    def start(self, background: bool = True) -> None:
        """Start the Kafka consumer."""
        if self._running:
            LOGGER.info("Alerting service already running.")
            return

        self._consumer = self._build_consumer()
        self._running = True

        if background:
            self._thread = threading.Thread(target=self._consume_forever, daemon=True)
            self._thread.start()
            LOGGER.info("External alerting service started in background thread.")
        else:
            self._consume_forever()

    def stop(self) -> None:
        """Stop the Kafka consumer and clean up resources."""
        if not self._running:
            return

        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        if self._consumer:
            self._consumer.close()
            self._consumer = None
        LOGGER.info("External alerting service stopped.")

    def ingest_mock_event(self) -> None:
        """Persist a simple mock alert for smoke testing without Kafka."""
        mock_payload = {
            "event_id": f"mock-{int(time.time())}",
            "conversation_id": "mock_conversation",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "mock_event",
            "severity": "info",
            "message": "Mock alert event for external alerting pipeline.",
        }
        if self._validate_event(mock_payload):
            self._persist_event(mock_payload)


def main() -> None:
    """Allow running the stub as a standalone process from the command line."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    service = ExternalAlertingService()

    def handle_signal(signum, frame):  # pragma: no cover - CLI helper
        LOGGER.info("Received signal %s, stopping alerting service…", signum)
        service.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_signal)

    service.start(background=True)
    LOGGER.info("External alerting service is running. Press Ctrl+C to stop.")

    # Keep the main thread alive
    try:
        while service._running:
            time.sleep(1)
    finally:
        service.stop()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()



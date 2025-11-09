#!/usr/bin/env python3
"""
Smoke-test helper for the Guardrail Strategy service.

It performs a single /validate call with a payload that should trigger a guardrail
violation (to ensure an event is emitted) and then listens on Kafka to confirm the
event was published on the configured output topic.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from typing import Optional

import requests
from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.errors import KafkaError

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DEFAULT_TIMEOUT = 30  # seconds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test the Guardrail Strategy validation pipeline."
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Guardrail Strategy base URL (default derived from PORT env).",
    )
    parser.add_argument(
        "--bootstrap-servers",
        default=None,
        help="Kafka bootstrap servers (default from KAFKA_BOOTSTRAP_SERVERS).",
    )
    parser.add_argument(
        "--output-topic",
        default=None,
        help="Kafka topic where guardrail events are published (default from KAFKA_OUTPUT_TOPIC).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to wait for Kafka event (default {DEFAULT_TIMEOUT}).",
    )
    return parser.parse_args()


def load_configuration(args: argparse.Namespace) -> dict:
    load_dotenv()

    port = os.getenv("PORT", "5001")
    config = {
        "base_url": args.base_url or f"http://localhost:{port}",
        "bootstrap_servers": args.bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "output_topic": args.output_topic or os.getenv("KAFKA_OUTPUT_TOPIC", "guardrail_events"),
        "timeout": args.timeout,
    }
    return config


def run_validation(base_url: str, conversation_id: str) -> requests.Response:
    payload = {
        "conversation_id": conversation_id,
        "user_id": "smoke_test_operator",
        "message": "I am going to kill everyone in this hospital right now.",
        "conversation_history": [
            {
                "role": "user",
                "content": "How are you feeling today?"
            },
            {
                "role": "assistant",
                "content": "I'm here to help."
            }
        ],
    }

    url = f"{base_url.rstrip('/')}/validate"
    response = requests.post(url, json=payload, timeout=10)
    return response


def wait_for_kafka_event(
    bootstrap_servers: str,
    topic: str,
    conversation_id: str,
    timeout: int,
) -> Optional[dict]:
    group_id = f"guardrail-smoke-{uuid.uuid4().hex[:8]}"
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="latest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    start = time.time()
    try:
        while time.time() - start < timeout:
            records = consumer.poll(timeout_ms=500)
            for _, messages in records.items():
                for message in messages:
                    value = message.value
                    if not isinstance(value, dict):
                        continue
                    if value.get("conversation_id") == conversation_id:
                        return value
        return None
    finally:
        consumer.close()


def main() -> int:
    args = parse_args()
    config = load_configuration(args)

    print("=== Guardrail Strategy Smoke Test ===")
    print(f"Base URL:           {config['base_url']}")
    print(f"Kafka brokers:      {config['bootstrap_servers']}")
    print(f"Kafka output topic: {config['output_topic']}")
    print("")

    conversation_id = f"smoke_{uuid.uuid4().hex[:8]}"

    try:
        response = run_validation(config["base_url"], conversation_id)
    except requests.RequestException as exc:
        print(f"❌ HTTP request to /validate failed: {exc}")
        return 1

    if response.status_code != 200:
        print(f"❌ /validate returned {response.status_code}: {response.text}")
        return 1

    payload = response.json()
    valid = payload.get("validation_results", {}).get("valid")
    kafka_flag = payload.get("event", {}).get("kafka_sent")

    print(f"✔ /validate responded with valid={valid}, kafka_sent={kafka_flag}")

    if valid is True or kafka_flag is not True:
        print("⚠️ The message did not trigger a guardrail violation; Kafka event may not be emitted.")

    try:
        event = wait_for_kafka_event(
            config["bootstrap_servers"],
            config["output_topic"],
            conversation_id,
            config["timeout"],
        )
    except KafkaError as exc:
        print(f"❌ Kafka consumer error: {exc}")
        return 1

    if event:
        print("✅ Guardrail event received from Kafka:")
        print(json.dumps(event, indent=2))
        return 0

    print(f"❌ No guardrail event received within {config['timeout']}s.")
    return 2


if __name__ == "__main__":
    sys.exit(main())



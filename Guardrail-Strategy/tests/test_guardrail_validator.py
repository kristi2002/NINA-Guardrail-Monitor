import sys
from pathlib import Path

import pytest

# Ensure the Guardrail-Strategy package is importable when tests run from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.validation.guardrail_validator import GuardrailValidator  # noqa: E402


class _DummyGuardSuccess:
    """Stub Guardrails guard that always succeeds."""

    def __init__(self, sanitized_output: str | None = None):
        self._sanitized_output = sanitized_output

    def validate(self, message, metadata=None, **kwargs):  # noqa: D401
        sanitized_output = self._sanitized_output or message
        return type(
            "Result",
            (),
            {"validated_output": sanitized_output, "error_message": None},
        )()


class _DummyGuardFailure:
    """Stub Guardrails guard that always fails with the provided error message."""

    def __init__(self, error_message: str = "validation failed"):
        self._error_message = error_message

    def validate(self, message, metadata=None, **kwargs):  # noqa: D401
        return type(
            "Result",
            (),
            {"validated_output": None, "error_message": self._error_message},
        )()


def _build_validator():
    """Create a GuardrailValidator suitable for unit testing."""
    validator = GuardrailValidator()
    validator.enable_llm_context_check = False  # Avoid OpenAI calls during tests
    return validator


def test_validate_passes_with_successful_guard(monkeypatch):
    validator = _build_validator()
    validator.guard = _DummyGuardSuccess()
    validator.enable_compliance_check = False

    result = validator.validate("Normal conversation text", conversation_id="conv-test")

    assert result["valid"] is True
    assert result["violations"] == []
    assert result["message"] == "Normal conversation text"


def test_validate_returns_violation_when_guard_fails():
    validator = _build_validator()
    validator.guard = _DummyGuardFailure("Toxic content detected")
    validator.enable_compliance_check = False

    result = validator.validate("Some message", conversation_id="conv-fail")

    assert result["valid"] is False
    assert any(v["type"] == "validation_failed" for v in result["violations"])
    assert "Toxic content detected" in result["violations"][0]["details"]["error_message"]


def test_validate_returns_system_error_when_guard_missing():
    validator = _build_validator()
    validator.guard = None

    result = validator.validate("Test message", conversation_id="conv-missing")

    assert result["valid"] is False
    assert any(v["type"] == "system_error" for v in result["violations"])


def test_validate_detects_compliance_violation_and_sends_kafka_event(monkeypatch):
    events = []

    class DummyProducer:
        def __init__(self):
            self.producer = object()

        def send_guardrail_event(self, conversation_id, event):
            events.append((conversation_id, event))
            return True

    producer = DummyProducer()

    from services.validation import guardrail_validator

    monkeypatch.setattr(guardrail_validator, "get_kafka_producer", lambda: producer)

    validator = _build_validator()
    validator.guard = _DummyGuardSuccess()
    validator.enable_compliance_check = True

    message = "You should take this treatment immediately."
    result = validator.validate(message, conversation_id="conv-compliance", user_id="user-1")

    assert result["valid"] is False
    assert any(v["type"] == "medical_advice" for v in result["violations"])
    assert len(events) == 1
    sent_conversation_id, event = events[0]
    assert sent_conversation_id == "conv-compliance"
    assert event["event_type"] == "compliance_check"
    assert event["context"].startswith("You should take this treatment")


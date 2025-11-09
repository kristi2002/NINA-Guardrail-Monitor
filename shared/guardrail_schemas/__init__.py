#!/usr/bin/env python3
"""
Shared guardrail schema loader for the NINA ecosystem.

Centralises access to the JSON schemas used by both the guardrail
strategy service and the monitoring dashboard so that they always
validate against the same contract.
"""

from __future__ import annotations

import json
from functools import lru_cache
from dataclasses import dataclass, field
from importlib import resources
from typing import Any, Dict, List, Optional


SCHEMA_PACKAGE = __name__ + ".schemas"


@lru_cache(maxsize=None)
def load_schema(schema_name: str) -> Dict:
    """
    Load a JSON schema included in the shared package.

    Args:
        schema_name: name of the schema file without the .schema.json suffix

    Returns:
        dict representing the JSON schema

    Raises:
        FileNotFoundError: if the schema file is not found
        json.JSONDecodeError: if the schema file cannot be parsed
    """
    schema_filename = f"{schema_name}.schema.json"
    schema_path = resources.files(SCHEMA_PACKAGE).joinpath(schema_filename)

    if not schema_path.is_file():
        raise FileNotFoundError(
            f"Schema '{schema_name}' not found in shared.guardrail_schemas"
        )

    with schema_path.open("r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def available_schemas() -> List[str]:
    """Return the list of available schema names."""
    return sorted(
        path.stem
        for path in resources.files(SCHEMA_PACKAGE).iterdir()
        if path.name.endswith(".schema.json")
    )


@dataclass(frozen=True)
class GuardrailEvent:
    """Typed representation of a guardrail event."""

    conversation_id: str
    event_id: str
    timestamp: str
    event_type: str
    severity: str
    message: Optional[str] = None
    context: Optional[str] = None
    user_id: Optional[str] = None
    action_taken: Optional[str] = None
    confidence_score: Optional[float] = None
    guardrail_version: Optional[str] = None
    session_metadata: Optional[Dict[str, any]] = field(default=None)
    detection_metadata: Optional[Dict[str, any]] = field(default=None)

    def to_dict(self) -> Dict[str, any]:
        return {key: value for key, value in self.__dict__.items() if value is not None}


@dataclass(frozen=True)
class GuardrailControlFeedback:
    """Typed representation of guardrail control/feedback messages."""

    conversation_id: str
    timestamp: str
    feedback_type: str
    feedback_content: str
    feedback_source: str
    original_event_id: Optional[str] = None
    feedback_metadata: Optional[Dict[str, any]] = field(default=None)
    system_response: Optional[Dict[str, any]] = field(default=None)
    context: Optional[Dict[str, any]] = field(default=None)
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, any]:
        return {key: value for key, value in self.__dict__.items() if value is not None}


@dataclass(frozen=True)
class ConversationTranscriptMessage:
    """Envelope for transcript messages exchanged during a conversation."""

    conversation_id: str
    message_id: str
    role: str  # user, assistant, system, operator
    content: str
    timestamp: str
    sequence: Optional[int] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    message_type: str = "text"
    language: str = "it"
    metadata: Optional[Dict[str, Any]] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if value is not None}


__all__ = [
    "load_schema",
    "available_schemas",
    "GuardrailEvent",
    "GuardrailControlFeedback",
    "ConversationTranscriptMessage",
]




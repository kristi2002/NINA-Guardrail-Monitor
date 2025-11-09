#!/usr/bin/env python3
"""
Conversation Transcript Routes
Stub endpoint for ingesting transcript updates from the agent.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request  # type: ignore

from shared.guardrail_schemas import ConversationTranscriptMessage
from core.database import get_database_manager
from repositories.conversation_repository import ConversationRepository
from repositories.chat_message_repository import ChatMessageRepository
from models.conversation import ConversationSession
from models.chat_message import ChatMessage
import logging
from api.middleware.auth_middleware import token_required

logger = logging.getLogger(__name__)

transcripts_bp = Blueprint("transcripts", __name__, url_prefix="/api/transcripts")


def _parse_timestamp(timestamp: str) -> datetime:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _clean_role(role: str) -> str:
    role_map = {
        "assistant": "bot",
        "bot": "bot",
        "user": "user",
        "system": "system",
        "operator": "operator",
    }
    normalized = role.lower()
    return role_map.get(normalized, "system")


@transcripts_bp.route("", methods=["POST"])
@token_required
def ingest_transcript():
    """Ingest a single transcript message (stub implementation)."""
    payload: Optional[Dict[str, Any]] = request.get_json(silent=True)
    if not payload:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

    try:
        message = ConversationTranscriptMessage(**payload)
    except TypeError as exc:
        logger.warning("Invalid transcript payload: %s", exc)
        return jsonify({"success": False, "error": f"Invalid payload: {exc}"}), 400

    db_manager = get_database_manager()
    session = db_manager.SessionLocal()

    try:
        conversation_repo = ConversationRepository(session)
        message_repo = ChatMessageRepository(session)

        timestamp = _parse_timestamp(message.timestamp)

        conversation = conversation_repo.get_by_session_id(message.conversation_id)
        if not conversation:
            conversation = ConversationSession(
                id=message.conversation_id,
                session_start=timestamp,
                status="ACTIVE",
            )
            session.add(conversation)
            session.flush()

        existing_message = message_repo.get_by_message_id(message.message_id)
        if existing_message:
            logger.info("Transcript message %s already stored", message.message_id)
            return (
                jsonify(
                    {
                        "success": True,
                        "data": existing_message.to_dict_serialized(),
                        "message": "Message already ingested",
                    }
                ),
                200,
            )

        sequence = message.sequence
        if sequence is None:
            sequence = (conversation.total_messages or 0) + 1

        chat_message = ChatMessage(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            content=message.content,
            sender_type=_clean_role(message.role),
            sender_id=message.sender_id,
            sender_name=message.sender_name,
            timestamp=timestamp,
            sequence_number=sequence,
            message_type=message.message_type,
            language=message.language,
            message_metadata=message.metadata,
        )

        session.add(chat_message)

        conversation.total_messages = (conversation.total_messages or 0) + 1
        conversation.updated_at = datetime.now(timezone.utc)

        session.commit()

        logger.info(
            "Stored transcript message %s for conversation %s",
            message.message_id,
            message.conversation_id,
        )

        return jsonify(
            {
                "success": True,
                "data": chat_message.to_dict_serialized(),
                "conversation_id": message.conversation_id,
            }
        ), 201

    except Exception as exc:
        session.rollback()
        logger.exception("Failed to ingest transcript message: %s", exc)
        return (
            jsonify({"success": False, "error": "Failed to ingest transcript message"}),
            500,
        )
    finally:
        session.close()



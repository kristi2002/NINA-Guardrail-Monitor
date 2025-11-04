#!/usr/bin/env python3
"""
Guardrail Validators using Guardrails-AI
Uses validators from Guardrails Hub (https://github.com/guardrails-ai/guardrails)
"""

import os
import re
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from guardrails import Guard, OnFailAction  # type: ignore 
    from guardrails.hub import ToxicLanguage, DetectPII

    GUARDRAILS_AVAILABLE = True
except ImportError as e:
    GUARDRAILS_AVAILABLE = False
    logging.warning(f"Guardrails-AI library not available: {e}")
    logging.warning("Please install guardrails-ai and validators from hub:")
    logging.warning("  pip install guardrails-ai")
    logging.warning("  guardrails hub install hub://guardrails/toxic_language")
    logging.warning("  guardrails hub install hub://guardrails/detect_pii")

from kafka_handler import send_alert_to_kafka

logger = logging.getLogger(__name__)


class GuardrailValidator:
    """Validates messages against guardrails using Guardrails-AI"""

    def __init__(self):
        """Initialize guardrails-ai validators"""
        # Guardrail settings (must be set before _initialize_guard)
        self.enable_pii_detection = (
            os.getenv("GUARDRAIL_ENABLE_PII_DETECTION", "True").lower() == "true"
        )
        self.enable_toxicity_check = (
            os.getenv("GUARDRAIL_ENABLE_TOXICITY_CHECK", "True").lower() == "true"
        )
        self.enable_compliance_check = (
            os.getenv("GUARDRAIL_ENABLE_COMPLIANCE_CHECK", "True").lower() == "true"
        )

        # Compliance regex patterns (medical advice patterns)
        self.compliance_patterns = [
            (
                r"\b(take|prescribe|dosage|diagnosis|treatment)\b",
                "medical_advice",
                "medium",
            ),
            # Add more patterns here as needed
        ]

        self.guard = None
        self._initialize_guard()

    def _initialize_guard(self):
        """Initialize the Guard with validators from Guardrails Hub"""
        if not GUARDRAILS_AVAILABLE:
            logger.error("Guardrails-AI is not available. Cannot initialize guards.")
            return

        try:
            # Create a Guard
            self.guard = Guard(name="conversational-guard")

            # Add validators based on configuration
            validators_added = []

            # Add ToxicLanguage validator if enabled
            if self.enable_toxicity_check:
                try:
                    self.guard = self.guard.use(
                        ToxicLanguage(
                            threshold=0.5,
                            validation_method="sentence",
                            on_fail=send_alert_to_kafka,  # Custom Kafka handler
                        )
                    )
                    validators_added.append("ToxicLanguage")
                    logger.info("✅ ToxicLanguage validator added")
                except Exception as e:
                    logger.warning(f"Failed to add ToxicLanguage validator: {e}")
                    logger.warning(
                        "Try running: guardrails hub install hub://guardrails/toxic_language"
                    )

            # Add PII Detection validator if enabled
            if self.enable_pii_detection:
                try:
                    self.guard = self.guard.use(
                        DetectPII(
                            pii_entities=[
                                "EMAIL_ADDRESS",
                                "PHONE_NUMBER",
                                "SSN",
                                "CREDIT_CARD",
                                "IP_ADDRESS",
                            ],
                            on_fail=send_alert_to_kafka,
                        )
                    )
                    validators_added.append("DetectPII")
                    logger.info("✅ DetectPII validator added")
                except Exception as e:
                    logger.warning(f"Failed to add DetectPII validator: {e}")
                    logger.warning(
                        "Try running: guardrails hub install hub://guardrails/detect_pii"
                    )

            # Note: Compliance checks are handled manually in validate() method
            # since RegexMatch validator is not available in guardrails.hub
            if self.enable_compliance_check:
                logger.info(
                    "✅ Compliance check enabled (using custom regex validation)"
                )

            if validators_added:
                logger.info(
                    f"✅ Guard initialized with {len(validators_added)} validator(s): {validators_added}"
                )
            else:
                logger.warning(
                    "⚠️ No validators were added to the guard. Validation will not work properly."
                )

        except Exception as e:
            logger.error(f"Failed to initialize Guard: {e}", exc_info=True)
            self.guard = None

    def validate(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Validate a message against all configured guardrails

        Args:
            message: The message to validate
            conversation_id: The conversation ID
            user_id: Optional user ID
            **kwargs: Additional metadata to pass to validators

        Returns:
            Dictionary with validation results
        """
        start_time = datetime.now()
        results = {
            "valid": True,
            "violations": [],
            "response_time_ms": 0,
            "validation_timestamp": start_time.isoformat(),
        }

        logger.info(f"Validating message for conversation {conversation_id}")

        if not self.guard:
            logger.error("Guard not initialized. Cannot validate.")
            results["valid"] = False
            results["violations"].append(
                {
                    "type": "system_error",
                    "severity": "high",
                    "details": {"message": "Guard not initialized"},
                }
            )
            return results

        try:
            # Prepare metadata for validators
            user_id_str: str = (
                user_id
                or f'user_{conversation_id.split("_")[-1] if "_" in conversation_id else "unknown"}'
            )
            metadata = {
                "conversation_id": conversation_id,
                "user_id": user_id_str,
                **kwargs,
            }

            # Validate using guardrails-ai
            # This returns a ValidationOutcome object.
            # It will NOT raise an exception on failure because
            # we are using a custom on_fail handler.
            validation_outcome = self.guard.validate(
                message,
                metadata=metadata,
                **kwargs,  # Pass metadata/kwargs to the guard
            )

            # Check if validation failed by examining the ValidationOutcome object
            # The on_fail handler was already called if validation failed, so we check the result
            # Guardrails-AI ValidationOutcome may have different attributes depending on version
            validation_failed = False
            error_msg = "Validation failed"
            validated_output = None

            try:
                # Try to get validated_output
                if hasattr(validation_outcome, "validated_output"):
                    validated_output = validation_outcome.validated_output

                # Check for error_message (indicates failure)
                if hasattr(validation_outcome, "error_message") and validation_outcome.error_message:  # type: ignore
                    validation_failed = True
                    error_msg = str(validation_outcome.error_message)  # type: ignore
                # Check if validated_output contains "BLOCKED" (from on_fail handler) - check this FIRST if output exists
                elif (
                    validated_output
                    and isinstance(validated_output, str)
                    and "BLOCKED:" in validated_output
                ):
                    validation_failed = True
                    error_msg = validated_output
                # If validated_output is None or empty, likely a failure
                elif not validated_output:
                    validation_failed = True
            except AttributeError as e:
                # If we can't access attributes, assume failure for safety
                logger.warning(f"Could not determine validation outcome: {e}")
                validation_failed = True
                error_msg = f"Unable to determine validation result: {e}"

            if validation_failed:
                # Validation failed - the on_fail handler was already called
                logger.warning(f"Validation failed for {conversation_id}: {error_msg}")
                results["valid"] = False
                results["violations"].append(
                    {
                        "type": "validation_failed",
                        "severity": "medium",  # kafka_handler set the "real" severity
                        "details": {
                            "error_message": error_msg,
                            "message_preview": (
                                message[:100] + "..." if len(message) > 100 else message
                            ),
                        },
                    }
                )
            else:
                # Validation passed
                results["valid"] = True
                if validated_output:
                    results["message"] = validated_output

            # Custom regex compliance checks (run after guardrails validation)
            if self.enable_compliance_check:
                for pattern, violation_type, severity in self.compliance_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        logger.warning(
                            f"Compliance violation detected: {violation_type} in conversation {conversation_id}"
                        )
                        results["valid"] = False
                        match_text = match.group(0)
                        violation = {
                            "type": violation_type,
                            "severity": severity,
                            "details": {
                                "pattern": pattern,
                                "matched_text": match_text,
                                "message_preview": (
                                    message[:100] + "..."
                                    if len(message) > 100
                                    else message
                                ),
                            },
                        }
                        results["violations"].append(violation)

                        # Send to Kafka
                        try:
                            from kafka_handler import get_kafka_producer

                            producer = get_kafka_producer()
                            if producer and producer.producer:
                                alert_message = {
                                    "schema_version": "1.0",
                                    "event_id": str(uuid.uuid4()),
                                    "conversation_id": conversation_id,
                                    "timestamp": datetime.now().isoformat(),
                                    "event_type": "compliance_check",
                                    "severity": severity,
                                    "message": f"Compliance violation: {violation_type} detected",
                                    "context": (
                                        message[:200] + "..."
                                        if len(message) > 200
                                        else message
                                    ),
                                    "user_id": user_id
                                    or metadata.get("user_id", "unknown"),
                                    "action_taken": "logged",
                                    "confidence_score": 0.9,
                                    "guardrail_version": "2.0",
                                    "detection_metadata": {
                                        "model_version": "regex-compliance-v1.0",
                                        "detection_time_ms": 0,
                                        "triggered_rules": [violation_type],
                                        "matched_pattern": pattern,
                                    },
                                    "session_metadata": None,
                                }
                                producer.send_guardrail_event(
                                    conversation_id, alert_message
                                )
                                logger.info(
                                    f"✅ Compliance violation sent to Kafka for {conversation_id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to send compliance violation to Kafka: {e}",
                                exc_info=True,
                            )

        except Exception as e:
            # This 'except' block is now for UNEXPECTED system errors
            # (e.g., guardrails-ai itself crashed), not for validation failures.
            logger.error(f"CRITICAL system error during validation: {e}", exc_info=True)
            results["valid"] = False
            results["violations"].append(
                {
                    "type": "system_error",
                    "severity": "high",
                    "details": {"message": str(e)},
                }
            )

        # Calculate response time
        end_time = datetime.now()
        results["response_time_ms"] = int(
            (end_time - start_time).total_seconds() * 1000
        )

        logger.info(
            f"Validation complete for conversation {conversation_id}: {'PASS' if results['valid'] else 'FAIL'}"
        )

        return results

#!/usr/bin/env python3
"""
Guardrail Validators using Guardrails-AI
Uses validators from Guardrails Hub (https://github.com/guardrails-ai/guardrails)
"""

import os
import re
import uuid
import logging
import json               
import openai          
from typing import Dict, Any, Optional, List 
from datetime import datetime

try:
    from guardrails import Guard, OnFailAction 
    from guardrails.hub import ToxicLanguage, DetectPII
    GUARDRAILS_AVAILABLE = True
except ImportError as e:
    GUARDRAILS_AVAILABLE = False
    logging.warning(f"Guardrails-AI library not available: {e}")
    logging.warning("Please install guardrails-ai and validators from hub:")
    logging.warning("  pip install guardrails-ai")
    logging.warning("  guardrails hub install hub://guardrails/toxic_language")
    logging.warning("  guardrails hub install hub://guardrails/detect_pii")

# Note: Make sure this import path is correct for your project structure
from services.infrastructure.kafka import send_alert_to_kafka, get_kafka_producer

logger = logging.getLogger(__name__)


class GuardrailValidator:
    """Validates messages against guardrails using Guardrails-AI"""

    def __init__(self):
        """Initialize guardrails-ai validators"""
        self.enable_pii_detection = (
            os.getenv("GUARDRAIL_ENABLE_PII_DETECTION", "True").lower() == "true"
        )
        self.enable_toxicity_check = (
            os.getenv("GUARDRAIL_ENABLE_TOXICITY_CHECK", "True").lower() == "true"
        )
        self.enable_compliance_check = (
            os.getenv("GUARDRAIL_ENABLE_COMPLIANCE_CHECK", "True").lower() == "true"
        )
        
        # --- ADD NEW LLM CHECK SETTINGS ---
        self.enable_llm_context_check = (
            os.getenv("GUARDRAIL_ENABLE_LLM_CONTEXT_CHECK", "True").lower() == "true"
        )
        self.openai_client = None
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-1106")
        self.llm_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

        if self.enable_llm_context_check:
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OPENAI_API_KEY not set. LLM context check will be disabled.")
                self.enable_llm_context_check = False
            else:
                try:
                    self.openai_client = openai.OpenAI()
                    logger.info(f"✅ LLM Context-Aware validator enabled (OpenAI, model: {self.llm_model})")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.enable_llm_context_check = False
        # --- END NEW LLM CHECK SETTINGS ---

        # ---Compliance_patterns---
        self.compliance_patterns = [
            (
                r"\b(take|prescribe|dosage|diagnosis|treatment)\b",
                "medical_advice",
                "medium",
            ),
        ]

        self.guard = None
        self.feedback_learner = None  # Will be set if available
        self._initialize_guard()
    
    def set_feedback_learner(self, feedback_learner):
        """Set the feedback learner for adaptive threshold adjustments"""
        self.feedback_learner = feedback_learner
        logger.info("✅ Feedback learner connected to validator")

    def _initialize_guard(self):
        if not GUARDRAILS_AVAILABLE:
            logger.error("Guardrails-AI is not available. Cannot initialize guards.")
            return

        try:
            self.guard = Guard(name="conversational-guard")
            validators_added = []

            # Configure ToxicLanguage validator with adaptive thresholding
            if self.enable_toxicity_check:
                try:
                    # Get adaptive threshold if feedback learner is available
                    toxicity_threshold = 0.5
                    if self.feedback_learner:
                        threshold_multiplier = self.feedback_learner.get_threshold_multiplier('toxicity')
                        # Adjust threshold: higher multiplier = less sensitive (higher threshold)
                        toxicity_threshold = min(0.5 * threshold_multiplier, 1.0)
                        logger.debug(f"Using adaptive toxicity threshold: {toxicity_threshold:.2f} (multiplier: {threshold_multiplier:.2f})")
                    
                    self.guard = self.guard.use(
                        ToxicLanguage(
                            threshold=toxicity_threshold,
                            validation_method="sentence",
                            on_fail=send_alert_to_kafka,
                        )
                    )
                    validators_added.append("ToxicLanguage")
                    logger.info("✅ ToxicLanguage validator added")
                except Exception as e:
                    logger.warning(f"Failed to add ToxicLanguage validator: {e}")

            # Configure DetectPII validator for common sensitive entities
            if self.enable_pii_detection:
                try:
                    self.guard = self.guard.use(
                        DetectPII(
                            pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "SSN", "CREDIT_CARD"],
                            on_fail=send_alert_to_kafka,
                        )
                    )
                    validators_added.append("DetectPII")
                    logger.info("✅ DetectPII validator added")
                except Exception as e:
                    logger.warning(f"Failed to add DetectPII validator: {e}")

            if self.enable_compliance_check:
                logger.info("✅ Compliance check enabled (using custom regex validation)")
            
            # --- ADD LOGGING FOR LLM CHECK ---
            if self.enable_llm_context_check:
                 logger.info("✅ LLM Context-Aware check enabled")
            # --- END LOGGING ---

            if validators_added:
                logger.info(
                    f"✅ Guard initialized with {len(validators_added)} validator(s): {validators_added}"
                )
            else:
                logger.warning("⚠️ No stateless validators were added to the guard.")

        except Exception as e:
            logger.error(f"Failed to initialize Guard: {e}", exc_info=True)
            self.guard = None

    def validate(
        self,
        message: str,
        conversation_id: str,
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None, # <-- ADD THIS
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Validate a message against all configured guardrails

        Args:
            message: The message to validate
            conversation_id: The conversation ID
            user_id: Optional user ID
            conversation_history: Optional list of previous messages
                                  (e.g., [{"role": "user", "content": "..."}, ...])
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
            # Guard instance missing, return system error to caller
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
            # Prepare metadata
            user_id_str: str = (
                user_id
                or f'user_{conversation_id.split("_")[-1] if "_" in conversation_id else "unknown"}'
            )
            metadata = {
                "conversation_id": conversation_id,
                "user_id": user_id_str,
                **kwargs,
            }

            # --- 1. Run stateless validation first (fast) ---
            validation_outcome = self.guard.validate(
                message,
                metadata=metadata,
                **kwargs,
            )

            # Interpret Guardrails validation outcome to determine pass or fail
            validation_failed = False
            error_msg = "Validation failed"
            validated_output = None
            try:
                if hasattr(validation_outcome, "validated_output"):
                    validated_output = validation_outcome.validated_output
                if hasattr(validation_outcome, "error_message") and validation_outcome.error_message:
                    validation_failed = True
                    error_msg = str(validation_outcome.error_message)
                elif (
                    validated_output
                    and isinstance(validated_output, str)
                    and "BLOCKED:" in validated_output
                ):
                    validation_failed = True
                    error_msg = validated_output
                elif not validated_output:
                    validation_failed = True
            except AttributeError as e:
                logger.warning(f"Could not determine validation outcome: {e}")
                validation_failed = True
                error_msg = f"Unable to determine validation result: {e}"

            if validation_failed:
                logger.warning(f"Stateless validation failed for {conversation_id}: {error_msg}")
                results["valid"] = False
                results["violations"].append(
                    {
                        "type": "validation_failed",
                        "severity": "medium",
                        "details": {
                            "error_message": error_msg,
                            "message_preview": (
                                message[:100] + "..." if len(message) > 100 else message
                            ),
                        },
                    }
                )
            else:
                results["valid"] = True
                if validated_output:
                    results["message"] = validated_output

            # --- 2. Custom regex compliance checks (fast) ---
            if self.enable_compliance_check:
                for pattern, violation_type, severity in self.compliance_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        logger.warning(
                            f"Compliance violation detected: {violation_type} in conversation {conversation_id}"
                        )
                        results["valid"] = False
                        # Build compliance violation payload and publish to Kafka
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
                        try:
                            # Use get_kafka_producer from the top-level import
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
                                    "user_id": user_id or metadata.get("user_id", "unknown"),
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

            # --- 3. Run LLM Context-Aware Check (slower, run last) ---
            # Only run if stateless checks passed and the check is enabled
            if (
                results["valid"]  # Only check if it hasn't failed yet
                and self.enable_llm_context_check
                and self.openai_client
                and conversation_history is not None
            ):
                logger.info(f"Running LLM context-aware check for {conversation_id}")
                
                # The history + the new message
                messages_for_llm = conversation_history + [{"role": "user", "content": message}]
                
                system_prompt = """
                You are a context-aware guardrail. You will be given a conversation history.
                The last message is the one you must validate.
                Your job is to determine if this last message violates any policies
                *in the context of the preceding conversation*.

                Policies to check:
                1.  **Medical Advice:** Does the new message constitute giving or seeking a specific medical diagnosis, prescription, or treatment plan (e.g., "based on my symptoms, should I take X?" or "you should take X for your Y").
                2.  **Persistent Evasion:** Is the user repeatedly trying to bypass a stated refusal? (e.g., bot said "I can't give medical advice" and user is re-phrasing to get it anyway).
                3.  **Contextual Toxicity:** Is the message becoming toxic, harassing, or inappropriate *given the flow* of the conversation?

                Analyze the *last* message based on the history.
                
                Respond with a JSON object:
                {
                  "is_violation": boolean,
                  "reason": "A brief description of the violation, or 'none' if no violation."
                }
                """
                
                try:
                    llm_start_time = datetime.now()
                    
                    response = self.openai_client.chat.completions.create(
                        model=self.llm_model,
                        temperature=self.llm_temperature,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *messages_for_llm
                        ]
                    )
                    
                    llm_result_str = response.choices[0].message.content
                    llm_result = json.loads(llm_result_str)
                    
                    llm_end_time = datetime.now()
                    llm_time_ms = int((llm_end_time - llm_start_time).total_seconds() * 1000)

                    if llm_result.get("is_violation"):
                        llm_reason = llm_result.get('reason', 'LLM Context Violation')
                        logger.warning(
                            f"LLM Context-Aware violation detected: {llm_reason} in {conversation_id}"
                        )
                        results["valid"] = False
                        violation = {
                            "type": "context_violation",
                            "severity": "medium",
                            "details": {
                                "reason": llm_reason,
                                "message_preview": message[:100] + "...",
                            },
                        }
                        results["violations"].append(violation)

                        # Send this specific failure to Kafka
                        try:
                            producer = get_kafka_producer()
                            if producer and producer.producer:
                                alert_message = {
                                    "schema_version": "1.0",
                                    "event_id": str(uuid.uuid4()),
                                    "conversation_id": conversation_id,
                                    "timestamp": datetime.now().isoformat(),
                                    "event_type": "context_violation", # New event type
                                    "severity": "medium",
                                    "message": f"LLM Context Violation: {llm_reason}",
                                    "context": message[:200] + '...' if len(message) > 200 else message,
                                    "user_id": user_id_str,
                                    "action_taken": "logged",
                                    "confidence_score": 0.9, # Example
                                    "guardrail_version": "2.0",
                                    "detection_metadata": {
                                        "model_version": self.llm_model,
                                        "detection_time_ms": llm_time_ms,
                                        "triggered_rules": ["LLMContextAwareCheck"],
                                    },
                                    "session_metadata": None,
                                }
                                producer.send_guardrail_event(conversation_id, alert_message)
                                logger.info(f"✅ LLM Context violation sent to Kafka for {conversation_id}")
                        except Exception as e:
                            logger.error(f"Failed to send LLM violation to Kafka: {e}", exc_info=True)

                except Exception as llm_e:
                    logger.error(f"LLM Context-Aware check failed: {llm_e}", exc_info=True)
                    # FAIL-SAFE: If the LLM check fails, we "fail open" (allow the message)
                    # to prevent a service outage, but log it as a violation for review.
                    results["violations"].append({
                        "type": "system_error",
                        "severity": "high",
                        "details": {"message": f"LLM context check failed: {llm_e}"},
                    })
            
            # --- END OF ALL VALIDATIONS ---

        except Exception as e:
            # Catch any unexpected validator failures and mark as system error
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
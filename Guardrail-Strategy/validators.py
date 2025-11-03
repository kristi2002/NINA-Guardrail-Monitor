#!/usr/bin/env python3
"""
Guardrail Validators using Guardrails-AI
Uses validators from Guardrails Hub (https://github.com/guardrails-ai/guardrails)
"""

import os
import logging
from typing import Dict, Any
from datetime import datetime

try:
    from guardrails import Guard, OnFailAction
    from guardrails.hub import (
        ToxicLanguage,
        DetectPII,
        CompetitorCheck,
        ReadingTime,
        RegexMatch
    )
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
        self.enable_pii_detection = os.getenv('GUARDRAIL_ENABLE_PII_DETECTION', 'True').lower() == 'true'
        self.enable_toxicity_check = os.getenv('GUARDRAIL_ENABLE_TOXICITY_CHECK', 'True').lower() == 'true'
        self.enable_compliance_check = os.getenv('GUARDRAIL_ENABLE_COMPLIANCE_CHECK', 'True').lower() == 'true'
        
        self.guard = None
        self._initialize_guard()
    
    def _initialize_guard(self):
        """Initialize the Guard with validators from Guardrails Hub"""
        if not GUARDRAILS_AVAILABLE:
            logger.error("Guardrails-AI is not available. Cannot initialize guards.")
            return
        
        try:
            # Create a Guard
            self.guard = Guard(name='conversational-guard')
            
            # Add validators based on configuration
            validators_added = []
            
            # Add ToxicLanguage validator if enabled
            if self.enable_toxicity_check:
                try:
                    self.guard = self.guard.use(
                        ToxicLanguage(
                            threshold=0.5,
                            validation_method="sentence",
                            on_fail=send_alert_to_kafka  # Custom Kafka handler
                        )
                    )
                    validators_added.append("ToxicLanguage")
                    logger.info("✅ ToxicLanguage validator added")
                except Exception as e:
                    logger.warning(f"Failed to add ToxicLanguage validator: {e}")
                    logger.warning("Try running: guardrails hub install hub://guardrails/toxic_language")
            
            # Add PII Detection validator if enabled
            if self.enable_pii_detection:
                try:
                    self.guard = self.guard.use(
                        DetectPII(
                            pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "SSN", "CREDIT_CARD", "IP_ADDRESS"],
                            on_fail=send_alert_to_kafka
                        )
                    )
                    validators_added.append("DetectPII")
                    logger.info("✅ DetectPII validator added")
                except Exception as e:
                    logger.warning(f"Failed to add DetectPII validator: {e}")
                    logger.warning("Try running: guardrails hub install hub://guardrails/detect_pii")
            
            # Add compliance checks (custom regex patterns)
            if self.enable_compliance_check:
                try:
                    # Medical advice pattern - look for prescription-like language
                    medical_pattern = r'\b(take|prescribe|dosage|diagnosis|treatment)\b'
                    self.guard = self.guard.use(
                        RegexMatch(
                            regex=medical_pattern,
                            match_type="search",  # Search for pattern anywhere in the message
                            on_fail=send_alert_to_kafka
                        )
                    )
                    validators_added.append("MedicalCompliance")
                    logger.info("✅ Medical compliance validator added")
                except Exception as e:
                    logger.warning(f"Failed to add compliance validator: {e}")
            
            if validators_added:
                logger.info(f"✅ Guard initialized with {len(validators_added)} validator(s): {validators_added}")
            else:
                logger.warning("⚠️ No validators were added to the guard. Validation will not work properly.")
                
        except Exception as e:
            logger.error(f"Failed to initialize Guard: {e}", exc_info=True)
            self.guard = None
    
    def validate(self, message: str, conversation_id: str, user_id: str = None, **kwargs) -> Dict[str, Any]:
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
            'valid': True,
            'violations': [],
            'response_time_ms': 0,
            'validation_timestamp': start_time.isoformat()
        }
        
        logger.info(f"Validating message for conversation {conversation_id}")
        
        if not self.guard:
            logger.error("Guard not initialized. Cannot validate.")
            results['valid'] = False
            results['violations'].append({
                'type': 'system_error',
                'severity': 'high',
                'details': {'message': 'Guard not initialized'}
            })
            return results
        
        try:
            # Prepare metadata for validators
            metadata = {
                'conversation_id': conversation_id,
                'user_id': user_id or f'user_{conversation_id.split("_")[-1] if "_" in conversation_id else "unknown"}',
                **kwargs
            }
            
            # Validate using guardrails-ai
            # This returns a ValidationOutcome object.
            # It will NOT raise an exception on failure because
            # we are using a custom on_fail handler.
            validation_outcome = self.guard.validate(
                message,
                metadata=metadata,
                **kwargs  # Pass metadata/kwargs to the guard
            )
            
            # --- THIS IS THE FIX ---
            # Check the 'outcome' attribute of the result.
            if validation_outcome.outcome == 'fail':
                # The on_fail handler was already called.
                # Just log it and set the result to invalid.
                logger.warning(f"Validation failed for {conversation_id}: {validation_outcome.error_message}")
                results['valid'] = False
                results['violations'].append({
                    'type': 'validation_failed',
                    'severity': 'medium',  # kafka_handler set the "real" severity
                    'details': {
                        'error_message': str(validation_outcome.error_message),
                        'message_preview': message[:100] + '...' if len(message) > 100 else message
                    }
                })
            else:
                # Validation passed
                results['valid'] = True
                results['message'] = validation_outcome.validated_output
        
        except Exception as e:
            # This 'except' block is now for UNEXPECTED system errors
            # (e.g., guardrails-ai itself crashed), not for validation failures.
            logger.error(f"CRITICAL system error during validation: {e}", exc_info=True)
            results['valid'] = False
            results['violations'].append({
                'type': 'system_error',
                'severity': 'high',
                'details': {'message': str(e)}
            })
        
        # Calculate response time
        end_time = datetime.now()
        results['response_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"Validation complete for conversation {conversation_id}: {'PASS' if results['valid'] else 'FAIL'}")
        
        return results

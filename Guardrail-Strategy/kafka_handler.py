#!/usr/bin/env python3
"""
Kafka Handler for Guardrails AI
Custom on_fail handler that sends guardrail failures to Kafka
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from guardrails.validator_base import FailResult 

logger = logging.getLogger(__name__)

# Initialize Kafka producer (singleton)
_kafka_producer = None

def get_kafka_producer():  # Removed type annotation to avoid forward reference error
    """Get or create Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer is None:
        # Lazy import to avoid circular dependency
        from kafka_producer import GuardrailKafkaProducer # type: ignore
        _kafka_producer = GuardrailKafkaProducer()
    return _kafka_producer

def send_alert_to_kafka(value: str, fail_result: FailResult, metadata: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """
    Custom on_fail handler for Guardrails AI.
    
    This function is called automatically by guardrails-ai when a validation fails.
    It formats an alert and sends it to Kafka.
    
    Args:
        value: The text that failed validation
        fail_result: The FailResult object containing error details
        metadata: Optional metadata dictionary (may contain conversation_id)
        **kwargs: Additional keyword arguments
    
    Returns:
        str: A message indicating the failure (this is returned to the caller)
    """
    logger.warning(f"🔥 Guardrail failure detected! Sending to Kafka...")
    
    # Get conversation_id from various possible sources
    # Generate a valid conversation_id if not found
    import uuid
    conversation_id = (
        kwargs.get('conversation_id') or
        (metadata.get('conversation_id') if metadata else None) or
        f"conv_{uuid.uuid4().hex[:12]}"
    )
    
    # Extract validator information
    validator_name = "unknown"
    if hasattr(fail_result, 'validator') and fail_result.validator:  # type: ignore
        validator_name = fail_result.validator.__class__.__name__  # type: ignore
    
    # Determine event type and severity based on validator type
    event_type = "warning_triggered"  # Default
    severity = "medium"
    
    validator_lower = validator_name.lower()
    if "toxic" in validator_lower or "inappropriate" in validator_lower:
        event_type = "inappropriate_content"
        severity = "medium"
    elif "pii" in validator_lower or "privacy" in validator_lower:
        event_type = "privacy_violation_prevented"
        severity = "high"
    elif "medical" in validator_lower or "compliance" in validator_lower:
        event_type = "compliance_check"  # Use the enum from the new schema
        severity = "medium"
    
    # Format the alert message to match the new 'guardrail_event_v1.schema.json'
    alert_message = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "message": f"Guardrail Failure: {fail_result.error_message}",
        "context": value[:200] + '...' if len(value) > 200 else value,
        "user_id": kwargs.get('user_id', f'user_{conversation_id.split("_")[-1] if "_" in conversation_id else "unknown"}'),
        "action_taken": "logged",  # This is a valid enum
        "confidence_score": 0.85,  # Example score
        "guardrail_version": "2.0",
        
        # This field is now 'detection_metadata' and is an object
        "detection_metadata": {
            "model_version": "guardrails-ai-v0.1",
            "detection_time_ms": 0,  # 'response_time_ms' is renamed and moved here
            "triggered_rules": [validator_name]
        },
        
        # 'session_metadata' is allowed to be null and we don't have this data
        "session_metadata": None
    }
    
    # Send to Kafka
    producer = get_kafka_producer()
    if producer and producer.producer:
        try:
            success = producer.send_guardrail_event(conversation_id, alert_message)
            if success:
                logger.info(f"✅ Alert for {conversation_id} sent to Kafka. Validator: {validator_name}")
            else:
                logger.warning(f"⚠️ Failed to send alert to Kafka for {conversation_id}")
        except Exception as e:
            logger.error(f"❌ ERROR sending alert to Kafka: {e}", exc_info=True)
    else:
        logger.warning("❌ Kafka producer is not available. Alert not sent.")
    
    # Return a string that will be seen by the caller
    # This message indicates the validation failed
    return f"BLOCKED: {fail_result.error_message}"


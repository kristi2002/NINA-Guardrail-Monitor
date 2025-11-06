# Kafka Message Specifications for NINA Guardrail Monitor

This document specifies the Kafka message formats used in the NINA Guardrail Monitor system. All message formats are defined using JSON Schema Draft 7.

**Last Updated:** 2025  
**Schema Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Kafka Topics](#kafka-topics)
3. [Message Schemas](#message-schemas)
   - [Guardrail Events](#guardrail-events)
   - [Operator Actions](#operator-actions)
4. [Message Flow](#message-flow)
5. [Validation](#validation)

---

## Overview

The NINA Guardrail Monitor uses Kafka for asynchronous communication between three main components:

1. **Guardrail Strategy Service** - Validates messages and publishes guardrail events
2. **OFH Dashboard** - Monitors conversations and sends admin actions
3. **AI Agent** (Future) - Consumes admin actions and publishes conversation events

---

## Kafka Topics

The system uses four static Kafka topics:

| Topic Name | Producer | Consumer | Description |
|------------|----------|----------|-------------|
| `guardrail_events` | Guardrail Strategy Service | OFH Dashboard | Guardrail violations and monitoring events |
| `operator_actions` | OFH Dashboard | AI Agent | Commands from dashboard admins |
| `guardrail_control` | (Future) | OFH Dashboard | Control messages for guardrails |
| `dead_letter_queue` | All | System | Failed messages for manual review |

---

## Message Schemas

### Guardrail Events

**Topic:** `guardrail_events`  
**Producer:** Guardrail Strategy Service  
**Consumer:** OFH Dashboard  
**Schema Version:** 1.0

Guardrail events are published whenever a message validation fails or a monitoring event occurs.

#### Message Structure

```json
{
  "schema_version": "1.0",
  "event_id": "uuid-string",
  "conversation_id": "string",
  "timestamp": "ISO 8601 datetime",
  "event_type": "string",
  "severity": "string",
  "message": "string",
  "context": "string or null",
  "user_id": "string or null",
  "action_taken": "string or null",
  "confidence_score": "number or null",
  "guardrail_version": "string or null",
  "session_metadata": "object or null",
  "detection_metadata": "object or null"
}
```

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Must be `"1.0"` |
| `event_id` | string | Unique UUID for this event |
| `conversation_id` | string | Unique conversation identifier |
| `timestamp` | string | ISO 8601 format datetime |
| `event_type` | string | Event type (see enum below) |
| `severity` | string | Severity level (see enum below) |
| `message` | string | Human-readable description |

#### Event Types

| Value | Description |
|-------|-------------|
| `conversation_started` | New conversation initiated |
| `warning_triggered` | Warning-level guardrail triggered |
| `alarm_triggered` | Alarm-level guardrail triggered |
| `privacy_violation_prevented` | PII or privacy violation detected and blocked |
| `medication_warning` | Medical advice detected |
| `inappropriate_content` | Toxic/inappropriate content detected |
| `emergency_protocol` | Emergency situation detected |
| `conversation_ended` | Conversation terminated |
| `false_alarm_reported` | False positive reported by operator |
| `operator_intervention` | Manual operator intervention |
| `system_alert` | System-level alert |
| `compliance_check` | Compliance violation detected |

#### Severity Levels

| Value | Description |
|-------|-------------|
| `info` | Informational event |
| `medium` | Moderate severity |
| `high` | High severity |
| `critical` | Critical severity requiring immediate attention |

#### Action Taken Values

| Value | Description |
|-------|-------------|
| `blocked` | Message was blocked |
| `warned` | Warning issued but message allowed |
| `logged` | Event logged only |
| `escalated` | Escalated to operator |
| `allowed` | Message allowed through |
| `null` | No action taken |

#### Optional Objects

**session_metadata** (when provided):
```json
{
  "start_time": "ISO 8601 datetime",
  "message_count": "integer",
  "duration_seconds": "integer",
  "user_agent": "string or null",
  "ip_address": "string or null"
}
```

**detection_metadata** (when provided):
```json
{
  "model_version": "string or null",
  "detection_time_ms": "number or null",
  "triggered_rules": ["array of strings"],
  "false_positive_probability": "number or null"
}
```

#### Example: Privacy Violation Detected

```json
{
  "schema_version": "1.0",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "conv-abc-123",
  "timestamp": "2025-01-15T10:30:00Z",
  "event_type": "privacy_violation_prevented",
  "severity": "high",
  "message": "Guardrail Failure: PII detected",
  "context": "My email is john.doe@example.com...",
  "user_id": "user_12345",
  "action_taken": "logged",
  "confidence_score": 0.85,
  "guardrail_version": "2.0",
  "session_metadata": null,
  "detection_metadata": {
    "model_version": "guardrails-ai-v0.1",
    "detection_time_ms": 150,
    "triggered_rules": ["DetectPII"]
  }
}
```

#### Example: Conversation Started

```json
{
  "schema_version": "1.0",
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "conversation_id": "conv-xyz-789",
  "timestamp": "2025-01-15T10:35:00Z",
  "event_type": "conversation_started",
  "severity": "info",
  "message": "New conversation started",
  "context": null,
  "user_id": "user_67890",
  "action_taken": null,
  "confidence_score": null,
  "guardrail_version": "2.0",
  "session_metadata": {
    "start_time": "2025-01-15T10:35:00Z",
    "message_count": 0,
    "duration_seconds": 0,
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100"
  },
  "detection_metadata": null
}
```

---

### Admin Actions (Operator Actions)

**Topic:** `operator_actions`  
**Producer:** OFH Dashboard  
**Consumer:** AI Agent  
**Schema Version:** 1.0

Admin actions (formerly operator actions) are commands sent from the dashboard to control AI agent behavior.

#### Message Structure

```json
{
  "schema_version": "1.0",
  "conversation_id": "string",
  "timestamp": "ISO 8601 datetime",
  "action_type": "string",
  "operator_id": "string",
  "message": "string",
  "reason": "string or null",
  "priority": "string",
  "target_event_id": "string or null",
  "command": "object or null",
  "action_metadata": "object or null",
  "system_context": "object or null"
}
```

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version |
| `conversation_id` | string | Unique conversation identifier |
| `timestamp` | string | ISO 8601 format datetime |
| `action_type` | string | Action type (see enum below) |
| `operator_id` | string | Admin identifier (legacy field name) |
| `message` | string | Human-readable description |

#### Action Types

| Value | Description |
|-------|-------------|
| `stop_conversation` | Stop the conversation immediately |
| `false_alarm` | Mark event as false alarm |
| `escalate` | Escalate to higher priority |
| `acknowledge` | Acknowledge the event |
| `resolve` | Resolve the event |
| `override_guardrail` | Override guardrail decision |
| `manual_intervention` | Manual intervention required |
| `system_override` | System-level override |
| `emergency_stop` | Emergency stop protocol |
| `resume_conversation` | Resume a paused conversation |

#### Priority Levels

| Value | Description |
|-------|-------------|
| `low` | Low priority |
| `normal` | Normal priority |
| `high` | High priority |
| `urgent` | Urgent priority |

#### Optional Objects

**command** (for AI Agent):
```json
{
  "type": "string",
  "reason": "string or null",
  "final_message": "string or null"
}
```

**action_metadata**:
```json
{
  "response_time_seconds": "number or null",
  "escalation_level": "string or null",
  "notification_sent": "boolean or null",
  "follow_up_required": "boolean or null",
  "resolution_notes": "string or null"
}
```

**system_context**:
```json
{
  "active_guardrails": ["array of strings"],
  "conversation_state": "string or null",
  "risk_level": "string or null"
}
```

#### Example: Stop Conversation

```json
{
  "schema_version": "1.0",
  "conversation_id": "conv-abc-123",
  "timestamp": "2025-01-15T10:45:00Z",
  "action_type": "stop_conversation",
  "operator_id": "admin_001",
  "message": "This conversation has been ended by an admin.",
  "reason": "Toxic content detected repeatedly",
  "priority": "urgent",
  "target_event_id": "550e8400-e29b-41d4-a716-446655440000",
  "command": {
    "type": "stop_conversation",
    "reason": "Toxic content detected repeatedly",
    "final_message": "This conversation has been ended by an operator."
  },
  "action_metadata": {
    "response_time_seconds": 5.2,
    "escalation_level": "supervisor",
    "notification_sent": true,
    "follow_up_required": true,
    "resolution_notes": "User repeatedly attempted to use inappropriate language"
  },
  "system_context": {
    "active_guardrails": ["ToxicLanguage", "DetectPII"],
    "conversation_state": "active",
    "risk_level": "high"
  }
}
```

#### Example: False Alarm Report

```json
{
  "schema_version": "1.0",
  "conversation_id": "conv-xyz-789",
  "timestamp": "2025-01-15T10:50:00Z",
  "action_type": "false_alarm",
  "operator_id": "admin_002",
  "message": "Marked as false alarm - content is acceptable in context",
  "reason": "Medical context requires these terms",
  "priority": "normal",
  "target_event_id": "770e8400-e29b-41d4-a716-446655440002",
  "command": null,
  "action_metadata": {
    "response_time_seconds": 2.1,
    "escalation_level": null,
    "notification_sent": false,
    "follow_up_required": false,
    "resolution_notes": "User discussing medical symptoms with valid terminology"
  },
  "system_context": {
    "active_guardrails": ["MedicalCompliance"],
    "conversation_state": "active",
    "risk_level": "low"
  }
}
```

---

## Message Flow

### 1. Guardrail Event Flow

```
AI Agent generates message
         ↓
POST /validate to Guardrail Strategy Service
         ↓
Guardrail-AI validation
         ↓
If FAIL → publish to guardrail_events topic
         ↓
OFH Dashboard consumes event
         ↓
Store in database & show alert
```

### 2. Admin Action Flow

```
Admin clicks action in dashboard
         ↓
Dashboard publishes to operator_actions topic
         ↓
AI Agent consumes action
         ↓
Execute command (stop, override, etc.)
```

---

## Validation

All messages are validated against their respective JSON schemas before processing. Messages that fail validation are sent to the `dead_letter_queue` for manual review.

### Schema Files

- **Guardrail Events:** `OFH-Dashboard/backend/schemas/guardrail_event.schema.json`
- **Operator Actions:** `OFH-Dashboard/backend/schemas/operator_action.schema.json`

### Validation Example

```python
from jsonschema import validate
from jsonschema.exceptions import ValidationError

try:
    validate(instance=message, schema=guardrail_event_schema)
    # Process message
except ValidationError as e:
    # Send to DLQ
    send_to_dlq(message, error=str(e))
```

---

## Notes for Integrators

1. **Schema Versioning:** Always include `schema_version` field. Future versions will maintain backward compatibility.
2. **Timestamps:** Use ISO 8601 format with timezone information.
3. **UUIDs:** Use UUID v4 for all ID fields.
4. **Null Values:** Optional fields should be `null`, not omitted.
5. **Topic Names:** Use environment variables for topic names to support different environments.
6. **Dead Letter Queue:** Failed messages are sent to `dead_letter_queue` - always monitor this topic.

---

## Contact

For questions or clarifications:
- **Kristi:** [Contact information]
- **Repository:** https://github.com/PROSLab/OFH-Dashboard
- **Issues:** https://github.com/PROSLab/OFH-Dashboard/issues

---

**Document Version:** 1.0  
**Last Updated:** 2025  
**Maintained By:** NINA Guardrail Monitor Team


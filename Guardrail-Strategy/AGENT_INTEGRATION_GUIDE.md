# AI Agent → Guardrail Strategy Integration Guide

This document describes the data contracts, Kafka topics, and API calls your teammate must follow so that the AI agent chat plugs into the guardrail monitoring stack without any surprises.

---

## 1. High-Level Flow

1. **Agent emits guardrail events** → publish to Kafka so the dashboard can ingest them.
2. **Dashboard operators respond** → control feedback is written to Kafka (`guardrail_control`).
3. **Guardrail Strategy consumes feedback** → updates the learning loop and adjusts guardrails.
4. **Conversation transcripts** → optional REST hook or Kafka stream keeps the dashboard’s transcript view in sync.

Keep the shared schema library (`shared/guardrail_schemas`) as the source of truth for payload shapes.

---

## 2. Publish Guardrail Events

**Topic:** `guardrail_events` (or pattern `guardrail.conversation.*` if you enable topic wildcards).  
**Schema:** `GuardrailEvent` dataclass.

```jsonc
{
  "schema_version": "1.0",
  "conversation_id": "conv_123",
  "event_id": "evt_20250219_001",
  "timestamp": "2025-02-19T12:34:56.789Z",
  "event_type": "alarm_triggered",          // aligns with dashboard mappings
  "severity": "high",                       // info | low | medium | high | critical
  "message": "Toxic language detected.",
  "context": "Full agent message or summary.",
  "user_id": "agent_backend",
  "action_taken": "blocked_response",       // optional
  "confidence_score": 0.92,
  "guardrail_version": "v2.1.0",
  "session_metadata": {
    "channel": "chat",
    "language": "it"
  },
  "detection_metadata": {
    "triggered_rules": ["ToxicLanguage.v1"],
    "model_version": "moderation-2025-02"
  }
}
```

**Implementation tips**
- Import `GuardrailEvent` from `shared.guardrail_schemas` and instantiate it for validation before send.
- Stick to ISO-8601 timestamps (`datetime.utcnow().isoformat()` + `"Z"`).
- Severity drives dashboard visuals, so choose the right level.

---

## 3. Consume Control Feedback

**Topic:** `guardrail_control` (already consumed by `GuardrailKafkaConsumer`).  
**Schema:** `GuardrailControlFeedback`.

```jsonc
{
  "conversation_id": "conv_123",
  "timestamp": "2025-02-19T12:40:00.500Z",
  "feedback_type": "false_alarm",           // false_alarm | true_positive | guardrail_adjustment | ...
  "feedback_content": "Operator confirmed this was benign.",
  "feedback_source": "dashboard_operator",
  "original_event_id": "evt_20250219_001",
  "context": {
    "reason": "Patient used reclaimed language.",
    "triggered_rules": ["ToxicLanguage.v1"]
  },
  "feedback_metadata": {
    "priority": "normal",
    "conversation_state": "active",
    "risk_level": "low"
  },
  "schema_version": "1.0"
}
```

**What to do with it**
- False alarms → call `FeedbackLearner.record_false_alarm(...)`.
- True positives → call `FeedbackLearner.record_true_positive(...)`.
- Guardrail adjustments → adjust your policy cache or raise TODOs.

---

## 4. Stream Conversation Transcripts (Optional but Recommended)

To keep the monitoring UI aligned with the agent conversation history, POST messages to the dashboard’s transcript API.

**Endpoint:** `POST /api/transcripts` (requires the dashboard’s auth token).  
**Payload example:**

```jsonc
{
  "conversation_id": "conv_123",
  "message_id": "msg_0001",
  "timestamp": "2025-02-19T12:30:00.000Z",
  "sender_type": "user",                     // user | bot | system | operator
  "content": "Buongiorno, ho bisogno di aiuto.",
  "sender_id": "patient_456",
  "sender_name": "Maria Rossi",
  "sequence_number": 1,
  "sentiment_score": 0.18,
  "language": "it",
  "risk_score": 0.2,
  "contains_sensitive_content": false,
  "flagged_keywords": [],
  "response_time_ms": 0,
  "model_version": "agent-v1.4",
  "attachments": []
}
```

You can also emit transcript entries to a dedicated Kafka topic if you prefer, but the REST endpoint is ready to go today.

---

## 5. Configuration Checklist

| Variable                          | Agent Value                                        | Notes                                       |
|----------------------------------|----------------------------------------------------|---------------------------------------------|
| `KAFKA_BOOTSTRAP_SERVERS`        | `localhost:9092` (or shared cluster)               | Must match what the dashboard/strategy use. |
| `KAFKA_TOPIC_GUARDRAIL`          | `guardrail_events`                                 | Align with `config.py` defaults.            |
| `KAFKA_TOPIC_CONTROL`            | `guardrail_control`                                | For feedback consumption.                   |
| `KAFKA_GROUP_ID`                 | `guardrail-strategy-service` (or custom)           | Ensure unique consumer groups if needed.    |
| `SHARED_SCHEMA_PATH` (optional)  | Use repo’s `shared` package                        | Don’t duplicate schema definitions.         |
| Auth token for `/api/transcripts`| Obtain via existing dashboard auth flow            | Needed only if you use REST transcripts.    |

> **Tip:** keep `.env` files in sync across services, or create a shared `.env.common` to source variables consistently.

---

## 6. Minimum Test Script

1. Start Kafka, Postgres, dashboard backend, and guardrail strategy.
2. Produce a sample `GuardrailEvent`.
3. Verify:
   - Dashboard updates (metrics + alerts).
   - Event stored in DB (`guardrail_events` table).
4. Trigger an operator feedback event (false alarm) from the dashboard:
   - Check guardrail strategy logs for the acknowledgment.
   - Confirm `FeedbackLearner` updated its counters (`get_recent_feedback()`).
5. (Optional) POST a transcript message and ensure it appears on the dashboard conversation detail view.

---

## 7. Deliverables for Your Teammate

1. **Kafka producer** in the agent service that marshals `GuardrailEvent`.  
2. **Transcript pusher** (REST or Kafka) to keep the dashboard session timeline accurate.  
3. **Integration tests or scripts** that publish sample data and verify the monitoring stack responds.  
4. **Documentation** of any additional metadata fields the agent plans to send so we can update shared schemas if necessary.

Once these steps are complete, the AI agent will be fully visible to operators, and their feedback will feed back into the guardrail adaptation loop. Let us know if any schema extension is needed before implementation starts.


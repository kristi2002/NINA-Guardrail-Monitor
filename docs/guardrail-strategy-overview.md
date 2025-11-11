# Guardrail Strategy Service Code Walkthrough

This document explains how the `Guardrail-Strategy` Python service works, module by module. It is meant as a companion to the source code so new contributors can understand how conversation messages are validated, how feedback is processed, and how Kafka integration is implemented.

---

## 1. Service Role and Runtime Layout

- **Purpose**: validate AI-generated conversation messages in real time for privacy, toxicity, and compliance issues and publish structured violations to Kafka.
- **Entry point**: `Guardrail-Strategy/app.py` which boots Flask, the validator pipeline, Kafka integrations, and adaptive learning.
- **Key folders**:
  - `services/validation/` – stateless validators, regex checks, optional LLM context check.
  - `services/infrastructure/kafka/` – Kafka producer, consumer, and the Guardrails-AI `on_fail` handler.
  - `services/learning/` – feedback learner that ingests operator feedback and tunes validators.
  - `shared/guardrail_schemas/` – shared JSON Schemas used to validate outgoing Kafka messages.

At startup the service loads environment variables, connects the validator to the feedback learner, then tries to spin up a Kafka producer and (optionally) a background consumer for operator feedback. None of these dependencies are required to start; connectivity failures are logged and the service continues in a degraded-but-operational mode.

---

## 2. Flask Application (`app.py`)

`app.py` wires the service together and exposes HTTP endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Reports service status, Kafka connectivity, and adaptive learning stats. |
| `GET /analytics/performance` | Returns feedback learner analytics (false-alarm rates, problematic rules, trend data). |
| `GET /analytics/export-training-data` | Exports raw feedback lists for offline model retraining (JSON or CSV). |
| `POST /validate` | Validates a single message; returns all violation details. |
| `POST /validate/batch` | Validates an array of messages for bulk checks. |

Supporting setup steps performed during import:

1. Load `.env` values via `python-dotenv`.
2. Create a `GuardrailValidator` instance (`services.validation.guardrail_validator.GuardrailValidator`).
3. Try to instantiate `GuardrailKafkaProducer`; fall back to a no-op wrapper if Kafka is unavailable.
4. Instantiate a single `FeedbackLearner` and attach it to both the validator and the Kafka consumer so they share adaptive statistics.
5. Start `GuardrailKafkaConsumer` in a daemon thread, allowing the service to ingest operator feedback asynchronously.

All endpoints return JSON, include descriptive error payloads, and deliberately avoid throwing 500s for Kafka unavailability (Kafka status is surfaced in responses instead).

---

## 3. Validation Pipeline (`services/validation/guardrail_validator.py`)

The `GuardrailValidator` class centralizes all validation stages. It is initialized once and reused across requests.

### 3.1 Configuration Flags

Environment variables enable or disable individual checks:

- `GUARDRAIL_ENABLE_PII_DETECTION`, `GUARDRAIL_ENABLE_TOXICITY_CHECK`, `GUARDRAIL_ENABLE_COMPLIANCE_CHECK`
- `GUARDRAIL_ENABLE_LLM_CONTEXT_CHECK`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE` (required for the LLM context-aware stage)

If OpenAI credentials are missing, the LLM stage is disabled automatically and a warning is logged.

### 3.2 Stateless Guardrails (Guardrails-AI)

The validator configures the Guardrails-AI `Guard` with available detectors:

- `ToxicLanguage` (threshold optionally adjusted by the feedback learner)
- `DetectPII` (email, phone, SSN, credit card)

Each detector is registered with `send_alert_to_kafka` as its `on_fail` callback. When a rule fails, Guardrails-AI invokes that handler, which formats and publishes a Kafka event (see section 4).

### 3.3 Custom Compliance Regex Checks

A light-weight regex pass scans for domain-specific compliance violations (for example, potential medical advice). When triggered it:

1. Marks the request as invalid.
2. Builds a Kafka event locally using `get_kafka_producer`.
3. Sends the event to Kafka with enriched metadata (matched pattern, preview text).

### 3.4 LLM Context-Aware Check

After stateless checks succeed, and only if enabled, the validator runs an LLM-powered contextual audit:

1. Merges `conversation_history` (if provided) with the current message.
2. Calls OpenAI Chat Completions with a JSON response format requesting `{ "is_violation": bool, "reason": string }`.
3. If the model flags the message, the validator adds a `context_violation`, attaches supplementary details, and pushes a new Kafka alert.
4. Failure to reach the LLM does **not** block the request; instead the service logs a system violation for later investigation.

### 3.5 Result Object

Every call to `validate(...)` returns a dict with:

- `valid`: overall pass/fail flag.
- `violations`: list containing type, severity, preview, and metadata.
- `response_time_ms`: measured runtime across all stages.
- For passes, a normalized `message` field if Guardrails-AI returned a sanitized output.

---

## 4. Kafka Publishing (`services/infrastructure/kafka`)

### 4.1 `GuardrailKafkaProducer`

- Lazily connects to the broker supplied by `KAFKA_BOOTSTRAP_SERVERS`.
- Serializes payloads as UTF-8 JSON and sends to the `KAFKA_OUTPUT_TOPIC` (default `guardrail_events`).
- Uses short timeouts and capped retry attempts to prevent API calls from blocking the Flask thread.
- Exposes `send_guardrail_event(conversation_id, event_dict)` for callers.

### 4.2 Guardrails-AI Failure Handler (`kafka_handler.py`)

- Cached schema (`shared/guardrail_schemas/guardrail_event_v1.schema.json`) guarantees outgoing events match the cross-service contract.
- `send_alert_to_kafka(...)` is registered as the `on_fail` callback for Guardrails-AI validators. It:
  1. Classifies event type/severity based on the failing validator.
  2. Builds the JSON payload with conversation context and detection metadata.
  3. Validates against the shared schema using `jsonschema`.
  4. Sends the message through the singleton producer.
- Designed to be safe even when Kafka is down (logs warning and returns `BLOCKED: ...` to the caller).

### 4.3 `GuardrailKafkaConsumer`

- Subscribes to `KAFKA_TOPIC_CONTROL` (default `guardrail_control`) to ingest operator feedback emitted by the dashboard.
- Runs inside a background thread, automatically reconnecting with exponential backoff.
- Parses messages using the shared `GuardrailControlFeedback` dataclass for type safety.
- Routes actionable feedback to the `FeedbackLearner` (false alarms, true positives, suggested adjustments).
- Tracks basic telemetry (`get_feedback_stats`) so `/health` can report consumer status and learning metrics.

---

## 5. Adaptive Feedback Learning (`services/learning/feedback_learner.py`)

The `FeedbackLearner` class closes the loop between operator feedback and validator sensitivity.

### Responsibilities

- Persist the latest up to 1000 false alarms and true positives on disk (`guardrail_feedback.json` by default).
- Track per-rule statistics (counts, false-alarm rates, last updated timestamp).
- Maintain threshold multipliers per validator type (PII, toxicity, compliance, LLM context).
- Provide analytics endpoints (`get_statistics`, `get_problematic_rules`, `get_feedback_timeline`, `get_recent_feedback`).
- Support data export for offline retraining (`/analytics/export-training-data`).

### Interaction Flow

1. Dashboard emits feedback message to Kafka (e.g., operator marks an alert as false).
2. `GuardrailKafkaConsumer` consumes the message, parses it, and calls `record_false_alarm(...)` or `record_true_positive(...)`.
3. Feedback learner updates stats and recalculates threshold multipliers (increase multiplier to relax overly sensitive validators, or decrease to tighten).
4. `GuardrailValidator` reads those multipliers the next time it builds/upgrades a Guardrails detector, giving the system a self-correcting loop.

### Configuration

Environment variables adjust minimum sample size and tuning aggressiveness:

- `GUARDRAIL_MIN_FEEDBACK` – number of samples before adjustments kick in.
- `GUARDRAIL_ADJUSTMENT_FACTOR` – multiplier applied per adjustment step.
- `GUARDRAIL_MAX_ADJUSTMENT` – upper bound to prevent extreme changes.

---

## 6. Error Handling and Resilience

- Kafka outages downgrade functionality gracefully; the service continues to validate messages and returns informative status flags.
- Every try/except block logs diagnostic detail with `exc_info=True` so logs capture stack traces.
- Circuit-breaker style retry caps in producer and consumer prevent runaway connection attempts.
- The LLM stage fails open to avoid blocking message flow during external API incidents.
- `/health` surfaces producer/consumer connectivity, validator flags, and adaptive learning state for quick diagnostics.

---

## 7. Observability Hooks

- Structured log messages include emojis and keywords that make it easy to search for validation failures, Kafka issues, or feedback ingestion events.
- Kafka events themselves carry `detection_metadata` fields (model name, detection time, triggered rules) so downstream analytics can segment false alarms from true positives.
- Performance endpoints expose seven-day timelines, accuracy metrics, and problem rule summaries for dashboards.

---

## 8. Local Development Tips

1. Copy `Guardrail-Strategy/env.example` to `.env` and set Kafka/OpenAI credentials.
2. Run the Flask app via `python app.py` (port defaults to 5001).
3. Start Kafka locally or point `KAFKA_BOOTSTRAP_SERVERS` at a remote broker; if Kafka is down the service still validates but skips publishing.
4. Use `POST /validate` with sample payloads to confirm detector behavior.
5. Post feedback messages to the `guardrail_control` topic to exercise adaptive learning (or inspect saved feedback file).
6. Watch service logs for `✅`, `⚠️`, and `❌` markers indicating connection status and validation results.

---

## 9. How Components Fit Together

1. **Validate** – `/validate` receives a message, runs stateless Guardrails checks, compliance regex, and optional LLM context audit.
2. **Alert** – Any violation triggers `send_alert_to_kafka`, producing a schema-validated event to `guardrail_events`.
3. **Review** – Operators act in the dashboard; their feedback is published to `guardrail_control`.
4. **Learn** – `GuardrailKafkaConsumer` forwards feedback to `FeedbackLearner`, which updates rule statistics and threshold multipliers.
5. **Adjust** – On the next validation, `GuardrailValidator` reads updated multipliers and tunes guardrail sensitivity, reducing repetitive false alarms.

This closed loop keeps guardrail enforcement strict where necessary, relaxed where operators signal noise, and always observable through Kafka events and analytics endpoints.



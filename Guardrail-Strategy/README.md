# Guardrail Strategy Service

**System 2: The Guard** - A Flask microservice for validating LLM responses before they're sent to users.

This service validates messages using Guardrails-AI and publishes violations to Kafka for monitoring in the NINA Dashboard.

## Architecture

```
AI Agent generates response
         ↓
POST /validate (HTTP)
         ↓
Guardrail Strategy Service
├─→ Validates with Guardrails-AI
│   ├─→ ToxicLanguage validator
│   ├─→ DetectPII validator
│   └─→ Compliance validator
         ↓
    Pass or Fail
         ↓
    If Fail: Send to Kafka
    If Pass: Return success
```

## Quick Start

### 1. Setup Virtual Environment (Windows)

**Option A: Using setup script (Recommended)**
```powershell
.\setup.bat
```

**Option B: Manual setup**
```powershell
# Create virtual environment with Python 3.12
py -3.12 -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env.example` to `.env`:
```powershell
copy env.example .env
```

Then edit `.env` with your configuration:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_OUTPUT_TOPIC=guardrail_events

# Guardrails Configuration
GUARDRAIL_ENABLE_PII_DETECTION=True
GUARDRAIL_ENABLE_TOXICITY_CHECK=True
GUARDRAIL_ENABLE_COMPLIANCE_CHECK=True

# Optional: OpenAI for advanced features
OPENAI_API_KEY=your-key-here

# Service Configuration
PORT=5001
LOG_LEVEL=INFO
```

### 3. Start the Service

**Option A: Using run script**
```powershell
.\run.bat
```

**Option B: Manual start**
```powershell
# Activate virtual environment (if not already activated)
.\venv\Scripts\Activate.ps1

# Run the service
python app.py
```

Service starts on `http://localhost:5001`

### 4. Test It

Test with curl:

```bash
curl -X POST http://localhost:5001/validate \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, world!", "conversation_id": "test-123"}'
```

## API Endpoints

### POST /validate

Validate a message against all configured guardrails.

**Request:**
```json
{
  "message": "Text to validate",
  "conversation_id": "conv-12345",
  "user_id": "user-123",
  "conversation_history": [
    {"role": "user", "content": "Previous message 1"},
    {"role": "assistant", "content": "Previous response 1"},
    {"role": "user", "content": "Previous message 2"}
  ]
}
```

**Note:** `conversation_history` is optional. If provided, it enables LLM context-aware validation which can detect violations that only make sense in the context of the conversation (e.g., persistent evasion attempts, contextual toxicity).

**Response (Pass):**
```json
{
  "success": true,
  "valid": true,
  "conversation_id": "conv-12345",
  "validation_results": {
    "valid": true,
    "violations": [],
    "response_time_ms": 150
  },
  "event": {
    "event_type": "validation_passed",
    "severity": "info",
    "kafka_sent": false
  }
}
```

**Response (Fail):**
```json
{
  "success": true,
  "valid": false,
  "conversation_id": "conv-12345",
  "validation_results": {
    "valid": false,
    "violations": [...]
  },
  "event": {
    "event_type": "validation_failed",
    "severity": "high",
    "kafka_sent": true
  }
}
```

### GET /health

Check service health and configuration.

**Response:**
```json
{
  "status": "healthy",
  "service": "guardrail-service",
  "port": 5001,
  "kafka": {
    "status": "connected",
    "producer": "connected",
    "consumer": "running",
    "operator_actions_consumer": "running",
    "control_topic": "guardrail_control",
    "operator_actions_topic": "operator_actions"
  },
  "validator": {
    "pii_enabled": true,
    "toxicity_enabled": true,
    "compliance_enabled": true,
    "llm_context_check_enabled": true,
    "llm_available": true
  },
  "feedback": {
    "total_feedback": 5,
    "false_alarms": 3,
    "consumer_running": true,
    "topic": "guardrail_control"
  },
  "operator_actions": {
    "total_actions": 1,
    "actions_by_type": {
      "system_override": 1
    },
    "consumer_running": true,
    "topic": "operator_actions"
  }
}
```

## Project Structure

```
Guardrail-Strategy/
├── app.py                      # Flask application entry point
├── services/                   # Domain-organized services
│   ├── validation/            # Validation domain services
│   │   ├── guardrail_validator.py  # Guardrails-AI integration
│   │   └── __init__.py
│   └── infrastructure/        # Infrastructure services
│       └── kafka/             # Kafka infrastructure
│           ├── kafka_producer.py        # Kafka producer for events
│           ├── kafka_consumer.py        # Feedback consumer (guardrail_control)
│           ├── operator_actions_consumer.py # Minimal consumer that logs operator actions
│           ├── kafka_handler.py         # on_fail handler for validators
│           └── __init__.py
├── scripts/                   # Test and utility scripts
│   └── test_validation.py
├── core/                      # Core infrastructure (for future use)
├── requirements.txt           # Python dependencies
├── env.example                # Environment variables template
└── README.md                  # This file
```

## Key Components

### services/validation/guardrail_validator.py

Uses Guardrails-AI with validators from Guardrails Hub:
- **ToxicLanguage**: Detects toxic/inappropriate content
- **DetectPII**: Finds personally identifiable information
- **Compliance**: Custom regex patterns for compliance
- **LLM Context-Aware Check**: Uses OpenAI to analyze messages in the context of conversation history
  - Detects medical advice requests in context
  - Identifies persistent evasion attempts
  - Detects contextual toxicity that may not be obvious from a single message

### services/infrastructure/kafka/kafka_producer.py

Kafka producer for publishing guardrail events:
- Publishes violations to `guardrail_events` topic
- Resilient connection handling (graceful degradation)
- Automatic reconnection on failures

### services/infrastructure/kafka/kafka_consumer.py

Kafka consumer for receiving control feedback:
- Consumes from `guardrail_control` topic
- Processes false alarm feedback from dashboard
- Integrates with feedback learner for adaptive learning
- Runs in background thread
- Resilient connection handling (graceful degradation)

### services/infrastructure/kafka/operator_actions_consumer.py

Minimal Kafka consumer for operator evidence logging:
- Subscribes to `operator_actions` topic
- Logs each admin action for audit/evidence trail
- Exposes per-action statistics on `/health`
- Auto-reconnects and runs in its own background thread
- Performs no automated intervention (logging only)

### services/learning/feedback_learner.py

Adaptive learning system that improves guardrails based on operator feedback:
- **Tracks False Alarms**: Records when operators mark detections as false positives
- **Tracks True Positives**: Records confirmed valid detections
- **Rule Performance**: Calculates false alarm rates per rule/validator
- **Adaptive Thresholds**: Automatically adjusts detection thresholds based on feedback
- **Problematic Rule Detection**: Identifies rules with high false alarm rates
- **Persistent Storage**: Saves feedback data to JSON file for analysis
- **Threshold Multipliers**: Applies learned adjustments to validator thresholds

### services/infrastructure/kafka/kafka_handler.py

Custom `on_fail` handler that:
1. Formats violation details
2. Sends event to Kafka
3. Returns failure message to caller

Kafka producer that:
- Connects to Kafka broker
- Publishes guardrail events
- Handles connection errors gracefully

## Integration Example

Your AI Agent should call this service before sending messages:

```python
import requests

def send_message_safely(message, conversation_id):
    # Validate first
    response = requests.post(
        'http://localhost:5001/validate',
        json={
            'message': message,
            'conversation_id': conversation_id
        }
    )
    
    validation = response.json()
    
    if validation['valid']:
        # Safe to send
        send_to_user(message)
    else:
        # Blocked - send fallback
        send_to_user("I cannot respond to that.")
```

## Testing

You can test the service manually using curl or HTTP clients:

```bash
# Test with clean message
curl -X POST http://localhost:5001/validate \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, world!", "conversation_id": "test-123"}'

# Test with PII (should fail)
curl -X POST http://localhost:5001/validate \
  -H "Content-Type: application/json" \
  -d '{"message": "My email is test@example.com", "conversation_id": "test-456"}'

# Test with conversation history for LLM context-aware check
curl -X POST http://localhost:5001/validate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "But what if I just want to know if I should take aspirin?",
    "conversation_id": "test-789",
    "conversation_history": [
      {"role": "user", "content": "I have a headache"},
      {"role": "assistant", "content": "I cannot provide medical advice. Please consult a healthcare professional."},
      {"role": "user", "content": "Can you at least tell me what medicine helps?"}
    ]
  }'

# Test health check
curl http://localhost:5001/health
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker URL | `localhost:9092` |
| `KAFKA_OUTPUT_TOPIC` | Topic for guardrail events | `guardrail_events` |
| `GUARDRAIL_ENABLE_PII_DETECTION` | Enable PII detector | `True` |
| `GUARDRAIL_ENABLE_TOXICITY_CHECK` | Enable toxicity check | `True` |
| `GUARDRAIL_ENABLE_COMPLIANCE_CHECK` | Enable compliance check | `True` |
| `GUARDRAIL_ENABLE_LLM_CONTEXT_CHECK` | Enable LLM context-aware validation | `True` |
| `OPENAI_API_KEY` | OpenAI API key (required for LLM check) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo-1106` |
| `OPENAI_TEMPERATURE` | LLM temperature (0.0-1.0) | `0.3` |
| `PORT` | Flask port | `5001` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Troubleshooting

### "Guardrails-AI library not available"

Install Guardrails-AI and validators:

```bash
pip install guardrails-ai
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/detect_pii
```

### "Kafka connection failed"

Check Kafka is running:

```bash
# Docker
docker-compose up -d

# Or check Kafka status
kafka-broker-api-versions --bootstrap-server localhost:9092
```

### "Validators not installed"

**On Windows:** Use the PowerShell script to handle encoding issues:

```powershell
.\install-hub-validators.ps1
```

**On Linux/Mac or Manual Installation:**

Set UTF-8 encoding and install:

```powershell
# Windows PowerShell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/detect_pii
```

```bash
# Linux/Mac
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/detect_pii
```

**Note:** On Windows, if you see a `charmap codec can't encode character` error, it's due to Windows console encoding. The PowerShell script above handles this automatically.

## Requirements

- Python 3.8+
- Flask
- Guardrails-AI
- Kafka-Python
- Requests

See `requirements.txt` for complete list.

## License

Part of the NINA Guardrail Monitor system.


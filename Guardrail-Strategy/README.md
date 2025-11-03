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

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `env.example` to `.env`:

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

```bash
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
  "user_id": "user-123"
}
```

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
  "kafka": "connected",
  "validator": {
    "pii_enabled": true,
    "toxicity_enabled": true,
    "compliance_enabled": true
  }
}
```

## Project Structure

```
Guardrail-Strategy/
├── app.py              # Flask application entry point
├── validators.py       # Guardrails-AI integration
├── kafka_handler.py    # on_fail handler for validators
├── kafka_producer.py   # Kafka producer for events
├── requirements.txt    # Python dependencies
├── env.example         # Environment variables template
└── README.md           # This file
```

## Key Components

### validators.py

Uses Guardrails-AI with validators from Guardrails Hub:
- **ToxicLanguage**: Detects toxic/inappropriate content
- **DetectPII**: Finds personally identifiable information
- **Compliance**: Custom regex patterns for compliance

### kafka_handler.py

Custom `on_fail` handler that:
1. Formats violation details
2. Sends event to Kafka
3. Returns failure message to caller

### kafka_producer.py

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
| `OPENAI_API_KEY` | OpenAI API key (optional) | - |
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

Install from Guardrails Hub:

```bash
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/detect_pii
```

## Requirements

- Python 3.8+
- Flask
- Guardrails-AI
- Kafka-Python
- Requests

See `requirements.txt` for complete list.

## License

Part of the NINA Guardrail Monitor system.


# Guardrail Service

**System 2: The Guard** - A microservice for handling guardrail validation and LLM interaction.

This service runs on **port 5001** and acts as a Kafka Producer, publishing guardrail events.

## Architecture

- **Flask API** on port 5001
- **Kafka Producer** - Publishes guardrail events to Kafka
- **Guardrails-AI** integration for validation
- **OpenAI** integration for LLM interactions

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `env.example` to `.env` and configure your API keys.

### 4. Run the Service

```bash
python app.py
```

The service will start on `http://localhost:5001`

## Project Structure

```
Guardrail-Service/
├── app.py              # Flask application (port 5001)
├── validators.py       # Guardrail validation logic
├── kafka_producer.py   # Kafka producer for guardrail events
├── test_service.py     # Test script for the service
├── requirements.txt    # Python dependencies
├── env.example         # Environment variables template
├── .env               # Your configuration (create from env.example)
└── README.md          # This file
```

## Integration with OFH-Dashboard

This service communicates with the OFH-Dashboard backend via Kafka:
- Consumes: Conversation messages (optional, if needed)
- Produces: Guardrail events to `guardrail.conversation.{conversation_id}` topic

## API Endpoints

### Health Check
```
GET /health
```
Returns service status and configuration.

### Validate Message
```
POST /validate
Content-Type: application/json

{
  "message": "Text to validate",
  "conversation_id": "conv_12345",  // Optional
  "user_id": "user_123"              // Optional
}
```

### Batch Validation
```
POST /validate/batch
Content-Type: application/json

{
  "messages": ["message1", "message2", ...],
  "conversation_id": "conv_12345",  // Optional
  "user_id": "user_123"              // Optional
}
```

## Testing

Run the test script to verify the service is working:

```bash
python test_service.py
```

Make sure the service is running on port 5001 before running tests.

## Features

- **PII Detection**: Detects personally identifiable information (email, phone, SSN, credit cards, etc.)
- **Toxicity Check**: Identifies toxic, harmful, or inappropriate content
- **Compliance Check**: Validates compliance with rules (medical disclaimers, message length, etc.)
- **Kafka Integration**: Publishes guardrail events to Kafka for monitoring
- **OpenAI Integration**: Optional AI-powered validation (requires OPENAI_API_KEY)


# NINA Guardrail Monitor

A comprehensive real-time monitoring and validation system for AI chatbot conversations, specifically designed for healthcare applications. The system validates AI responses, detects violations (PII, toxicity, compliance issues), and provides a dashboard for admins to monitor and respond to guardrail events.

## 🏗️ Architecture Overview

The system consists of three main components working together:

```
┌─────────────────┐         ┌──────────────────────┐         ┌──────────────────┐
│   AI Agent     │────────▶│  Guardrail-Strategy │────────▶│   OFH Dashboard  │
│  (External)    │  HTTP   │    (Port 5001)       │  Kafka  │   (Port 5000)    │
│                │  POST    │                      │         │                  │
│                │          │  • Validates messages│         │  • Monitors      │
│                │          │  • Detects PII       │         │  • Visualizes    │
│                │          │  • Checks toxicity   │         │  • Responds      │
└────────────────┘          └──────────────────────┘         └──────────────────┘
          ▲                           │   ▲                           │
          │                           │   │                           │
          │           feedback        │   │ control feedback          │
          │        (`guardrail_control`)  │  (`guardrail_control`)    │
          │                           │   │                           │
          └──────── Kafka (`operator_actions`) ───────────────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │    Kafka     │
                              │   (Port 9092)│
                              └──────────────┘
```

### Components

1. **Guardrail-Strategy Service** (Port 5001)
   - Validates AI-generated messages in real-time
   - Detects PII (emails, phone numbers, SSNs)
   - Checks for toxic/inappropriate content
   - Enforces compliance rules
   - Publishes violations to Kafka

2. **OFH Dashboard** (Ports 3000/5000)
   - **Frontend** (React + Vite) - Port 3000
     - Real-time conversation monitoring
     - Analytics and reporting
     - Admin intervention tools
   - **Backend** (Flask) - Port 5000
     - Consumes Kafka events
     - RESTful API for frontend
     - WebSocket for real-time updates
     - PostgreSQL/SQLite database

3. **Kafka** (Port 9092)
   - Message queue for async communication
   - Topics: `guardrail_events`, `operator_actions`, `guardrail_control`, `dead_letter_queue`, *(optional)* `conversation_transcripts`

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (Python 3.14 recommended for Guardrail-Strategy)
- **Node.js 18+** (for frontend)
- **Kafka** (local or remote)
- **PostgreSQL** (optional, SQLite works for development)
- **Windows** (PowerShell) or **Linux/Mac**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "NINA Guardrail-Monitor"
```

### 2. Start Kafka

Make sure Kafka is running on `localhost:9092`. If you don't have Kafka installed:

```bash
# Using Docker (easiest)
docker run -d -p 9092:9092 apache/kafka:latest

# Or install Kafka locally and start:
# bin/zookeeper-server-start.sh config/zookeeper.properties
# bin/kafka-server-start.sh config/server.properties
```

### 3. Setup Guardrail-Strategy Service

```powershell
cd Guardrail-Strategy

# Setup virtual environment (Windows)
.\setup.bat

# Or manually:
py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure environment
copy env.example .env
# Edit .env with your Kafka and OpenAI settings

# Start the service
.\run.bat
# Or: python app.py
```

The service will start on **http://localhost:5001**

### 4. Setup OFH Dashboard

#### Backend Setup

```powershell
cd OFH-Dashboard\backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy env.example .env
# Edit .env with your database and Kafka settings

# Initialize database
python init_database.py

# Start the backend
.\run.bat
# Or: python app.py
```

The backend will start on **http://localhost:5000**

#### Frontend Setup

```powershell
cd OFH-Dashboard\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on **http://localhost:3000**

## 📋 Configuration

### Environment Variables

#### Guardrail-Strategy (`Guardrail-Strategy/.env`)

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_OUTPUT_TOPIC=guardrail_events
KAFKA_CONTROL_TOPIC=guardrail_control
# Optional: wildcard family if you partition conversations per topic
# KAFKA_OUTPUT_TOPIC_PATTERN=guardrail.conversation.*

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

#### OFH Dashboard Backend (`OFH-Dashboard/backend/.env`)

```bash
# Database
DATABASE_URL=sqlite:///nina_dashboard.db
# Or PostgreSQL: postgresql://user:password@localhost:5432/nina_dashboard

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=ofh-dashboard-consumer
KAFKA_TOPIC_GUARDRAIL=guardrail_events
KAFKA_TOPIC_OPERATOR=operator_actions
KAFKA_TOPIC_CONTROL=guardrail_control
# Optional: subscribe via regex (e.g. guardrail\.conversation\..+)
# KAFKA_TOPIC_GUARDRAIL_PATTERN=

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Security
JWT_SECRET_KEY=your-jwt-secret-here
JWT_EXPIRATION_HOURS=24

# Redis (optional, for rate limiting)
REDIS_URL=redis://localhost:6379/0
```

#### OFH Dashboard Frontend (`OFH-Dashboard/frontend/.env`)

```bash
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
```

## 🔄 Message Flow

### Complete Flow Example

1. **AI Agent** sends message to Guardrail-Strategy:
   ```bash
   POST http://localhost:5001/validate
   {
     "message": "Contact me at patient@example.com",
     "conversation_id": "conv-123",
     "user_id": "user-456"
   }
   ```

2. **Guardrail-Strategy** validates the message:
   - ✅ Detects PII (email)
   - ❌ Validation fails
   - 📨 Publishes event to Kafka topic `guardrail_events`

3. **OFH Dashboard** consumes from Kafka:
   - Receives guardrail event
   - Saves to database
   - Updates frontend via WebSocket
   - Admin sees alert in dashboard

4. **Admin** can respond:
   - Acknowledge, escalate, resolve, or override the event
   - Dashboard publishes commands to the AI agent (`operator_actions` topic)
   - Dashboard mirrors operator feedback to `guardrail_control` for guardrail learning

5. **Guardrail-Strategy** consumes feedback:
   - Updates adaptive thresholds via `FeedbackLearner`
   - Logs operator corrections for telemetry

6. *(Optional)* **Agent pushes transcript updates**:
   - Use `POST /api/transcripts` (or publish to `conversation_transcripts`)
   - Dashboard stores `ChatMessage` entries so moderators see full context

## 🧪 Testing

### Test Full Flow

Run the comprehensive test script that simulates the complete flow:

```powershell
cd OFH-Dashboard\backend\scripts
python test_full_flow.py
```

Or use PowerShell:

```powershell
.\test_full_flow.ps1
```

This test:
- Sends a synthetic guardrail event into Kafka
- Waits for the dashboard backend to persist it
- Emits an operator action (mirrored to the AI agent topic)
- Optionally verifies guardrail feedback metrics (if the strategy is running)

### Test Individual Components

#### Test Guardrail-Strategy

```powershell
cd Guardrail-Strategy\scripts
python test_validation.py
```

Or send manual HTTP requests:

```powershell
$body = @{
    message = "Contact me at test@example.com"
    conversation_id = "test-123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/validate" `
    -Method Post -Body $body -ContentType "application/json"
```

#### Test Bad Messages

```powershell
cd OFH-Dashboard\backend\scripts
.\test_bad_kafka_messages.ps1
```

This tests error handling for malformed Kafka messages.

#### External Alerting Stub (optional)

To exercise the alerting integration end to end:

```powershell
# Terminal 1 – start the alerting stub (consumes guardrail events and writes to Postgres)
cd OFH-Dashboard\backend\scripts
python run_alerting_stub.py

# Terminal 2 – run the integration smoke test (publishes events + operator feedback)
python run_integration_check.py
```

After both scripts report success, refresh the Security → Alerting tab on the dashboard to confirm the new alerts appear.

## 📚 API Documentation

### Guardrail-Strategy API

**Base URL:** `http://localhost:5001`

#### POST `/validate`

Validates a message against guardrails.

**Request:**
```json
{
  "message": "The message to validate",
  "conversation_id": "conv-123",
  "user_id": "user-456" // optional
}
```

**Response:**
```json
{
  "success": true,
  "valid": false,
  "conversation_id": "conv-123",
  "validation_results": {
    "valid": false,
    "violations": [
      {
        "type": "validation_failed",
        "severity": "medium",
        "details": {
          "error_message": "BLOCKED: Contains PII",
          "message_preview": "..."
        }
      }
    ]
  },
  "event": {
    "event_type": "validation_failed",
    "severity": "high",
    "kafka_sent": true
  }
}
```

#### GET `/health`

Health check endpoint.

### OFH Dashboard API

**Base URL:** `http://localhost:5000`

#### Authentication

Most endpoints require JWT authentication. Login first:

```bash
POST /api/auth/login
{
  "username": "admin",
  "password": "password"
}
```

Returns a JWT token to use in subsequent requests:
```
Authorization: Bearer <token>
```

#### Key Endpoints

- `GET /api/conversations` - List all conversations
- `GET /api/conversations/:id` - Get conversation details
- `GET /api/alerts` - List guardrail events
- `GET /api/analytics/overview` - Dashboard analytics
- `GET /api/analytics/notifications` - Notification analytics

See `OFH-Dashboard/API_DOCUMENTATION.md` for complete API documentation.

## 🗄️ Database Schema

### Key Tables

- **conversation_sessions** - Conversation metadata
- **guardrail_events** - Guardrail violations and events
- **operator_actions** - Admin interventions
- **users** - System users (admin role)
- **chat_messages** - Conversation messages

See `OFH-Dashboard/backend/models/` for complete schema definitions.

## 🔐 Security

### User Roles

- **Admin** - Full system access, user management, configuration, monitoring, and alert management

### Authentication

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)

### Security Features

- Rate limiting on API endpoints
- CORS protection
- SQL injection prevention (SQLAlchemy ORM)
- Input validation and sanitization
- Audit logging

See `OFH-Dashboard/SECURITY_HARDENING.md` for detailed security information.

## 📊 Monitoring & Analytics

The dashboard provides:

- **Real-time Conversation Monitoring**
  - Active conversations count
  - Risk level indicators
  - Guardrail violations

- **Analytics Dashboard**
  - Alert statistics
  - Response time metrics
  - Notification analytics
  - Conversation statistics

- **Security Dashboard**
  - User activity
  - Failed login attempts
  - System health

## 🐛 Troubleshooting

### Kafka Connection Issues

If the Kafka consumer isn't connecting:

1. Verify Kafka is running:
   ```bash
   # Check if Kafka is accessible
   telnet localhost 9092
   ```

2. Check environment variables:
   ```bash
   # Should match your Kafka server
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   ```

3. Check logs:
   - Guardrail-Strategy: Look for Kafka producer errors
   - OFH Dashboard backend: Look for consumer connection errors

See `OFH-Dashboard/backend/KAFKA_CONNECTION_ISSUES.md` for detailed troubleshooting.

### Database Issues

If you see `NotNullViolation` errors:

1. Run migrations:
   ```powershell
   cd OFH-Dashboard\backend\migrations
   python 20251104_add_category_column.py
   # Run other migrations as needed
   ```

2. Check model definitions match database schema

### Frontend 500 Errors

If the frontend shows 500 errors:

1. Check backend logs for specific error messages
2. Verify database connection
3. Check API authentication tokens
4. Restart backend server after code changes

### Active Conversations Showing 0

This was a status mapping issue (now fixed). If you still see it:

1. Restart the backend server
2. Verify conversations have status `ACTIVE` in database
3. Frontend expects `IN_PROGRESS` (mapping is handled in API)

## 📁 Project Structure

```
NINA Guardrail-Monitor/
├── Guardrail-Strategy/          # Message validation service
│   ├── app.py                   # Flask application
│   ├── validators.py            # Guardrail validators
│   ├── kafka_producer.py        # Kafka event publisher
│   ├── requirements.txt
│   └── scripts/                 # Test scripts
│
├── OFH-Dashboard/
│   ├── backend/                 # Flask backend (Domain-Driven Architecture)
│   │   ├── app.py              # Main application
│   │   ├── api/                # REST API routes
│   │   ├── models/             # Database models (domain-organized)
│   │   │   └── notifications/  # Notification domain models
│   │   ├── services/           # Business logic (domain-organized)
│   │   │   ├── notifications/  # Notification domain services
│   │   │   └── infrastructure/ # Infrastructure services
│   │   │       └── kafka/      # Kafka services
│   │   ├── repositories/       # Data access layer (domain-organized)
│   │   │   └── notifications/  # Notification domain repositories
│   │   ├── schemas/            # JSON schemas
│   │   ├── scripts/            # Utility scripts
│   │   │   ├── management/     # Management scripts
│   │   │   ├── testing/        # Test scripts
│   │   │   └── utils/          # Utility scripts
│   │   └── docs/               # Documentation
│   │
│   └── frontend/               # React frontend (Domain-Organized)
│       ├── src/
│       │   ├── components/     # Domain-organized components
│       │   │   ├── conversations/
│       │   │   ├── notifications/
│       │   │   ├── analytics/
│       │   │   ├── ui/
│       │   │   └── common/
│       │   ├── pages/         # Page components
│       │   ├── services/      # Domain-organized services
│       │   │   ├── api/
│       │   │   └── notifications/
│       │   └── contexts/      # React contexts
│       └── package.json
│
├── message_specs.md            # Kafka message specifications
└── README.md                   # This file
```

## 🚢 Deployment

### Production Checklist

See `OFH-Dashboard/PRODUCTION_CHECKLIST.md` for complete deployment guide.

Key considerations:

- Use PostgreSQL instead of SQLite
- Set `FLASK_ENV=production`
- Configure proper CORS origins
- Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
- Enable HTTPS
- Configure proper Kafka cluster
- Set up monitoring and logging
- Database backups

### Docker Deployment

Docker Compose configuration is available:

```bash
cd OFH-Dashboard
docker-compose up -d
```


## 🎯 Key Features

✅ **Real-time Validation** - Messages validated before reaching users  
✅ **PII Detection** - Automatically detects emails, phone numbers, SSNs  
✅ **Toxicity Detection** - Identifies inappropriate or harmful content  
✅ **Compliance Checking** - Enforces healthcare compliance rules  
✅ **Real-time Dashboard** - Live monitoring of conversations  
✅ **Admin Intervention** - Tools for human oversight  
✅ **Analytics** - Comprehensive reporting and statistics  
✅ **Admin Access Control** - Admin role for full system access  
✅ **Audit Logging** - Complete audit trail  
✅ **Kafka Integration** - Scalable message queue architecture  
✅ **Adaptive Guardrail Learning** - Operator feedback feeds `guardrail_control` for continuous tuning  
✅ **External Alerting Stub** - Optional consumer that mirrors alerts to an external Postgres store  
✅ **Resilient Connectivity** - Circuit breakers around Kafka and Guardrail Strategy requests prevent cascading failures  

---

**Version:** 1.0  
**Last Updated:** November 2025


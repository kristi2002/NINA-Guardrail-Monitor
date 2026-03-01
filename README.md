# Guardrail Monitor

A comprehensive real-time monitoring and validation system for AI chatbot conversations, specifically designed for healthcare applications. The system validates AI responses, detects violations (PII, toxicity, compliance issues), and provides a dashboard for admins to monitor and respond to guardrail events.

## 🏗️ Architecture Overview

The system consists of three main components working together:

```
┌─────────────────┐         ┌──────────────────────┐         ┌──────────────────┐
│   AI Agent     │────────▶│  Guardrail-Strategy │────────▶ │ Guardrail Dashboard │
│  (External)    │  HTTP   │    (Port 5001)       │  Kafka   │   (Port 5000)    │
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

2. **Guardrail Dashboard** (Ports 3000/5000)
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

### Option 1: Docker Setup (Recommended) 🐳

The easiest way to get started is using Docker Compose, which sets up all services automatically.

#### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine + Docker Compose** (Linux)

> **Note:** If your dashboard folder has a different name, use that path in the commands below instead of `Guardrail-Monitor-Dashboard`.

#### Setup Steps

1. **Clone the Repository**

```bash
git clone <repository-url>
cd "Guardrail-Monitor"
```

2. **Initialize and Start All Services**

**Windows (PowerShell):**
```powershell
.\docker-init.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x docker-init.sh
./docker-init.sh
```

**Or manually:**
```bash
docker compose build
docker compose up -d
```

3. **Access the Services**

Once all services are running:

- **Guardrail-Strategy API**: http://localhost:5001
- **Guardrail Dashboard API**: http://localhost:5000
- **Guardrail Dashboard UI**: http://localhost:3001
- **Kafka**: localhost:9092
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

**View logs:**
```bash
docker compose logs -f
```

**Stop services:**
```bash
docker compose down
```

📖 **For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md)**

---

### Option 2: Manual Setup (Development)

If you prefer to run services manually for development:

#### Prerequisites

- **Python 3.11+** (Python 3.12 recommended for Guardrail-Strategy)
- **Node.js 18+** (for frontend)
- **Kafka** (local or remote)
- **PostgreSQL** (optional, SQLite works for development)
- **Windows** (PowerShell) or **Linux/Mac**

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Guardrail-Monitor"
```

#### 2. Start Kafka

**Option A: Using Docker (Easiest)**

```bash
# Start only Kafka and Zookeeper
docker compose up -d zookeeper kafka
```

**Option B: Manual Setup**

For manual Kafka setup, you'll need to install and configure Kafka, Zookeeper, PostgreSQL, and Redis separately. See the Docker setup for reference configuration.

#### 3. Setup Guardrail-Strategy Service

```powershell
cd Guardrail-Strategy

# Setup virtual environment (Windows)
.\setup.bat

# Or manually:
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure environment
copy env.example .env
# Edit .env with your Kafka and OpenAI settings

# Start the service
python app.py
```

The service will start on **http://localhost:5001**

#### 4. Setup Guardrail Dashboard

**Backend Setup:**

```powershell
cd Guardrail-Monitor-Dashboard\backend

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
python app.py
```

The backend will start on **http://localhost:5000**

**Frontend Setup:**

```powershell
cd Guardrail-Monitor-Dashboard\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on **http://localhost:3000**

## 📋 Configuration

### Environment Variables

> **Note for Docker users**: When using Docker, services communicate using Docker service names (e.g., `kafka:9093`). From your host machine, use `localhost:9092` for Kafka. The Docker Compose setup handles networking automatically.

#### Guardrail-Strategy (`Guardrail-Strategy/.env`)

**For Docker:**
```bash
# Kafka Configuration (use Docker service name)
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
```

**For Manual Setup:**
```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

**Common Settings:**
```bash
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

#### Guardrail Dashboard Backend (`Guardrail-Monitor-Dashboard/backend/.env`)

**For Docker:**
```bash
# Database (use Docker service name)
DATABASE_URL=postgresql://postgres_user:postgres_pass@postgres:5432/postgres_db

# Kafka (use Docker service name)
KAFKA_BOOTSTRAP_SERVERS=kafka:9093

# Redis (use Docker service name)
REDIS_URL=redis://redis:6379/0
```

**For Manual Setup:**
```bash
# Database
DATABASE_URL=sqlite:///guardrail_dashboard.db
# Or PostgreSQL: postgresql://user:password@localhost:5432/guardrail_dashboard

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379/0
```

**Common Settings:**
```bash
KAFKA_GROUP_ID=guardrail-monitor-consumer
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
```

#### Guardrail Dashboard Frontend (`Guardrail-Monitor-Dashboard/frontend/.env`)

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

3. **Guardrail Dashboard** consumes from Kafka:
   - Receives guardrail event
   - Saves to database
   - Updates frontend via WebSocket
   - Admin sees alert in dashboard

4. **Admin** can respond:
   - Acknowledge, escalate, resolve, or override the event
   - Dashboard publishes commands to `operator_actions` topic (for AI Agent and Guardrail-Strategy)
   - Dashboard mirrors operator feedback to `guardrail_control` for guardrail learning

5. **Guardrail-Strategy** consumes:
   - **From `guardrail_control`**: Updates adaptive thresholds via `FeedbackLearner`
   - **From `operator_actions`**: Logs operator actions for evidence tracking

6. *(Optional)* **Agent pushes transcript updates**:
   - Use `POST /api/transcripts` (or publish to `conversation_transcripts`)
   - Dashboard stores `ChatMessage` entries so moderators see full context

## 🧪 Testing

### Test Full Flow

Run the comprehensive test script that simulates the complete flow:

```powershell
cd Guardrail-Monitor-Dashboard\backend\scripts
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
cd Guardrail-Monitor-Dashboard\backend\scripts
.\test_bad_kafka_messages.ps1
```

This tests error handling for malformed Kafka messages.

#### External Alerting Stub (optional)

To exercise the alerting integration end to end:

```powershell
# Terminal 1 – start the alerting stub (consumes guardrail events and writes to Postgres)
cd Guardrail-Monitor-Dashboard\backend\scripts
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

### Guardrail Dashboard API

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

See `Guardrail-Monitor-Dashboard/API_DOCUMENTATION.md` for complete API documentation.

## 🗄️ Database Schema

### Key Tables

- **conversation_sessions** - Conversation metadata
- **guardrail_events** - Guardrail violations and events
- **operator_actions** - Admin interventions
- **users** - System users (admin role)
- **chat_messages** - Conversation messages

See `Guardrail-Monitor-Dashboard/backend/models/` for complete schema definitions.

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

See `Guardrail-Monitor-Dashboard/SECURITY_HARDENING.md` for detailed security information.

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

**For Docker Setup:**

If using Docker, Kafka runs in a container. Check service status:

```powershell
docker compose ps kafka
docker compose logs kafka
```

**For Manual Setup:**

If the Kafka consumer isn't connecting:

1. **Verify Kafka is running**:
   ```bash
   # Check Kafka status
   bin/kafka-topics.sh --list --bootstrap-server localhost:9092
   ```

2. **Check environment variables**:
   - Ensure `KAFKA_BOOTSTRAP_SERVERS` is correctly configured
   - For Docker: Use service name `kafka:9093`
   - For local: Use `localhost:9092`

3. **Check logs**:
   - Guardrail-Strategy: Look for Kafka producer errors
   - Guardrail Dashboard backend: Look for consumer connection errors

4. **Common issues**:
   - Kafka not started → Start Zookeeper first, then Kafka
   - Wrong bootstrap server → Verify connection string
   - Network issues → Check firewall and port accessibility

### Database Issues

If you see `NotNullViolation` errors:

1. Run migrations:
   ```powershell
   cd Guardrail-Monitor-Dashboard\backend\migrations
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
Guardrail-Monitor/
├── Guardrail-Strategy/          # Message validation service
│   ├── app.py                   # Flask application
│   ├── validators.py            # Guardrail validators
│   ├── kafka_producer.py        # Kafka event publisher
│   ├── requirements.txt
│   └── scripts/                 # Test scripts
│
├── Guardrail-Monitor-Dashboard/
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

See `Guardrail-Monitor-Dashboard/PRODUCTION_CHECKLIST.md` for complete deployment guide.

Key considerations:

- Use PostgreSQL instead of SQLite
- Set `FLASK_ENV=production`
- **Configure proper CORS origins** (see CORS Configuration below)
- Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
- Enable HTTPS
- Configure proper Kafka cluster
- Set up monitoring and logging
- Database backups

#### CORS Configuration

**⚠️ SECURITY WARNING**: Never use wildcard (`*`) for CORS in production!

**Development:**
```env
CORS_ORIGINS=http://localhost:3001,http://localhost:3000
```

**Production:**
```env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

The application will:
- ✅ Default to `http://localhost:3001,http://localhost:3000` for development
- ⚠️  Warn if wildcard is used in production mode
- ✅ Validate CORS configuration on startup

### Docker Deployment

Docker Compose configuration is available at the root level:

```bash
# From project root
docker compose up -d
```

Or use the initialization script:

**Windows:**
```powershell
.\docker-init.ps1
```

**Linux/Mac:**
```bash
./docker-init.sh
```

📖 **See [DOCKER_SETUP.md](DOCKER_SETUP.md) for complete Docker setup guide**


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


# Guardrail Monitor Dashboard

A comprehensive real-time monitoring and analytics platform for the guardrail system. This dashboard provides advanced insights into conversation monitoring, security events, and system performance with enterprise-grade features.

## 🎯 Project Overview

The Guardrail Monitor Dashboard is a full-stack monitoring solution that provides real-time insights into guardrail performance, security metrics, and system analytics. It features a modern React frontend with comprehensive analytics, security monitoring, and real-time data visualization capabilities.

### Technology Stack

**Frontend**:
- React 18 + Vite + Recharts + Socket.IO
- Custom hooks for state management
- Context API for global state
- Error boundaries for fault tolerance

**Backend**:
- Python 3.12 + Flask + SQLAlchemy
- Clean Architecture with Repository Pattern
- SQLite (development) / PostgreSQL (production)
- WebSocket (Flask-SocketIO) for real-time updates
- Kafka integration for event streaming

**Security & Authentication**:
- JWT authentication
- Admin role with full system access
- Protected routes and middleware

**Testing & Quality**:
- Jest + React Testing Library
- ESLint + Prettier
- Comprehensive error handling
- Logging and monitoring

## 📁 Project Structure

```
Guardrail-Monitor-Dashboard/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # Domain-organized components
│   │   │   ├── conversations/  # Conversation domain components
│   │   │   │   ├── ConversationCard.jsx
│   │   │   │   ├── ConversationDetailModal.jsx
│   │   │   │   ├── ConversationList.jsx
│   │   │   │   └── ...
│   │   │   ├── notifications/ # Notification domain components
│   │   │   │   ├── NotificationCenter.jsx
│   │   │   │   └── NotificationPreferences.jsx
│   │   │   ├── analytics/     # Analytics domain components
│   │   │   │   ├── AlertCard.jsx
│   │   │   │   ├── GuardrailChart.jsx
│   │   │   │   └── MetricCard.jsx
│   │   │   ├── ui/            # Reusable UI components
│   │   │   │   ├── CustomSelect.jsx
│   │   │   │   ├── DataTable.jsx
│   │   │   │   └── LoadingSkeleton.jsx
│   │   │   └── common/        # Shared/common components
│   │   │       ├── ErrorBoundary.jsx
│   │   │       ├── ProtectedRoute.jsx
│   │   │       └── UserProfile.jsx
│   │   ├── pages/              # Dashboard pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Analytics.jsx
│   │   │   ├── Security.jsx
│   │   │   └── Login.jsx
│   │   ├── contexts/           # React contexts
│   │   │   ├── AuthContext.jsx
│   │   │   └── NotificationContext.jsx
│   │   ├── services/           # Domain-organized services
│   │   │   ├── api/           # API services
│   │   │   │   ├── authService.js
│   │   │   │   ├── dataService.js
│   │   │   │   └── messagingService.js
│   │   │   └── notifications/ # Notification services
│   │   │       └── notificationService.js
│   │   ├── styles/            # Global styles
│   │   ├── translations/      # i18n files
│   │   └── utils/             # Utility functions
│   │       └── eventTypeMapper.js
│   └── package.json
│
├── backend/                     # Python Flask API (Domain-Driven Clean Architecture)
│   ├── app.py                  # Main Flask application entry point
│   ├── config.py               # Configuration management
│   │
│   ├── api/                    # Presentation Layer
│   │   ├── routes/             # API endpoints (Blueprints)
│   │   │   ├── alerts.py
│   │   │   ├── analytics.py
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── escalations.py
│   │   │   ├── metrics.py
│   │   │   ├── notifications.py
│   │   │   ├── notifications_enhanced.py
│   │   │   └── security.py
│   │   └── middleware/         # Cross-cutting concerns
│   │       ├── auth_middleware.py
│   │       └── error_handler.py
│   │
│   ├── services/               # Business Logic Layer (Domain-Organized)
│   │   ├── notifications/      # Notification domain services
│   │   │   ├── notification_service.py
│   │   │   ├── enhanced_notification_service.py
│   │   │   ├── notification_orchestrator.py
│   │   │   └── ...
│   │   ├── infrastructure/     # Infrastructure services
│   │   │   └── kafka/         # Kafka infrastructure
│   │   │       ├── kafka_consumer.py
│   │   │       ├── kafka_producer.py
│   │   │       └── kafka_integration_service.py
│   │   ├── alert_service.py
│   │   ├── conversation_service.py
│   │   ├── user_service.py
│   │   ├── analytics_service.py
│   │   ├── security_service.py
│   │   ├── escalation_service.py
│   │   ├── error_alerting_service.py
│   │   ├── dlq_management_service.py
│   │   ├── system_monitor.py
│   │   └── database_service.py
│   │
│   ├── repositories/           # Data Access Layer (Domain-Organized)
│   │   ├── notifications/      # Notification domain repositories
│   │   │   ├── notification_repository.py
│   │   │   ├── notification_preference_repository.py
│   │   │   └── ...
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── conversation_repository.py
│   │   ├── guardrail_event_repository.py
│   │   ├── chat_message_repository.py
│   │   └── operator_action_repository.py
│   │
│   ├── models/                 # Data Layer (Domain-Organized)
│   │   ├── notifications/      # Notification domain models
│   │   │   ├── notification.py
│   │   │   ├── notification_preference.py
│   │   │   └── ...
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── guardrail_event.py
│   │   ├── chat_message.py
│   │   └── operator_action.py
│   │
│   ├── core/                   # Core Infrastructure
│   │   └── database.py         # Database manager
│   │
│   ├── schemas/                 # JSON schemas
│   │   ├── guardrail_event.schema.json
│   │   ├── operator_action.schema.json
│   │   └── control_feedback.schema.json
│   │
│   ├── scripts/                # Utility scripts
│   │   ├── management/         # Management scripts
│   │   ├── testing/            # Test scripts
│   │   └── utils/              # Utility scripts
│   │
│   ├── docs/                   # Documentation
│   │
│   ├── migrations/            # Database migrations
│   │
│   ├── .env                    # Environment variables (not in repo)
│   ├── requirements.txt
│   └── venv/                   # Virtual environment (not in repo)
│
├── ARCHITECTURE.md             # Architecture documentation
├── API_DOCUMENTATION.md        # Complete API documentation
├── USER_DOCUMENTATION.md       # User guide
└── README.md                   # This file
```

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v16 or higher) ✅ Installed: v22.12.0
- **Python** (v3.8 or higher) ✅ Installed: v3.12.6
- **PostgreSQL** (v12 or higher) for production
- **Kafka** (running in WSL 2 Ubuntu, for real-time streaming)

### Installation & Setup

#### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (PostgreSQL only)
python init_database.py

# Run the backend server
python app.py
```

The backend will start on `http://localhost:5000`

**Note**: For SQLite development, tables are created automatically. For PostgreSQL production, run `init_database.py` first to create tables and initial users.

#### 2. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will start on `http://localhost:3001`

#### 3. Start Kafka (WSL 2)

**Important**: Kafka runs in WSL 2 (Ubuntu). See [KAFKA_SETUP.md](KAFKA_SETUP.md) for detailed instructions.

**Quick Start**:
```bash
# In Ubuntu terminal
cd kafka_2.13-3.6.1

# Check IP (update .env if changed)
hostname -I

# Start Zookeeper (Terminal 1)
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka (Terminal 2)
bin/kafka-server-start.sh config/server.properties
```

> **Note**: WSL 2 IP changes on restart. Update `.env` and `server.properties` if IP changes.

#### 4. Environment Configuration

The application uses environment variables for configuration. Copy the example file to create your `.env` file:

```bash
# Backend Configuration
cd backend

# Copy example environment file
cp env.example .env

# Edit the .env file with your configuration
nano .env  # or use your preferred editor
```

**Development Configuration** (SQLite):
```env
DATABASE_URL=sqlite:///guardrail_dashboard.db
SECRET_KEY=dev-secret-key-change-in-production-2024
APP_DEBUG=True
```

**Production Configuration** (PostgreSQL):
```env
DATABASE_URL=postgresql://postgres_user:postgres_pass@localhost:5432/postgres_db
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters-long
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-minimum-32-characters-long
APP_DEBUG=False
ADMIN_PASSWORD=your_secure_admin_password
```

📖 **For complete production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

**Note**: The `.env` file is git-ignored for security. Never commit credentials!

## 🎨 Features

### ✅ **Core Features (Implemented)**

#### **📊 Main Dashboard**
- **Real-time Metrics**: Live conversation counts, alert status, system health
- **Active Conversations**: Real-time conversation monitoring
- **Recent Alerts**: Latest guardrail events and notifications
- **System Status**: Kafka connection, database status, service health
- **WebSocket Integration**: Live updates without page refresh

#### **📈 Analytics Dashboard**
- **Overview Tab**: Key metrics, performance trends, system health
- **Notifications Tab**: Delivery rates, time series data, failure analysis
- **Admin Performance Tab**: Admin performance metrics, workload distribution, quality scores
- **Alert Trends Tab**: Alert types, geographic analysis, trend analysis
- **Response Times Tab**: SLA compliance, average times, performance trends
- **Escalations Tab**: Escalation rates, auto-escalation, resolution times
- **Time Range Filtering**: 24 hours, 7 days, 30 days
- **Data Export**: JSON export with custom time ranges

#### **🛡️ Security Dashboard** (Admin Access)
- **Overview Tab**: Security score, threats blocked, system status, recent events
- **Threats Tab**: Threat detection, types, geographic analysis, response times
- **Access Control Tab**: Authentication metrics, user activity, MFA adoption
- **Compliance Tab**: GDPR, HIPAA, SOC2, ISO27001 compliance tracking
- **Incidents Tab**: Incident management, resolution metrics, escalation patterns
- **Real-time Monitoring**: Live security event tracking

#### **🔐 Authentication & Security**
- **JWT Authentication**: Secure token-based authentication
- **Admin Access Control**: Admin role with full system access
- **Protected Routes**: Route-level permission checking
- **Session Management**: Automatic token refresh and validation

#### **⚡ Real-time Features**
- **WebSocket Connections**: Live data updates
- **Auto-refresh**: Automatic data refresh every 5 minutes
- **Live Notifications**: Real-time alert notifications
- **Status Monitoring**: Live system health monitoring

### ✅ **Advanced Features (Implemented)**

- **Kafka Integration**: Real-time data streaming from guardrail system ✅
- **Dead Letter Queue (DLQ)**: Failed message handling and recovery ✅
- **Auto-Escalation**: Automatic alert escalation based on rules ✅
- **Multi-Channel Notifications**: SMS, Email, Slack, Teams integration ✅
- **System Monitoring**: Real-time health checks and metrics ✅
- **Clean Architecture**: Repository pattern with separation of concerns ✅

### 🚧 **Planned Features**

- **Machine Learning**: AI-powered threat detection and anomaly detection
- **Advanced Reporting**: PDF/Excel report generation
- **Mobile App**: React Native mobile application
- **API Rate Limiting**: Production-grade rate limiting
- **Caching**: Redis-based caching for performance

## 🔌 API Endpoints

### **Analytics Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/overview` | GET | Dashboard overview metrics |
| `/api/analytics/notifications` | GET | Notification analytics |
| `/api/analytics/admin-performance` | GET | Admin performance data |
| `/api/analytics/alert-trends` | GET | Alert trend analysis |
| `/api/analytics/response-times` | GET | Response time metrics |
| `/api/analytics/escalations` | GET | Escalation analytics |
| `/api/analytics/export` | POST | Export analytics data |

### **Security Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/security/overview` | GET | Security overview metrics |
| `/api/security/threats` | GET | Threat detection data |
| `/api/security/access` | GET | Access control metrics |
| `/api/security/compliance` | GET | Compliance status |
| `/api/security/incidents` | GET | Security incidents |

### **Authentication Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User authentication |
| `/api/auth/validate` | GET | Token validation |

### **System Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics` | GET | System metrics |
| `/api/alerts` | GET | Active alerts |
| `/api/conversations` | GET | Active conversations |

## 🧪 Testing & Quality

### **Testing Commands**
```bash
# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### **Code Quality Commands**
```bash
# Lint code
npm run lint

# Fix linting errors
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

### **Test Coverage**
- **ErrorBoundary**: Error handling and recovery
- **Analytics**: Data fetching and error states
- **Security**: Security dashboard functionality
- **Authentication**: Login and token validation

## 📊 Understanding the Dashboard

### **Metrics Explained**

#### **Main Dashboard**
- **Total Conversations**: Number of active monitoring sessions
- **Active Alerts**: Current unresolved guardrail events
- **Resolved Alerts**: Successfully handled events
- **Average Response Time**: Mean time to respond to alerts

#### **Analytics Dashboard**
- **Delivery Rate**: Success rate of notifications
- **Admin Performance**: Response times and efficiency metrics
- **Alert Trends**: Patterns in guardrail violations
- **Escalation Rates**: Percentage of alerts requiring escalation

#### **Security Dashboard**
- **Security Score**: Overall security posture rating (0-100)
- **Threats Blocked**: Number of security threats prevented
- **Compliance Score**: Adherence to regulatory requirements
- **Incident Response**: Security incident resolution metrics

### **Guardrail Types**

1. **Content Safety**: Prevents harmful or inappropriate content
2. **PII Detection**: Identifies and protects personal information
3. **Toxicity Filter**: Blocks toxic or offensive language
4. **Response Quality**: Ensures responses meet quality standards
5. **Medical Safety**: Prevents medical misinformation
6. **Privacy Protection**: Ensures patient privacy compliance

## 🛠️ Development

### **Development Commands**

```bash
# Frontend development
npm run dev              # Start development server
npm run build            # Build for production
npm run preview          # Preview production build

# Backend development
python app.py            # Start Flask server with clean architecture

# Database operations
python -c "from core.database import init_database; init_database()"  # Initialize DB
```

### **Code Quality Standards**

- **ESLint**: Comprehensive linting rules for React and JavaScript
- **Prettier**: Consistent code formatting
- **Error Boundaries**: Graceful error handling
- **TypeScript Ready**: Prepared for TypeScript migration
- **Accessibility**: WCAG compliance for screen readers

### **Architecture Patterns**

**Frontend**:
- **Component-based**: Modular React components
- **Context API**: Global state management
- **Custom Hooks**: Reusable logic
- **Error Boundaries**: Fault tolerance

**Backend**:
- **Clean Architecture**: Clear separation of concerns (Routes → Services → Repositories → Models)
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation
- **Factory Pattern**: Database session management
- **Decorator Pattern**: Authentication middleware
- **Observer Pattern**: Event-driven updates via Kafka

📚 **See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation**

## 🚀 Deployment

### **Production Setup**

1. **Environment Variables**:
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/db"
   export JWT_SECRET="your-secret-key"
   export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
   ```

2. **Database Migration**:
   ```bash
   python app.py  # Tables are created automatically on first run
   # Or manually:
   python -c "from core.database import init_database; db = init_database(); db.create_tables()"
   ```

3. **Frontend Build**:
   ```bash
   npm run build
   ```

4. **Production Server**:
   ```bash
   python app.py
   # Or with gunicorn for production:
   gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
   ```

### **Docker Deployment** (Coming Soon)
```bash
# Build and run with Docker
docker-compose up -d
```

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Clean architecture documentation with layers, patterns, and design principles
- **[API Documentation](API_DOCUMENTATION.md)**: Complete API reference (if available)
- **[User Documentation](USER_DOCUMENTATION.md)**: User guide and features (if available)
- **Code Comments**: Comprehensive inline documentation throughout the codebase
- **README**: This file with setup and usage instructions

## 🏗️ Architecture Highlights

The application follows **Clean Architecture** principles with a clear separation of concerns:

```
API Routes (Presentation) → Services (Business Logic) → Repositories (Data Access) → Models (Database)
```

**Key Benefits**:
- ✅ **Testability**: Each layer can be tested independently
- ✅ **Maintainability**: Clear boundaries make code easy to understand
- ✅ **Scalability**: Add new features without affecting existing code
- ✅ **Reusability**: Repositories and services are reusable across the application
- ✅ **Flexibility**: Easy to swap implementations (e.g., database, external services)

**Learn More**: Check out [ARCHITECTURE.md](ARCHITECTURE.md) for detailed information about the architecture, design patterns, and best practices used in this project.

## 🎓 Learning Resources

### **Key Concepts**

#### **React Patterns**
- **Components**: Reusable UI pieces (MetricCard, ErrorBoundary)
- **Hooks**: State management (useState, useEffect, useContext)
- **Context**: Global state (AuthContext, NotificationContext)
- **Error Boundaries**: Fault tolerance and recovery

#### **Backend Patterns**
- **REST API**: RESTful endpoint design
- **Database ORM**: SQLAlchemy for database operations
- **Authentication**: JWT-based security
- **Real-time**: WebSocket connections

#### **Architecture Concepts**
- **Microservices**: Modular service design
- **Event Streaming**: Kafka for real-time data
- **Security**: Role-based access control
- **Monitoring**: Comprehensive system observability

## 🛠️ Troubleshooting

### **Common Issues**

#### **Frontend Issues**
- **"Failed to load data"**: Check backend is running on port 5000
- **Authentication errors**: Verify JWT token and user permissions
- **WebSocket connection failed**: Check Socket.IO server status

#### **Backend Issues**
- **Database connection errors**: Verify PostgreSQL connection
- **Kafka connection failed**: Check Kafka server status
- **Import errors**: Ensure all dependencies are installed

#### **Development Issues**
- **Port conflicts**: Change ports in configuration files
- **Hot reload not working**: Restart development servers
- **Test failures**: Check test environment setup

### **Performance Optimization**

- **Caching**: Implement Redis caching for frequently accessed data
- **Database Indexing**: Optimize database queries
- **Frontend Optimization**: Code splitting and lazy loading
- **CDN**: Use CDN for static assets




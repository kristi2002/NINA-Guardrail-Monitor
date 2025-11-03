# OFH Dashboard - Clean Architecture Summary

## 🏗️ Architecture Overview

The OFH Dashboard follows a **Clean Architecture** pattern with clear separation of concerns across multiple layers. This design ensures maintainability, testability, and scalability.

## 📐 Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  (API Routes + Middleware + WebSocket)                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Business Logic Layer                   │
│  (Services - Domain Logic)                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Data Access Layer                      │
│  (Repositories + Database Manager)                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
│  (Models + Database + External Systems)                      │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
backend/
├── api/                          # Presentation Layer
│   ├── routes/                   # API Endpoints (Blueprints)
│   │   ├── __init__.py          # Route registration
│   │   ├── alerts.py            # Alert management
│   │   ├── analytics.py         # Analytics endpoints
│   │   ├── auth.py              # Authentication
│   │   ├── conversations.py     # Conversation management
│   │   ├── escalations.py       # Escalation handling
│   │   ├── metrics.py           # System metrics
│   │   ├── notifications.py     # Notifications
│   │   └── security.py          # Security features
│   └── middleware/               # Cross-cutting concerns
│       ├── auth_middleware.py   # JWT authentication
│       └── error_handler.py     # Error handling
│
├── services/                     # Business Logic Layer
│   ├── base_service.py          # Base service class
│   ├── alert_service.py         # Alert business logic
│   ├── conversation_service.py  # Conversation logic
│   ├── user_service.py          # User management
│   ├── analytics_service.py     # Analytics logic
│   ├── security_service.py      # Security logic
│   ├── escalation_service.py    # Auto-escalation
│   ├── notification_service.py  # Notification logic
│   ├── error_alerting_service.py # Error alerting
│   ├── dlq_management_service.py # Dead Letter Queue
│   ├── system_monitor.py        # System monitoring
│   ├── database_service.py      # Enhanced DB operations
│   ├── kafka_*.py               # Kafka integration (5 files)
│   └── notification_infrastructure_service.py # SMS/Email/Slack
│
├── repositories/                 # Data Access Layer
│   ├── base_repository.py       # Base repository with CRUD
│   ├── user_repository.py       # User data access
│   ├── conversation_repository.py # Conversation data access
│   ├── guardrail_event_repository.py # Guardrail events
│   ├── chat_message_repository.py # Chat messages
│   └── operator_action_repository.py # Operator actions
│
├── models/                       # Data Layer
│   ├── base.py                  # Base model with common fields
│   ├── user.py                  # User model
│   ├── conversation.py          # Conversation session
│   ├── guardrail_event.py       # Guardrail events
│   ├── chat_message.py          # Chat messages
│   └── operator_action.py       # Operator actions
│
├── core/                         # Core Infrastructure
│   ├── database.py              # Database manager & connection
│   ├── cache.py                 # Caching service
│   ├── logging_config.py        # Logging configuration
│   ├── query_optimizer.py       # Query optimization utilities
│   ├── serializer.py            # Data serialization utilities
│   └── config_helper.py         # Configuration helper functions
│
├── schemas/                      # JSON Schemas
│   ├── guardrail_event.schema.json
│   ├── operator_action.schema.json
│   └── control_feedback.schema.json
│
└── app.py                        # Application entry point
```

## 🔄 Data Flow

### Request Flow (Top to Bottom)
```
1. Client Request
   ↓
2. API Route (api/routes/*.py)
   - Parse request
   - Validate inputs
   - Extract authentication
   ↓
3. Middleware (api/middleware/*.py)
   - JWT validation
   - Error handling
   - Request logging
   ↓
4. Service Layer (services/*.py)
   - Business logic
   - Data transformation
   - Business rules validation
   - Cross-cutting concerns
   ↓
5. Repository Layer (repositories/*.py)
   - Database queries
   - Data mapping
   - Query optimization
   ↓
6. Model Layer (models/*.py)
   - Database entities
   - Relationships
   - Field definitions
   ↓
7. Database (SQLite/PostgreSQL)
   - Data persistence
```

### Real-time Data Flow
```
1. Kafka Topics
   ↓
2. Kafka Consumer (services/kafka_consumer.py)
   - Event ingestion
   - Deserialization
   ↓
3. Database Service (services/database_service.py)
   - Save to database
   ↓
4. Kafka Integration Service (services/kafka_integration_service.py)
   - Process events
   ↓
5. WebSocket (Flask-SocketIO)
   - Real-time updates to frontend
```

## 🎯 Key Components

### 1. Presentation Layer (API Routes)

**Purpose**: Handle HTTP requests, validation, and responses

**Key Files**:
- `api/routes/__init__.py` - Registers all blueprints
- `api/routes/alerts.py` - Alert endpoints
- `api/routes/auth.py` - Authentication endpoints
- `api/routes/analytics.py` - Analytics endpoints
- `api/routes/security.py` - Security endpoints

**Responsibilities**:
- Request/Response handling
- Authentication/Authorization
- Input validation
- Error formatting
- WebSocket events

**Example Flow**:
```python
@alerts_bp.route('', methods=['GET'])
@token_required
def get_alerts():
    # Get repositories
    repos = get_repositories()
    alert_repo = repos['alert_repo']
    
    # Business logic
    alerts = alert_repo.get_recent_alerts(hours=24)
    
    # Format response
    return jsonify(alerts_data)
```

### 2. Business Logic Layer (Services)

**Purpose**: Implement domain-specific business logic

**Key Files**:
- `base_service.py` - Common service functionality
- `alert_service.py` - Alert management logic
- `conversation_service.py` - Conversation handling
- `analytics_service.py` - Analytics computation
- `notification_service.py` - Notification logic

**Responsibilities**:
- Business rules enforcement
- Data validation
- Business calculations
- Cross-service coordination
- Transaction management

**Example**:
```python
class AlertService(BaseService):
    def acknowledge_alert(self, alert_id, user_id):
        # Business logic
        alert = self.alert_repo.get_by_id(alert_id)
        if alert.status != 'active':
            raise ValueError("Alert is not active")
        
        # Update database
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        
        # Trigger notifications
        self.notification_service.notify(...)
```

### 3. Data Access Layer (Repositories)

**Purpose**: Abstraction over database operations

**Key Files**:
- `base_repository.py` - Generic CRUD operations
- `alert_repository.py` - Alert-specific queries
- `conversation_repository.py` - Conversation queries
- `user_repository.py` - User queries

**Responsibilities**:
- Database queries
- Data mapping
- Query optimization
- Database-specific logic
- Soft delete handling

**Example**:
```python
class AlertRepository(BaseRepository):
    def get_recent_alerts(self, hours, limit):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Alert).filter(
            Alert.detected_at >= cutoff,
            Alert.is_deleted == 0
        ).order_by(desc(Alert.detected_at)).limit(limit).all()
```

### 4. Data Layer (Models)

**Purpose**: Define database schema and relationships

**Key Files**:
- `base.py` - Base model with common fields
- `alert.py` - Alert entity
- `conversation.py` - Conversation entity
- `user.py` - User entity

**Responsibilities**:
- Database schema definition
- Relationships (ForeignKey, relationship)
- Field validation
- Serialization methods
- Timestamps and soft deletes

**Example**:
```python
class BaseModel(Base):
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    is_deleted = Column(Integer, default=0)
    
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
```

## 🔌 Integration Points

### Kafka Integration
```
┌─────────────────┐
│ Kafka Topics    │
└────────┬────────┘
         ↓
┌─────────────────────────────────────────┐
│ Kafka Topic Manager                     │
│ - Topic creation                        │
│ - Topic configuration                   │
│ - Topic statistics                      │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Kafka Consumer                          │
│ - Event ingestion                       │
│ - Pattern-based subscriptions           │
│ - Dead Letter Queue                     │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Kafka Integration Service               │
│ - Event processing                      │
│ - Database persistence                  │
│ - WebSocket broadcasting                │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Database + WebSocket                    │
└─────────────────────────────────────────┘
```

### Real-time Communication
```
┌─────────────────┐      WebSocket       ┌──────────────────┐
│  Kafka Event    │ ───────────────────→ │  Socket.IO       │
└─────────────────┘                       └────────┬─────────┘
                                                   ↓
                                        ┌──────────────────────┐
                                        │  Frontend React App  │
                                        │  - Real-time updates │
                                        │  - Live notifications│
                                        └──────────────────────┘
```

## 🛡️ Security Features

### Authentication & Authorization
- **JWT Token-based**: Stateless authentication
- **Role-based Access Control**: Admin, Operator, Viewer, Auditor
- **Middleware**: `@token_required`, `@admin_required` decorators
- **Protected Routes**: Route-level access control

### Security Services
- `SecurityService`: Security analytics and threat detection
- `ErrorAlertingService`: Security event logging
- `SystemMonitor`: Health monitoring and alerting

## 📊 Data Models

### Core Entities
1. **User**: Authentication and authorization
2. **ConversationSession**: Patient conversations
3. **GuardrailEvent**: Security events
4. **Alert**: Alert management
5. **ChatMessage**: Conversation messages
6. **OperatorAction**: Operator interventions

### Relationships
```
User
  ├── created_by Alert
  └── acknowledged_by Alert

ConversationSession
  ├── has_many GuardrailEvent
  ├── has_many ChatMessage
  └── has_many OperatorAction

Alert
  └── belongs_to ConversationSession (optional)
```

## 🔧 Infrastructure Components

### Database Manager (`core/database.py`)
- Connection pooling
- Session management
- Automatic table creation
- Connection testing

### Configuration (`config.py`)
- Environment-based configuration
- Kafka settings
- Database settings
- Security settings

### Middleware
- **Authentication**: JWT validation
- **Error Handling**: Centralized error responses
- **Logging**: Request/response logging

## 🚀 Key Features

### Clean Architecture Benefits
1. **Separation of Concerns**: Clear boundaries between layers
2. **Testability**: Each layer can be tested independently
3. **Maintainability**: Easy to understand and modify
4. **Scalability**: Add new features without affecting others
5. **Reusability**: Repositories and services are reusable

### Enterprise Features
1. **Dead Letter Queue (DLQ)**: Failed message handling
2. **Auto-escalation**: Automatic alert escalation
3. **Notification Infrastructure**: SMS, Email, Slack, Teams
4. **System Monitoring**: Health checks and metrics
5. **Error Alerting**: Centralized error management
6. **Real-time Updates**: WebSocket + Kafka integration

## 🔄 Design Patterns Used

1. **Repository Pattern**: Data access abstraction
2. **Service Pattern**: Business logic encapsulation
3. **Factory Pattern**: Database session creation
4. **Observer Pattern**: Event-driven updates (Kafka)
5. **Singleton Pattern**: Database manager instance
6. **Decorator Pattern**: Authentication middleware
7. **Strategy Pattern**: Different notification channels

## 📝 Best Practices Implemented

1. ✅ **Single Responsibility**: Each class has one job
2. ✅ **Dependency Injection**: Services inject repositories
3. ✅ **Interface Segregation**: Base classes with specific methods
4. ✅ **DRY Principle**: Base repository and service classes
5. ✅ **Exception Handling**: Comprehensive error handling
6. ✅ **Logging**: Structured logging throughout
7. ✅ **Soft Deletes**: Data retention instead of hard deletes
8. ✅ **Audit Trails**: Created/Updated timestamps
9. ✅ **Type Hints**: Better code documentation
10. ✅ **Config Management**: Environment-based configuration

## 🎓 Learning Resources

This architecture demonstrates:
- Clean Architecture principles
- Repository pattern implementation
- Service layer best practices
- API design with Flask
- Real-time systems with Kafka
- WebSocket integration
- Database abstraction
- Enterprise application patterns

## 🔮 Future Enhancements

1. **Caching Layer**: Redis integration for performance
2. **API Gateway**: Centralized API management
3. **Message Queue**: RabbitMQ for async processing
4. **Event Sourcing**: Complete event history
5. **CQRS**: Separate read/write models
6. **Microservices**: Split into independent services
7. **Containerization**: Docker deployment
8. **Kubernetes**: Orchestration and scaling

---

**Architecture Version**: 2.0  
**Last Updated**: October 2025  
**Maintained By**: OFH Development Team


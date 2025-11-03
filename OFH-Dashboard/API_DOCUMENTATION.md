# API Documentation

Complete API reference for OFH Dashboard.

## Base URL

- **Development**: `http://localhost:5000`
- **Production**: `https://your-domain.com`

All endpoints return JSON responses.

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Response Format

All responses follow this structure:

```json
{
  "success": true|false,
  "data": {...},
  "message": "Description",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### Authentication

#### POST /api/auth/login
Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@ofh-dashboard.local",
    "role": "admin"
  },
  "expires_in": 86400
}
```

#### GET /api/auth/validate
Validate JWT token.

**Response (200):**
```json
{
  "success": true,
  "valid": true,
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

#### POST /api/auth/logout
Logout current user.

**Response (200):**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### Analytics

#### GET /api/analytics/overview
Get dashboard overview metrics.

**Query Parameters:**
- `timeRange`: Time range filter (24h, 7d, 30d)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_conversations": 1234,
    "active_alerts": 45,
    "resolved_alerts": 89,
    "average_response_time": 2.5,
    "health_score": 85.5
  }
}
```

#### GET /api/analytics/notifications
Get notification analytics.

**Query Parameters:**
- `timeRange`: Time range filter

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_notifications": 342,
    "by_type": {
      "email": 156,
      "sms": 89,
      "push": 97
    },
    "by_status": {
      "sent": 298,
      "failed": 12,
      "pending": 32
    }
  }
}
```

#### GET /api/analytics/operators
Get operator performance metrics.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_operators": 12,
    "average_response_time": 3.2,
    "total_resolved": 456,
    "performance_distribution": {...}
  }
}
```

#### GET /api/analytics/alert-trends
Get alert trend analysis.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_alerts": 234,
    "by_severity": {
      "critical": 12,
      "high": 45,
      "medium": 89,
      "low": 88
    },
    "trends": [...]
  }
}
```

#### GET /api/analytics/response-times
Get response time metrics.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "average_response_time": 2.5,
    "sla_compliance": 92.5,
    "response_time_distribution": {...}
  }
}
```

#### GET /api/analytics/escalations
Get escalation analytics.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_escalations": 34,
    "escalation_rate": 14.5,
    "auto_escalations": 12,
    "manual_escalations": 22
  }
}
```

#### POST /api/analytics/export
Export analytics data.

**Request:**
```json
{
  "timeRange": "7d",
  "format": "json"
}
```

**Response (200):**
Returns downloadable file

### Security

#### GET /api/security/overview
Get security overview (Admin/Auditor only).

**Response (200):**
```json
{
  "success": true,
  "data": {
    "security_score": 85,
    "threats_blocked": 234,
    "recent_incidents": 12,
    "system_status": "healthy"
  }
}
```

#### GET /api/security/threats
Get threat detection data.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_threats": 45,
    "by_type": {...},
    "response_times": {...}
  }
}
```

#### GET /api/security/access
Get access control metrics.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_users": 45,
    "active_sessions": 23,
    "failed_logins": 12,
    "mfa_enabled": 38
  }
}
```

#### GET /api/security/compliance
Get compliance status.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "overall_compliance": 92,
    "gdpr": 95,
    "hipaa": 90,
    "soc2": 88
  }
}
```

#### GET /api/security/incidents
Get security incidents.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_incidents": 15,
    "by_severity": {...},
    "resolution_times": {...}
  }
}
```

### Alerts

#### GET /api/alerts
Get all active alerts.

**Response (200):**
```json
{
  "success": true,
  "alerts": [
    {
      "id": "1",
      "event_type": "privacy_violation_prevented",
      "severity": "high",
      "status": "pending",
      "message": "Guardrail Failure: PII detected",
      "created_at": "2024-01-01T00:00:00Z",
      "conversation_id": "conv-abc-123",
      "priority": "high",
      "assigned_to": "operator_001",
      "escalated": false,
      "escalation_level": 0,
      "patient_info": {
        "name": "Paziente X",
        "age": 45,
        "gender": "M"
      },
      "tags": ["pii", "violation"],
      "response_time": 0,
      "resolution_time": null
    }
  ],
  "total": 45,
  "critical_count": 12,
  "active_count": 23,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Conversations

#### GET /api/conversations
Get all active conversations.

**Query Parameters:**
- `status`: Filter by status (optional)
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response (200):**
```json
{
  "success": true,
  "conversations": [
    {
      "id": "conv-abc-123",
      "patient_id": "pat_123",
      "patientInfo": {
        "name": "Paziente X",
        "age": 45,
        "gender": "M",
        "pathology": "Depression"
      },
      "status": "ACTIVE",
      "situation": "Normal monitoring",
      "situationLevel": "low",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T01:00:00Z",
      "session_start": "2024-01-01T00:00:00Z",
      "session_end": null,
      "session_duration_minutes": 60,
      "total_messages": 45,
      "guardrail_violations": 2,
      "statistics": {
        "total_events": 2,
        "events_by_severity": {
          "critical": 0,
          "high": 1,
          "medium": 1,
          "low": 0
        },
        "guardrail_violations": 2
      }
    }
  ],
  "total": 25
}
```

### Metrics

#### GET /api/metrics
Get system metrics.

**Response (200):**
```json
{
  "success": true,
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 38.5,
    "active_connections": 123
  }
}
```

### Health Check

#### GET /api/health
Check API health status.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "type": "sqlalchemy"
    },
    "cache": {
      "status": "healthy",
      "type": "memory"
    },
    "kafka": {
      "status": "healthy",
      "active_topics": 4,
      "active_consumers": 2
    }
  }
}
```

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": "error_type",
  "message": "Human-readable error message"
}
```

### Error Codes

- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required or invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Example Error Response

```json
{
  "success": false,
  "error": "invalid_credentials",
  "message": "Username or password is incorrect"
}
```

## Rate Limiting

Rate limiting is applied to prevent abuse:

- **Login endpoint**: 5 attempts per 5 minutes per IP
- **API endpoints**: 100 requests per 15 minutes per user
- **Analytics endpoints**: 30 requests per minute per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

## WebSocket Events

Real-time updates via Socket.IO:

### Connection

Connect to: `ws://localhost:5000`

### Events

#### metrics_update
Receives updated system metrics.

**Data:**
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### new_guardrail_event
New guardrail violation detected.

**Data:**
```json
{
  "id": 1,
  "type": "Content Safety",
  "severity": "high",
  "message": "Potential harmful content"
}
```

#### alert_updated
Alert status changed.

**Data:**
```json
{
  "id": 1,
  "status": "resolved",
  "updated_by": "operator"
}
```


# API Endpoint Testing Guide

This guide explains how to test the updated API endpoints for alerts, conversations, and security.

## Prerequisites

1. **Start the Flask Server**
   ```powershell
   cd OFH-Dashboard\backend
   python app.py
   ```
   The server should start on `http://localhost:5000`

2. **Verify Database Connection**
   - Make sure your database is accessible
   - Ensure you have test data (or the script will show warnings for empty database)

3. **Test User Credentials**
   - Update `test_api_endpoints.py` with valid username/password
   - Default: `admin` / `admin123`

## Running the Tests

### Option 1: Run All Tests
```powershell
python test_api_endpoints.py
```

### Option 2: Custom Configuration
```powershell
python test_api_endpoints.py --url http://localhost:5000 --username admin --password admin123
```

## What Gets Tested

### 1. Authentication
- ✓ Login and token retrieval
- ✓ JWT token validation

### 2. Alerts Endpoints (`/api/alerts`)
- ✓ `GET /api/alerts` - List alerts with filters
- ✓ `GET /api/alerts/<id>` - Get alert details
- ✓ `POST /api/alerts/<id>/acknowledge` - Acknowledge alert (real database update)
- ✓ `POST /api/alerts/<id>/resolve` - Resolve alert (real database update)

### 3. Conversations Endpoints (`/api/conversations`)
- ✓ `GET /api/conversations` - List conversations
- ✓ `GET /api/conversations/<id>` - Get conversation details
  - Verifies that `recent_actions` come from `OperatorAction` (not guardrail events)
  - Verifies that `recent_events` come from `GuardrailEvent`

### 4. Security Endpoints (`/api/security`)
- ✓ `GET /api/security/overview` - Security overview
- ✓ `GET /api/security/threats` - Security threats list

## Expected Output

The test script will show:
- ✓ Green checkmarks for successful tests
- ✗ Red X marks for failed tests
- ⚠ Yellow warnings for skipped tests (e.g., empty database)

## Manual Testing with cURL

If you prefer manual testing:

### 1. Login and Get Token
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Use Token for Protected Routes
```bash
# Get alerts
curl -X GET http://localhost:5000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get alert details
curl -X GET http://localhost:5000/api/alerts/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Acknowledge alert
curl -X POST http://localhost:5000/api/alerts/1/acknowledge \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "test_operator"}'

# Resolve alert
curl -X POST http://localhost:5000/api/alerts/1/resolve \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"resolution_notes": "Test resolution", "action": "resolved"}'
```

## Troubleshooting

1. **Connection Error**
   - Ensure Flask server is running: `python app.py`
   - Check the port (default: 5000)

2. **Authentication Error**
   - Verify username/password in test script
   - Check that user exists in database

3. **Empty Database Warnings**
   - This is normal if you haven't created test data yet
   - Create guardrail events via Kafka consumer to populate data

4. **404 Not Found Errors**
   - Expected if database is empty
   - Not a failure - the endpoints are working correctly

## Key Verifications

The tests verify that:

1. **Alerts routes use AlertService** (not AlertRepository)
   - Column mappings are correct (`event_type`, `message_content`, etc.)
   - Status values are correct (`PENDING`, `ACKNOWLEDGED`, `RESOLVED`)

2. **Conversations routes use GuardrailEventRepository and OperatorActionRepository**
   - `recent_events` come from GuardrailEvent model
   - `recent_actions` come from OperatorAction model (not derived from events)

3. **Security routes use GuardrailEventRepository** (not AlertRepository)
   - All column mappings are correct
   - Status filters use correct values

4. **Database updates actually persist**
   - Acknowledge/resolve operations update the database
   - Changes are visible in subsequent GET requests


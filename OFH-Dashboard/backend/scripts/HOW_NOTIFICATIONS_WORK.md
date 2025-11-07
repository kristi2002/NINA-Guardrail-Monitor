# How Notifications Work

## 📋 Overview

The notification system uses a **real-time WebSocket connection** (Socket.IO) to push notifications from the backend to the frontend as soon as guardrail events occur.

## 🔄 Flow Diagram

```
┌─────────────────────┐
│ Guardrail Strategy │
│     Service         │
│   (Port 5001)       │
└──────────┬──────────┘
           │ HTTP POST /validate
           │ (AI message validation)
           ▼
    ┌──────────────┐
    │   Kafka      │
    │ guardrail_   │
    │   events     │
    └──────┬───────┘
           │
           │ Consumer reads event
           ▼
┌─────────────────────┐
│  Backend Consumer   │
│  (OFH Dashboard)    │
│                     │
│  • Processes event  │
│  • Stores in DB     │
│  • Emits WebSocket  │
└──────┬──────────────┘
       │
       │ socketio.emit('notification', data)
       ▼
┌─────────────────────┐
│  Frontend Socket.IO │
│   (Notification     │
│    Service)         │
│                     │
│  • Receives event   │
│  • Updates UI       │
│  • Shows in panel   │
└─────────────────────┘
```

## 🎯 How to Receive Notifications

### Prerequisites

1. **Kafka must be running** (ZooKeeper + Kafka)
2. **Backend must be running** (Flask app with Kafka consumer)
3. **Frontend must be open** (React app with Socket.IO connection)

### Step-by-Step

1. **Start Kafka** (if not running):
   ```powershell
   # Terminal 1: ZooKeeper
   cd C:\kafka\kafka_2.13-3.6.1
   .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
   
   # Terminal 2: Kafka
   cd C:\kafka\kafka_2.13-3.6.1
   .\bin\windows\kafka-server-start.bat .\config\server.properties
   ```

2. **Start Backend** (if not running):
   ```powershell
   cd C:\NINA Guardrail-Monitor\OFH-Dashboard\backend
   python app.py
   # or
   .\run.ps1
   ```

3. **Start Frontend** (if not running):
   ```powershell
   cd C:\NINA Guardrail-Monitor\OFH-Dashboard\frontend
   npm run dev
   ```

4. **Open the Dashboard** in your browser (usually `http://localhost:3000`)

5. **Test Notification** - Choose one method:

### Method 1: Send Test Event to Kafka (Easiest)

```powershell
cd C:\NINA Guardrail-Monitor\OFH-Dashboard\backend
python scripts\test_notification.py
```

This will:
- Send a test guardrail event to Kafka
- Backend consumer will process it
- Backend will emit WebSocket notification
- Frontend will receive and display it

**Options:**
```powershell
# Low severity notification
python scripts\test_notification.py --severity low

# High severity (triggers alert_escalation)
python scripts\test_notification.py --severity high

# Critical severity (triggers alert_escalation)
python scripts\test_notification.py --severity critical
```

### Method 2: Trigger Real Guardrail Event

Send a message to the Guardrail Strategy service that will trigger a violation:

```powershell
# Start Guardrail Strategy service (if not running)
cd C:\NINA Guardrail-Monitor\Guardrail-Strategy
python app.py

# In another terminal, send a test message
curl -X POST http://localhost:5001/validate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My email is test@example.com and my SSN is 123-45-6789",
    "conversation_id": "test_conv_123"
  }'
```

This will trigger a PII detection, which will:
- Create a guardrail event
- Send to Kafka
- Trigger notification in frontend

### Method 3: Use API Endpoint (Admin Only)

If you're logged in as admin, you can send a notification directly:

```javascript
// In browser console (on the dashboard page)
fetch('/api/notifications/v2/send', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  },
  body: JSON.stringify({
    user_id: 1,  // Your user ID
    title: 'Test Notification',
    message: 'This is a test notification',
    priority: 'normal',
    type: 'system',
    channels: ['in_app']
  })
})
```

## 🔍 Notification Types

### Based on Severity

- **Low/Medium Severity** → `notification` event (normal notification)
- **High/Critical Severity** → `alert_escalation` event (urgent alert)

### Based on Event Type

1. **Guardrail Events** (`guardrail_event`)
   - Triggered when guardrail violations are detected
   - Severity determines notification type

2. **Operator Actions** (`operator_action`)
   - Triggered when operators take actions
   - Always sent as `notification` event

3. **False Alarm Feedback** (`false_alarm_feedback`)
   - Triggered when operators report false alarms
   - Always sent as `notification` event

## 🐛 Troubleshooting

### No Notifications Appearing?

1. **Check WebSocket Connection**:
   - Open browser DevTools (F12)
   - Go to Console tab
   - Look for: `✅ Connected to notification service`
   - If you see connection errors, check backend is running

2. **Check Backend Logs**:
   - Look for: `Socket.IO 'notification' emitted`
   - If missing, check Kafka consumer is running

3. **Check Kafka**:
   - Verify Kafka is running: `Test-NetConnection localhost -Port 9092`
   - Check topic exists: The backend should auto-create topics

4. **Check Backend Consumer**:
   - Backend should log: `Kafka consumer started`
   - Check for any consumer errors in logs

### Test Connection

Run the test script and watch:
1. **Backend terminal**: Should show event consumed and notification emitted
2. **Browser console**: Should show notification received
3. **Notification panel**: Should show the notification

## 📊 Notification Data Structure

When a notification is received, it contains:

```json
{
  "conversation_id": "conv_123",
  "event": {
    "event_id": "event_456",
    "event_type": "alarm_triggered",
    "severity": "high",
    "message": "PII detected in message",
    "timestamp": "2025-11-07T05:30:00Z",
    "violations": [...],
    "guardrail_rules": [...]
  }
}
```

## 🎨 Frontend Display

Notifications appear in:
- **Notification Center** (bell icon in header)
- **Dashboard alerts** (recent alerts section)
- **Real-time updates** (without page refresh)

The notification panel shows:
- **Title**: Based on event type
- **Message**: From the guardrail event
- **Timestamp**: When it occurred
- **Severity**: Visual indicator (color coding)
- **Action**: Link to conversation details


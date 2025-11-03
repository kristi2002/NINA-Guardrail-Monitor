# User Documentation

Complete user guide for OFH Dashboard.

## Overview

OFH Dashboard is a real-time monitoring and analytics platform for the NINA Guardrail system. It provides comprehensive insights into conversation monitoring, security events, and system performance.

## Getting Started

### Login

1. Navigate to the login page at `http://localhost:3001/login`
2. Enter your credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Click "Sign In"

### Dashboard Overview

After logging in, you'll see the main dashboard with:

- **Real-time Metrics**: Live conversation counts, alert status, system health
- **Active Conversations**: Current monitoring sessions
- **Recent Alerts**: Latest guardrail events
- **System Status**: Service health indicators

## Features

### 📊 Main Dashboard

The main dashboard provides an overview of system activity:

#### Metrics Cards
- **Total Conversations**: Number of active monitoring sessions
- **Active Alerts**: Current unresolved guardrail events
- **Resolved Alerts**: Successfully handled events
- **Average Response Time**: Mean time to respond to alerts

#### Active Conversations
Real-time list of ongoing monitoring sessions with:
- Conversation ID
- Patient ID
- Status
- Start time
- Duration

#### Recent Alerts
Latest guardrail events showing:
- Alert type and severity
- Status (active/resolved)
- Timestamp
- Quick action buttons

### 📈 Analytics Dashboard

Access comprehensive analytics through the Analytics tab:

#### Overview Tab
- Key metrics and KPIs
- Performance trends
- System health scores

#### Notifications Tab
- Delivery rates by type (Email, SMS, Push)
- Time series data
- Failure analysis

#### Operators Tab
- Performance metrics
- Workload distribution
- Quality scores

#### Alert Trends Tab
- Alert distribution by type
- Geographic analysis
- Trend patterns

#### Response Times Tab
- SLA compliance rates
- Average response times
- Performance trends

#### Escalations Tab
- Escalation rates
- Auto vs manual escalations
- Resolution metrics

#### Time Range Filters
Filter data by time period:
- Last 24 hours
- Last 7 days
- Last 30 days

#### Export Functionality
Export analytics data in JSON format with custom time ranges.

### 🛡️ Security Dashboard

Access the security dashboard (Admin/Auditor roles only):

#### Overview Tab
- Security score (0-100)
- Threats blocked
- System status
- Recent security events

#### Threats Tab
- Threat detection metrics
- Threat type distribution
- Geographic analysis
- Response times

#### Access Control Tab
- Authentication metrics
- User activity logs
- MFA adoption rates

#### Compliance Tab
Track compliance with:
- **GDPR**: General Data Protection Regulation
- **HIPAA**: Health Insurance Portability and Accountability Act
- **SOC2**: Service Organization Control 2
- **ISO27001**: Information Security Management

#### Incidents Tab
- Incident management
- Resolution metrics
- Escalation patterns

### 🔐 User Profile

Access your profile from the top-right corner:

#### User Information
- Username
- Email
- Role
- Last login

#### Profile Settings
- Update email
- Change password
- View activity history

## Real-time Updates

The dashboard provides real-time updates via WebSocket connections:

### Live Indicators
- **Green dot**: Real-time connection active
- **Gray dot**: Connection paused
- **Red dot**: Connection lost

### Automatic Refresh
Data automatically refreshes every:
- **Dashboard metrics**: 30 seconds
- **Alerts**: On new events
- **Conversations**: On status changes

### Manual Refresh
Click the refresh button to manually update data.

## Guardrail Types

Understand the different guardrail types:

### 1. Content Safety
Prevents harmful or inappropriate content in conversations.

### 2. PII Detection
Identifies and protects personally identifiable information.

### 3. Toxicity Filter
Blocks toxic or offensive language.

### 4. Response Quality
Ensures AI responses meet quality standards.

### 5. Medical Safety
Prevents medical misinformation.

### 6. Privacy Protection
Ensures patient privacy compliance.

## Alert Management

### Alert Severity Levels

- **Critical**: Immediate attention required
- **High**: Urgent action needed
- **Medium**: Standard priority
- **Low**: Monitor and log

### Alert Actions

#### Acknowledge
Mark alert as acknowledged to indicate awareness.

#### Resolve
Mark alert as resolved when handled.

#### Escalate
Escalate to supervisor for review.

#### Add Comment
Add notes or observations.

## User Roles

### Admin
Full system access including:
- All dashboards
- User management
- Security settings
- System configuration

### Operator
Monitoring and management capabilities:
- View all dashboards
- Acknowledge and resolve alerts
- View conversations
- Add comments

### Viewer
Read-only access:
- View dashboards
- View alerts and conversations
- No modification capabilities

### Auditor
Audit and compliance access:
- View security dashboard
- Access audit logs
- Compliance reports

## Best Practices

### Daily Operations
1. Check main dashboard for critical alerts
2. Review analytics for trends
3. Monitor system health
4. Respond to alerts promptly

### Weekly Reviews
1. Analyze performance trends
2. Review operator efficiency
3. Check compliance status
4. Review incident reports

### Monthly Reports
1. Generate analytics exports
2. Review security incidents
3. Assess system improvements
4. Update documentation

## Troubleshooting

### Login Issues

**Problem**: Cannot log in
**Solutions**:
- Verify correct credentials
- Check if account is locked
- Contact administrator for reset

### Connection Issues

**Problem**: WebSocket disconnected
**Solutions**:
- Refresh page
- Check network connection
- Verify backend is running

### Display Issues

**Problem**: Charts not loading
**Solutions**:
- Clear browser cache
- Check browser console for errors
- Verify data availability

## Keyboard Shortcuts

- **Ctrl/Cmd + K**: Quick search
- **G + H**: Home dashboard
- **G + A**: Analytics
- **G + S**: Security
- **?**: Show all shortcuts

## Support

For technical support:
- **Email**: support@ofh-dashboard.local
- **Documentation**: See README.md and ARCHITECTURE.md
- **Issues**: Contact system administrator

## Glossary

- **Guardrail**: Safety mechanism preventing harmful AI outputs
- **Alert**: Notification of a guardrail violation
- **Conversation Session**: AI conversation with a patient
- **Operator**: Human reviewer monitoring conversations
- **Escalation**: Automatic or manual promotion of alert priority
- **PII**: Personally Identifiable Information
- **DLQ**: Dead Letter Queue for failed messages
- **SLA**: Service Level Agreement


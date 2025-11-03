# User Roles Explanation: Admin vs Operator

## Overview

The NINA Guardrail Monitor uses a **Role-Based Access Control (RBAC)** system with four distinct user roles. Each role has specific permissions tailored to their responsibilities in a healthcare AI monitoring environment.

---

## Why We Have Both Admin and Operator

The separation between **Admin** and **Operator** roles follows the **principle of least privilege** - users only get the minimum permissions needed to do their job.

### Key Differences

| Aspect | Admin | Operator |
|--------|-------|----------|
| **Primary Purpose** | System management & configuration | Day-to-day monitoring & response |
| **Typical Users** | IT administrators, system architects | Healthcare staff, quality officers, compliance team |
| **Access Level** | Full system control | Operational control only |
| **Risk if Compromised** | Very High - can change everything | Medium - can only modify operational data |

---

## Role Breakdown

### 🔧 Admin Role

**Purpose:** Complete system administration and configuration

**Permissions:**
- ✅ **Read** - View all dashboards and data
- ✅ **Write** - Create, modify, and delete records
- ✅ **Delete** - Remove data and configurations
- ✅ **Admin** - System configuration and settings
- ✅ **Audit** - Access audit logs and compliance reports

**Typical Responsibilities:**
1. **User Management**
   - Create/delete user accounts
   - Assign roles to users
   - Manage user permissions
   - Reset passwords

2. **System Configuration**
   - Configure guardrail rules
   - Adjust severity thresholds
   - Manage Kafka topics
   - Database administration

3. **Security Settings**
   - Configure authentication
   - Set up encryption
   - Manage API keys
   - Configure firewall rules

4. **Audit & Compliance**
   - Review audit logs
   - Generate compliance reports
   - Investigate security incidents
   - Export data for auditors

**Access Areas:**
- ✅ All dashboards (Main, Analytics, Security)
- ✅ User Management panel
- ✅ System Settings
- ✅ Security Configuration
- ✅ Audit Logs

**Example Use Cases:**
- "We need to add a new operator user for the night shift"
- "The guardrail threshold needs to be adjusted based on audit findings"
- "Generate a HIPAA compliance report for the last quarter"

---

### 👨‍💼 Operator Role

**Purpose:** Monitor conversations and respond to guardrail events

**Permissions:**
- ✅ **Read** - View dashboards and conversations
- ✅ **Write** - Acknowledge and resolve alerts
- ✅ **Acknowledge Alerts** - Mark alerts as seen/acted upon

**Typical Responsibilities:**
1. **Real-Time Monitoring**
   - Watch for guardrail violations
   - Monitor conversation quality
   - Track system health metrics

2. **Alert Management**
   - Acknowledge incoming alerts
   - Resolve false alarms
   - Escalate critical issues
   - Add comments/notes

3. **Conversation Oversight**
   - Review flagged conversations
   - Stop problematic conversations
   - Flag for human review
   - Document incidents

4. **Operational Actions**
   - Mark false alarms
   - Override guardrails when justified
   - Request system interventions
   - Provide feedback on guardrail performance

**Access Areas:**
- ✅ Main Dashboard
- ✅ Analytics Dashboard
- ✅ Conversations view
- ✅ Alerts management
- ❌ User Management
- ❌ System Settings
- ❌ Security Configuration (read-only on Security dashboard)

**Example Use Cases:**
- "A conversation triggered a PII detection alert - I'll investigate"
- "This is clearly a false alarm from a medical context - marking it as such"
- "Critical toxicity detected - I need to stop this conversation immediately"

---

## Other Roles

### 👀 Viewer Role

**Purpose:** Read-only access for stakeholders

**Permissions:**
- ✅ **Read** only

**Typical Users:**
- Executives
- Board members
- External consultants
- Reporting teams

**Access:**
- View dashboards
- Read reports
- Export data
- ❌ No modifications allowed

**Example Use Cases:**
- "Show me the security metrics from last month"
- "I need to review our compliance status for the board meeting"

---

### 📋 Auditor Role

**Purpose:** Compliance and audit reviews

**Permissions:**
- ✅ **Read**
- ✅ **Audit**

**Typical Users:**
- Compliance officers
- Internal auditors
- Quality assurance team
- Regulators (with proper authorization)

**Access:**
- View Security dashboard
- Access audit logs
- Generate compliance reports
- Review incident history
- ❌ Cannot modify data

**Example Use Cases:**
- "I need to verify all PII violations were handled properly"
- "Generate an audit trail for the last GDPR compliance check"
- "Review all operator actions taken this week"

---

## Permission Comparison Matrix

| Feature | Admin | Operator | Viewer | Auditor |
|---------|-------|----------|--------|---------|
| View Dashboards | ✅ All | ✅ All | ✅ All | ✅ Security only |
| Acknowledge Alerts | ✅ | ✅ | ❌ | ❌ |
| Resolve Alerts | ✅ | ✅ | ❌ | ❌ |
| Stop Conversations | ✅ | ✅ | ❌ | ❌ |
| Mark False Alarms | ✅ | ✅ | ❌ | ❌ |
| Create Users | ✅ | ❌ | ❌ | ❌ |
| Delete Users | ✅ | ❌ | ❌ | ❌ |
| Modify System Settings | ✅ | ❌ | ❌ | ❌ |
| Configure Guardrails | ✅ | ❌ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ | ✅ |
| Generate Reports | ✅ | ✅ | ✅ | ✅ |
| Export Data | ✅ | ✅ | ✅ | ✅ |

---

## Real-World Scenarios

### Scenario 1: Suspected False Alarm

**Operator's Job:**
- Reviews the alert in the dashboard
- Examines the conversation context
- Determines it's a false alarm
- Clicks "Mark as False Alarm"
- Adds comment: "Medical terminology used correctly"

**Admin's Job:**
- Reviews false alarm rates in analytics
- If pattern emerges, adjusts guardrail thresholds
- Updates system configuration

### Scenario 2: Security Incident

**Operator's Job:**
- Detects suspicious pattern in alerts
- Escalates to supervisor
- Documents the incident

**Admin's Job:**
- Reviews audit logs
- Investigates the security breach
- Modifies access controls
- Generates incident report
- Updates security policies

### Scenario 3: New Team Member

**Operator's Job:**
- Cannot add users

**Admin's Job:**
- Creates new user account
- Assigns appropriate role (likely Operator)
- Configures permissions
- Provides credentials

### Scenario 4: Compliance Audit

**Operator's Job:**
- Continues monitoring during audit

**Admin's Job:**
- Provides system access to auditor
- Generates compliance reports

**Auditor's Job:**
- Reviews all guardrail events
- Verifies proper handling
- Checks documentation
- Completes audit report

---

## Best Practices

### For Admins
1. **Minimize Admin Accounts**: Only create admin users when absolutely necessary
2. **Regular Audits**: Review admin activity logs weekly
3. **Strong Authentication**: Use MFA for all admin accounts
4. **Separate Tasks**: Use operator account for daily operations, admin for configuration

### For Operators
1. **Document Everything**: Add comments when taking actions
2. **Follow Escalation**: Don't try to fix system issues - escalate to admin
3. **Know Your Limits**: Don't attempt configuration changes
4. **Report Patterns**: Alert admin to repeated issues

### For Management
1. **Role Rotation**: Have multiple operators, limit admins
2. **Access Reviews**: Quarterly review of who has what access
3. **Training**: Ensure operators understand their permissions
4. **Incident Response**: Clear escalation path from operator → admin

---

## Security Benefits

### Why This Matters in Healthcare

1. **HIPAA Compliance**
   - Least privilege principle required
   - Audit trails for all actions
   - Segregation of duties

2. **GDPR Compliance**
   - Limited data access
   - Access logging mandatory
   - Data minimization principle

3. **SOC 2 Compliance**
   - Role-based access control
   - Regular access reviews
   - Incident monitoring

4. **Operational Security**
   - Reduces insider threat risk
   - Limits blast radius of compromised accounts
   - Enables accountability

---

## Implementation Details

### How Permissions Are Enforced

**Database Level:**
```python
# User model has role field
role = Column(String(20), default='operator', nullable=False)
```

**Route Level:**
```python
@admin_required  # Only admins can access
@conversations_bp.route('/users', methods=['GET'])
def get_users():
    # Admin-only user management

@token_required  # Any authenticated user
@conversations_bp.route('/conversations', methods=['GET'])  
def get_conversations():
    # All users can view conversations
```

**Frontend Level:**
```javascript
// Conditional rendering based on role
{user.role === 'admin' && <AdminPanel />}
{['admin', 'operator'].includes(user.role) && <AlertActions />}
{['admin', 'auditor'].includes(user.role) && <AuditLogs />}
```

---

## Summary

The **Admin** role is for system configuration and management, while the **Operator** role is for day-to-day monitoring and response. This separation:

✅ **Improves Security** - Limits potential damage from compromised accounts  
✅ **Enables Compliance** - Meets regulatory requirements  
✅ **Clarifies Responsibilities** - Clear job boundaries  
✅ **Reduces Errors** - Operators can't accidentally break system  
✅ **Enhances Auditing** - Clear accountability chain  

**Remember:** In healthcare AI systems, you can't have everyone with admin access. The operator/admin split is essential for both security and operational efficiency.

---

**Document Version:** 1.0  
**Last Updated:** 2025  
**Maintained By:** NINA Guardrail Monitor Team


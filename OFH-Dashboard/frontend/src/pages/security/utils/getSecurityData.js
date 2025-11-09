/**
 * Helper function to safely access and default security data
 */
export function getSecurityData(securityData) {
  // Define the full default structure
  const defaults = {
    summary: {
      security_score: 0,
      total_threats: 0,
      resolved_threats: 0,
      active_threats: 0,
    },
    recent_incidents: [],
    threat_distribution: {},
    access_control: {
      active_sessions: 0,
    },
    compliance: {
      gdpr_compliance: 0,
      hipaa_compliance: 0,
      pci_compliance: 0,
    },
    threat_data: {
      trends: [],
    },
    threat_summary: {
      total_threats: 0,
      threats_blocked: 0,
      threats_resolved: 0,
      average_response_time: 'N/A',
    },
    threat_types: [],
    threat_analysis: {
      top_threats: [],
    },
    access_data: {
      trends: [],
    },
    access_summary: {
      success_rate: 0,
      failed_attempts: 0,
      mfa_adoption_rate: 0,
      suspicious_activities: 0,
      admin_activity_recent: 0,
    },
    user_patterns: [],
    frameworks: {
      GDPR: { score: 0, status: 'N/A', requirements_met: 0, total_requirements: 0 },
      HIPAA: { score: 0, status: 'N/A', requirements_met: 0, total_requirements: 0 },
      SOC2: { score: 0, status: 'N/A', requirements_met: 0, total_requirements: 0 },
    },
    security_controls: {},
    audit_history: [],
    overall_compliance_score: 0,
    incident_data: {
      trends: [],
    },
    incident_summary: {
      total_incidents: 0,
      resolved_incidents: 0,
      resolution_rate: 0,
      average_response_time: 'N/A',
    },
    alerting: {
      alerts: [],
      warning: null,
    },
  }

  // Get the current data (which might be null, or a slim object)
  const currentData = securityData ? (securityData.data || securityData) : {}

  // Return the defaults *merged* with the current data
  return {
    ...defaults,
    ...currentData,
  }
}


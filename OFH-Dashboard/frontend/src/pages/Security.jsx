import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import TimeAgo from '../components/TimeAgo'
import './Security.css'

const Security = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [timeRange, setTimeRange] = useState('7d')
  const [securityData, setSecurityData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  
  // ✅ Refs to track the *previous* state
  const prevTimeRange = useRef(timeRange)
  const prevActiveTab = useRef(activeTab)

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '🛡️' },
    { id: 'threats', label: 'Threats', icon: '⚠️' },
    { id: 'access', label: 'Access Control', icon: '🔐' },
    { id: 'compliance', label: 'Compliance', icon: '📋' },
    { id: 'incidents', label: 'Incidents', icon: '🚨' }
  ]

  const timeRanges = [
    { value: '1d', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ]

  // =================================================================
  // 1. THIS IS THE NEW CLICK HANDLER
  // =================================================================
  const handleTabClick = (tabId) => {
    if (tabId === activeTab) return // Don't re-fetch if tab is the same

    // JUST set the active tab. The useEffect will handle the data change.
    setActiveTab(tabId)
  }

  // =================================================================
  // 2. THIS IS THE COMBINED useEffect for [timeRange, activeTab]
  // =================================================================
  // ✅ ONE useEffect to rule them all - prevents duplicate requests
  useEffect(() => {
    // 1. Create the AbortController
    const controller = new AbortController()
    const signal = controller.signal

    // 2. Check what changed
    const timeRangeChanged = prevTimeRange.current !== timeRange
    const tabChanged = prevActiveTab.current !== activeTab

    // 3. Decide on loading state
    if (timeRangeChanged) {
      // Time range changed: Show full loader, then fetch
      fetchSecurityData(true, signal)
    } else if (tabChanged) {
      // Tab changed: Instantly show skeletons, then fetch (no full loader)
      setSecurityData(null)
      fetchSecurityData(false, signal)
    } else {
      // This is the initial mount (or Strict Mode's 2nd mount)
      // Show the full loader
      fetchSecurityData(true, signal)
    }

    // 4. Update the refs *after* the logic
    prevTimeRange.current = timeRange
    prevActiveTab.current = activeTab

    // 5. Set up the interval
    const interval = setInterval(() => {
      console.log('[SECURITY] Auto-refreshing security data...')
      // Auto-refresh is always silent, no signal or loader needed
      fetchSecurityData(false)
    }, 300000) // 5 minutes

    // 6. Return ONE cleanup function
    return () => {
      console.log('🧹 Cleaning up Security: aborting requests...')
      controller.abort()
      clearInterval(interval)
    }
  }, [timeRange, activeTab]) // ✅ DEPENDS ON BOTH

  const fetchSecurityData = async (showLoadingSpinner = true, signal = null) => {
    try {
      if (showLoadingSpinner) {
        setLoading(true) // Show full-page loader (for time range changes)
      }
      setError(null) // Always clear old errors on a new fetch

      // Build the request config with abort signal
      const config = signal ? { signal } : {}

      let response
      // This switch statement is the same as you had
      switch (activeTab) {
        case 'overview':
          response = await axios.get(`/api/security/overview`, config)
          break
        case 'threats':
          response = await axios.get(`/api/security/threats?timeRange=${timeRange}`, config)
          break
        case 'access':
          response = await axios.get(`/api/security/access?timeRange=${timeRange}`, config)
          break
        case 'compliance':
          response = await axios.get(`/api/security/compliance`, config)
          break
        case 'incidents':
          response = await axios.get(`/api/security/incidents?timeRange=${timeRange}`, config)
          break
        default:
          response = await axios.get(`/api/security/overview`, config)
      }

      // Handle both direct data and wrapped responses with safe fallbacks
      let data = null
      if (response.data.success && response.data.data) {
        data = response.data.data
      } else if (response.data) {
        data = response.data
      }

      // Ensure data has required structure with safe defaults
      if (data) {
        setSecurityData(data)
      } else {
        setSecurityData({})
      }
      setLastUpdated(new Date()) // ✅ Update last updated timestamp
    } catch (err) {
      // Don't set error if request was intentionally cancelled
      if (err.name === 'CanceledError' || axios.isCancel(err)) {
        console.log('[SECURITY] Request was cancelled')
        return
      }
      
      // Set an error regardless of loading type
      if (err.response) {
        setError(`Failed to load ${activeTab} data: ${err.response.status} ${err.response.statusText}`)
      } else if (err.request) {
        setError(`Network error: Unable to connect to server for ${activeTab} data`)
      } else {
        setError(`Failed to load ${activeTab} data: ${err.message}`)
      }
      // ✅✅ THIS IS THE CRITICAL FIX ✅✅
      // Set empty data to prevent render crashes
      setSecurityData({})
    } finally {
      // ✅ SIMPLIFY THIS - Always turn off loading
      setLoading(false)
    }
  }

  // Helper function to safely access and default security data
  const getSecurityData = () => {
    // 1. Define the full default structure
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
      // ✅ Added 'threat_types' and 'threat_analysis' to defaults
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
    }

    // 2. Get the current data (which might be null, or a slim object)
    const currentData = securityData ? (securityData.data || securityData) : {}

    // 3. Return the defaults *merged* with the current data
    // This ensures all keys always exist.
    return {
      ...defaults,
      ...currentData,
    }
  }

  const renderMetricCard = (title, value, subtitle, icon, trend) => (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
        {trend && <span className={`metric-trend ${trend.type}`}>{trend.value}</span>}
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-subtitle">{subtitle}</div>
    </div>
  )

  // Skeleton Components
  const OverviewSkeleton = () => (
    <div className="security-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-events-section"></div>
      <div className="skeleton-status-grid"></div>
    </div>
  )

  const ThreatsSkeleton = () => (
    <div className="security-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const AccessSkeleton = () => (
    <div className="security-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const ComplianceSkeleton = () => (
    <div className="security-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-frameworks-grid"></div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const IncidentsSkeleton = () => (
    <div className="security-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-incidents-list"></div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const renderOverviewTab = () => {
    // ✅ 1. Call the helper. This can NEVER be null.
    const data = getSecurityData()
    
    // ✅ 2. Check for skeleton state *after* getting data
    if (!securityData) return <OverviewSkeleton />

    try {
      // ✅ 3. Destructure *safely*. 'data' is guaranteed to have these keys.
      const { summary, recent_incidents, threat_distribution, access_control, compliance } = data

    return (
      <div className="security-tab">
        <div className="metrics-grid">
          {renderMetricCard('Security Score', `${summary.security_score}%`, 'Overall security rating', '🛡️')}
          {renderMetricCard('Total Threats', summary.total_threats, 'This period', '🚫')}
          {renderMetricCard('Active Sessions', access_control.active_sessions, 'Being monitored', '👁️')}
          {renderMetricCard('Resolved Threats', summary.resolved_threats, 'Successfully resolved', '✅')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Recent Security Incidents</h3>
            <div className="events-list">
              {recent_incidents.slice(0, 5).map((incident, index) => (
                <div key={incident.id || index} className={`event-item ${(incident.severity || 'unknown').toLowerCase()}`}>
                  <div className="event-header">
                    <span className="event-type">{incident.type || 'Unknown Incident'}</span>
                    <span className={`event-severity ${(incident.severity || 'unknown').toLowerCase()}`}>{incident.severity || 'Unknown'}</span>
                  </div>
                  <div className="event-description">{incident.description || 'No description available'}</div>
                  <div className="event-meta">
                    <span>Time: {new Date(incident.timestamp).toLocaleString()}</span>
                    <span>Status: {incident.status || 'Unknown'}</span>
                    <span>ID: {incident.id || 'N/A'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-container">
            <h3>Threat Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.entries(threat_distribution).map(([type, count]) => ({ type, count }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="security-status">
          <h3>Compliance Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">GDPR Compliance</span>
              <span className={`status-value ${compliance.gdpr_compliance >= 90 ? 'good' : compliance.gdpr_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.gdpr_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">HIPAA Compliance</span>
              <span className={`status-value ${compliance.hipaa_compliance >= 90 ? 'good' : compliance.hipaa_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.hipaa_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">PCI Compliance</span>
              <span className={`status-value ${compliance.pci_compliance >= 90 ? 'good' : compliance.pci_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.pci_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Active Threats</span>
              <span className={`status-value ${summary.active_threats === 0 ? 'good' : summary.active_threats <= 2 ? 'warning' : 'critical'}`}>
                {summary.active_threats}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
    } catch (err) {
      // Error rendering overview tab
      return (
        <div className="security-error">
          <h3>Error rendering overview tab</h3>
          <p>Error: {err.message}</p>
        </div>
      )
    }
  }

  const renderThreatsTab = () => {
    // ✅ 1. Call the helper. This can NEVER be null.
    const data = getSecurityData()
    
    // ✅ 2. Check for skeleton state *after* getting data
    if (!securityData) return <ThreatsSkeleton />

    try {
      // ✅ 3. Destructure *safely*. 'data' is guaranteed to have these keys.
      const { threat_data, threat_summary, threat_types, threat_analysis } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Total Threats', threat_summary.total_threats, 'Detected this period', '⚠️')}
            {renderMetricCard('Threats Blocked', threat_summary.threats_blocked, 'Successfully blocked', '🛡️')}
            {renderMetricCard('Resolution Rate', `${Math.round((threat_summary.threats_resolved / Math.max(threat_summary.total_threats, 1)) * 100)}%`, 'Threats resolved', '✅')}
            {renderMetricCard('Avg Response', threat_summary.average_response_time, 'Time to respond', '⏱️')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Threat Trends Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={threat_data.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total_threats" stroke="#ef4444" name="Total Threats" />
                  <Line type="monotone" dataKey="malware_detected" stroke="#f59e0b" name="Malware" />
                  <Line type="monotone" dataKey="phishing_attempts" stroke="#8b5cf6" name="Phishing" />
                  <Line type="monotone" dataKey="brute_force_attempts" stroke="#06b6d4" name="Brute Force" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <h3>Threat Types Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={threat_analysis.top_threats}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="count"
                    nameKey="type"
                    label={({type, count}) => `${type}: ${count}`}
                  >
                    {threat_analysis.top_threats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['#ef4444', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'][index]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )
    } catch (err) {
      // Error rendering threats tab
      return (
        <div className="security-error">
          <h3>Error rendering threats tab</h3>
          <p>Error: {err.message}</p>
        </div>
      )
    }
  }

  const renderAccessTab = () => {
    // ✅ 1. Call the helper. This can NEVER be null.
    const data = getSecurityData()
    
    // ✅ 2. Check for skeleton state *after* getting data
    if (!securityData) return <AccessSkeleton />

    try {
      // ✅ 3. Destructure *safely*. 'data' is guaranteed to have these keys.
      const { access_data, access_summary, user_patterns } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Success Rate', `${access_summary.success_rate}%`, 'Authentication success', '✅')}
            {renderMetricCard('Failed Attempts', access_summary.failed_attempts, 'Failed logins', '❌')}
            {renderMetricCard('MFA Adoption', `${access_summary.mfa_adoption_rate}%`, 'Multi-factor auth', '🔐')}
            {renderMetricCard('Suspicious Activity', access_summary.suspicious_activities, 'Detected activities', '👁️')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Authentication Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={access_data.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="successful_logins" stackId="1" stroke="#10b981" fill="#10b981" name="Successful" />
                  <Area type="monotone" dataKey="failed_logins" stackId="1" stroke="#ef4444" fill="#ef4444" name="Failed" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <h3>User Access Patterns</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={user_patterns}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="user_type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="active_sessions" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )
    } catch (err) {
      // Error rendering access tab
      return (
        <div className="security-error">
          <h3>Error rendering access tab</h3>
          <p>Error: {err.message}</p>
        </div>
      )
    }
  }

  const renderComplianceTab = () => {
    // ✅ 1. Call the helper. This can NEVER be null.
    const data = getSecurityData()
    
    // ✅ 2. Check for skeleton state *after* getting data
    if (!securityData) return <ComplianceSkeleton />

    try {
      // ✅ 3. Destructure *safely*. 'data' is guaranteed to have these keys.
      const { frameworks, security_controls, audit_history, overall_compliance_score } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Overall Score', `${overall_compliance_score}%`, 'Compliance rating', '📊')}
            {renderMetricCard('GDPR Score', `${frameworks.GDPR.score}%`, 'GDPR compliance', '🇪🇺')}
            {renderMetricCard('HIPAA Score', `${frameworks.HIPAA.score}%`, 'HIPAA compliance', '🏥')}
            {renderMetricCard('SOC2 Score', `${frameworks.SOC2.score}%`, 'SOC2 compliance', '🔒')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Compliance Frameworks</h3>
              <div className="compliance-frameworks">
                {Object.entries(frameworks).map(([framework, data]) => (
                  <div key={framework} className="framework-card">
                    <div className="framework-header">
                      <h4>{framework}</h4>
                      <span className={`framework-status ${data.status.toLowerCase()}`}>{data.status}</span>
                    </div>
                    <div className="framework-score">{data.score}%</div>
                    <div className="framework-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${data.score}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="framework-details">
                      <span>{data.requirements_met}/{data.total_requirements} requirements met</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="chart-container">
              <h3>Security Controls</h3>
              <div className="controls-grid">
                {Object.entries(security_controls).map(([control, data]) => (
                  <div key={control} className="control-item">
                    <div className="control-header">
                      <span className="control-name">{control.replace('_', ' ').toUpperCase()}</span>
                      <span className={`control-status ${data.status.toLowerCase()}`}>{data.status}</span>
                    </div>
                    <div className="control-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${(data.implemented / data.total) * 100}%` }}
                        ></div>
                      </div>
                      <span className="control-count">{data.implemented}/{data.total}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )
    } catch (err) {
      // Error rendering compliance tab
      return (
        <div className="security-error">
          <h3>Error rendering compliance tab</h3>
          <p>Error: {err.message}</p>
        </div>
      )
    }
  }

  const renderIncidentsTab = () => {
    // ✅ 1. Call the helper. This can NEVER be null.
    const data = getSecurityData()
    
    // ✅ 2. Check for skeleton state *after* getting data
    if (!securityData) return <IncidentsSkeleton />

    try {
      // ✅ 3. Destructure *safely*. 'data' is guaranteed to have these keys.
      const { incident_data, incident_summary, recent_incidents } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Total Incidents', incident_summary.total_incidents, 'This period', '🚨')}
            {renderMetricCard('Resolved', incident_summary.resolved_incidents, 'Successfully resolved', '✅')}
            {renderMetricCard('Resolution Rate', `${incident_summary.resolution_rate}%`, 'Incidents resolved', '📊')}
            {renderMetricCard('Avg Response', incident_summary.average_response_time, 'Response time', '⏱️')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Incident Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={incident_data.trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="incidents_detected" stroke="#ef4444" name="Detected" />
                  <Line type="monotone" dataKey="incidents_resolved" stroke="#10b981" name="Resolved" />
                  <Line type="monotone" dataKey="incidents_escalated" stroke="#f59e0b" name="Escalated" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <h3>Recent Incidents</h3>
              <div className="incidents-list">
                {recent_incidents.slice(0, 8).map((incident) => (
                  <div key={incident.id} className={`incident-item ${incident.severity.toLowerCase()}`}>
                    <div className="incident-header">
                      <span className="incident-type">{incident.type}</span>
                      <span className={`incident-severity ${incident.severity.toLowerCase()}`}>
                        {incident.severity}
                      </span>
                      <span className={`incident-status ${incident.status.toLowerCase()}`}>
                        {incident.status}
                      </span>
                    </div>
                    <div className="incident-description">{incident.description}</div>
                    <div className="incident-meta">
                      <span>Assigned: {incident.assigned_to}</span>
                      {incident.resolution_time && <span>Resolved in: {incident.resolution_time}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )
    } catch (err) {
      // Error rendering incidents tab
      return (
        <div className="security-error">
          <h3>Error rendering incidents tab</h3>
          <p>Error: {err.message}</p>
        </div>
      )
    }
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab()
      case 'threats':
        return renderThreatsTab()
      case 'access':
        return renderAccessTab()
      case 'compliance':
        return renderComplianceTab()
      case 'incidents':
        return renderIncidentsTab()
      default:
        return renderOverviewTab()
    }
  }

  // ✅ Only show full-page loading for initial load
  if (loading && !securityData) {
    return <div className="security-loading">Loading security dashboard...</div>
  }

  return (
    <div className="security-dashboard">
      <div className="security-header">
        <div className="header-left">
          <h1>🛡️ Security Dashboard</h1>
          <p className="header-subtitle">
            Comprehensive security monitoring and threat analysis • Last updated: <TimeAgo timestamp={lastUpdated} />
          </p>
        </div>
        
        <div className="header-controls">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="time-range-select"
          >
            {timeRanges.map(range => (
              <option key={range.value} value={range.value}>{range.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="security-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`security-tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => handleTabClick(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="security-content">
        {/* ✅ ADD THIS ERROR BANNER (like Analytics.jsx) */}
        {error && (
          <div className="security-error-banner" style={{ padding: '1rem', background: '#fee', color: '#c33', marginBottom: '1rem', borderRadius: '4px' }}>
            ⚠️ {error}
            <button onClick={() => { setError(null); fetchSecurityData(true); }} style={{ marginLeft: '1rem', padding: '0.25rem 0.5rem' }}>Retry</button>
          </div>
        )}
        {loading && securityData && (
          <div className="security-loading-indicator" style={{ padding: '1rem', textAlign: 'center' }}>Loading {activeTab} data...</div>
        )}
        {renderActiveTab()}
      </div>
    </div>
  )
}

export default Security

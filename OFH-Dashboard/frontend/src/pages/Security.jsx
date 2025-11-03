import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import './Security.css'

const Security = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [timeRange, setTimeRange] = useState('7d')
  const [securityData, setSecurityData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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

  // Effect for time range changes - show loading state
  useEffect(() => {
    fetchSecurityData(true) // true = show full-page loader
    
    // Auto-refresh security data every 5 minutes
    const interval = setInterval(() => fetchSecurityData(true), 300000)
    return () => clearInterval(interval)
  }, [timeRange]) // This ONLY runs on timeRange change

  // =================================================================
  // 1. THIS IS THE NEW CLICK HANDLER
  // =================================================================
  const handleTabClick = (tabId) => {
    if (tabId === activeTab) return // Don't re-fetch if tab is the same

    // Set BOTH states at once. This causes a re-render
    // where activeTab is new AND securityData is null.
    setActiveTab(tabId)
    setSecurityData(null)
  }

  // =================================================================
  // 2. THIS IS THE MODIFIED useEffect for [activeTab]
  // =================================================================
  // Separate effect for tab changes - fetch data without full loading state
  useEffect(() => {
    // We only fetch data. `setSecurityData(null)` was moved to the click handler.
    // This will run *after* the re-render from handleTabClick,
    // which correctly showed the loading state.
    fetchSecurityData(false) // false = do not show full-page loader
  }, [activeTab]) // This ONLY runs on activeTab change

  const fetchSecurityData = async (showLoadingSpinner = true) => {
    try {
      if (showLoadingSpinner) {
        setLoading(true) // Show full-page loader (for time range changes)
      }
      setError(null) // Always clear old errors on a new fetch

      let response
      // This switch statement is the same as you had
      switch (activeTab) {
        case 'overview':
          response = await axios.get(`/api/security/overview`)
          break
        case 'threats':
          response = await axios.get(`/api/security/threats?timeRange=${timeRange}`)
          break
        case 'access':
          response = await axios.get(`/api/security/access?timeRange=${timeRange}`)
          break
        case 'compliance':
          response = await axios.get(`/api/security/compliance`)
          break
        case 'incidents':
          response = await axios.get(`/api/security/incidents?timeRange=${timeRange}`)
          break
        default:
          response = await axios.get(`/api/security/overview`)
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
    } catch (err) {
      // Set an error regardless of loading type
      if (err.response) {
        setError(`Failed to load ${activeTab} data: ${err.response.status} ${err.response.statusText}`)
      } else if (err.request) {
        setError(`Network error: Unable to connect to server for ${activeTab} data`)
      } else {
        setError(`Failed to load ${activeTab} data: ${err.message}`)
      }
    } finally {
      if (showLoadingSpinner) {
        setLoading(false) // Only turn off full-page loader if we turned it on
      }
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
    try {
      if (loading) return <div className="security-loading">Loading security overview...</div>
      if (error && !securityData) return <div className="security-error">{error}</div>
      if (!securityData) return <OverviewSkeleton />

      // Add safety checks for data structure
      if (!securityData || typeof securityData !== 'object') {
        return <div className="security-loading">Loading security data...</div>
      }

      // Handle the actual backend data structure
      const { summary = {}, recent_incidents = [], threat_distribution = {}, access_control = {}, compliance = {} } = securityData
      
      // Add safety checks for summary
      if (!summary || typeof summary !== 'object') {
        return <div className="security-loading">Loading security data...</div>
      }

    return (
      <div className="security-tab">
        <div className="metrics-grid">
          {renderMetricCard('Security Score', `${summary.security_score || 0}%`, 'Overall security rating', '🛡️')}
          {renderMetricCard('Total Threats', summary.total_threats || 0, 'This period', '🚫')}
          {renderMetricCard('Active Sessions', access_control.active_sessions || 0, 'Being monitored', '👁️')}
          {renderMetricCard('Resolved Threats', summary.resolved_threats || 0, 'Successfully resolved', '✅')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Recent Security Incidents</h3>
            <div className="events-list">
              {(recent_incidents || []).slice(0, 5).map((incident, index) => (
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
                {compliance.gdpr_compliance || 0}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">HIPAA Compliance</span>
              <span className={`status-value ${compliance.hipaa_compliance >= 90 ? 'good' : compliance.hipaa_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.hipaa_compliance || 0}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">PCI Compliance</span>
              <span className={`status-value ${compliance.pci_compliance >= 90 ? 'good' : compliance.pci_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.pci_compliance || 0}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Active Threats</span>
              <span className={`status-value ${(summary.active_threats || 0) === 0 ? 'good' : (summary.active_threats || 0) <= 2 ? 'warning' : 'critical'}`}>
                {summary.active_threats || 0}
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
    try {
      if (loading) return <div className="security-loading">Loading threats data...</div>
      if (error) return <div className="security-error">{error}</div>
      if (!securityData) return <ThreatsSkeleton />

      // Handle different possible data structures
      const data = securityData.data || securityData
      
      // Add safety checks for required data
      if (!data || typeof data !== 'object') {
        return <div className="security-loading">Loading threats data...</div>
      }
      
      const { threat_data = {}, threat_summary = {}, threat_types = [], threat_analysis = {} } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Total Threats', threat_summary.total_threats || 0, 'Detected this period', '⚠️')}
            {renderMetricCard('Threats Blocked', threat_summary.threats_blocked || 0, 'Successfully blocked', '🛡️')}
            {renderMetricCard('Resolution Rate', `${Math.round(((threat_summary.threats_resolved || 0) / Math.max(threat_summary.total_threats || 1, 1)) * 100)}%`, 'Threats resolved', '✅')}
            {renderMetricCard('Avg Response', threat_summary.average_response_time || 'N/A', 'Time to respond', '⏱️')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Threat Trends Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={threat_data?.trends || []}>
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
                    data={threat_analysis?.top_threats || []}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="count"
                    nameKey="type"
                    label={({type, count}) => `${type}: ${count}`}
                  >
                    {threat_analysis?.top_threats?.map((entry, index) => (
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
    try {
      if (loading) return <div className="security-loading">Loading access data...</div>
      if (error) return <div className="security-error">{error}</div>
      if (!securityData) return <AccessSkeleton />

      // Handle different possible data structures
      const data = securityData.data || securityData
      
      // Add safety checks for required data
      if (!data || typeof data !== 'object') {
        return <div className="security-loading">Loading access data...</div>
      }
      
      const { access_data = {}, access_summary = {}, user_patterns = [] } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Success Rate', `${access_summary.success_rate || 0}%`, 'Authentication success', '✅')}
            {renderMetricCard('Failed Attempts', access_summary.failed_attempts || 0, 'Failed logins', '❌')}
            {renderMetricCard('MFA Adoption', `${access_summary.mfa_adoption_rate || 0}%`, 'Multi-factor auth', '🔐')}
            {renderMetricCard('Suspicious Activity', access_summary.suspicious_activities || 0, 'Detected activities', '👁️')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Authentication Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={access_data?.trends || []}>
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
                <BarChart data={user_patterns || []}>
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
    try {
      if (loading) return <div className="security-loading">Loading compliance data...</div>
      if (error) return <div className="security-error">{error}</div>
      if (!securityData) return <ComplianceSkeleton />

      // Handle different possible data structures
      const data = securityData.data || securityData
      
      // Add safety checks for required data
      if (!data || typeof data !== 'object') {
        return <div className="security-loading">Loading compliance data...</div>
      }
      
      const { frameworks = {}, security_controls = {}, audit_history = [], overall_compliance_score = 0 } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Overall Score', `${overall_compliance_score}%`, 'Compliance rating', '📊')}
            {renderMetricCard('GDPR Score', `${frameworks.GDPR?.score || 0}%`, 'GDPR compliance', '🇪🇺')}
            {renderMetricCard('HIPAA Score', `${frameworks.HIPAA?.score || 0}%`, 'HIPAA compliance', '🏥')}
            {renderMetricCard('SOC2 Score', `${frameworks.SOC2?.score || 0}%`, 'SOC2 compliance', '🔒')}
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
    try {
      if (loading) return <div className="security-loading">Loading incidents data...</div>
      if (error) return <div className="security-error">{error}</div>
      if (!securityData) return <IncidentsSkeleton />

      // Handle different possible data structures
      const data = securityData.data || securityData
      
      // Add safety checks for required data
      if (!data || typeof data !== 'object') {
        return <div className="security-loading">Loading incidents data...</div>
      }
      
      const { incident_data = {}, incident_summary = {}, recent_incidents = [] } = data

      return (
        <div className="security-tab">
          <div className="metrics-grid">
            {renderMetricCard('Total Incidents', incident_summary.total_incidents || 0, 'This period', '🚨')}
            {renderMetricCard('Resolved', incident_summary.resolved_incidents || 0, 'Successfully resolved', '✅')}
            {renderMetricCard('Resolution Rate', `${incident_summary.resolution_rate || 0}%`, 'Incidents resolved', '📊')}
            {renderMetricCard('Avg Response', incident_summary.average_response_time || 'N/A', 'Response time', '⏱️')}
          </div>

          <div className="charts-grid">
            <div className="chart-container">
              <h3>Incident Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={incident_data?.trends || []}>
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
                {(recent_incidents || []).slice(0, 8).map((incident) => (
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

  if (loading) {
    return <div className="security-loading">Loading security dashboard...</div>
  }

  if (error) {
    return <div className="security-error">{error}</div>
  }

  return (
    <div className="security-dashboard">
      <div className="security-header">
        <div className="header-left">
          <h1>🛡️ Security Dashboard</h1>
          <p className="header-subtitle">
            Comprehensive security monitoring and threat analysis • Last updated: {new Date().toLocaleTimeString()}
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
        {renderActiveTab()}
      </div>
    </div>
  )
}

export default Security

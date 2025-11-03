import { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './Analytics.css'

function Analytics() {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [timeRange, setTimeRange] = useState('7d')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Helper function to safely access analytics data
  const getAnalyticsData = () => {
    if (!analyticsData) return null
    const data = analyticsData.data || analyticsData
    
    // If data is missing critical properties, return a fallback structure
    if (!data || typeof data !== 'object') {
      return {
        summary_metrics: {
          total_alerts_processed: 0,
          avg_response_time: '0ms',
          resolution_rate: 0,
          notification_delivery_rate: 0,
          sla_compliance: 0,
          escalation_rate: 0
        },
        team_metrics: {
          active_operators: 0,
          total_alerts_handled: 0,
          average_response_time: '0ms',
          top_performer: 'N/A'
        },
        operator_rankings: [],
        workload_distribution: [],
        performance_trends: []
      }
    }
    
    return data
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'notifications', label: 'Notifications', icon: '📧' },
    { id: 'operators', label: 'Operators', icon: '👥' },
    { id: 'alerts', label: 'Alert Trends', icon: '📈' },
    { id: 'response', label: 'Response Times', icon: '⏱️' },
    { id: 'escalations', label: 'Escalations', icon: '⬆️' }
  ]

  const timeRanges = [
    { value: '1d', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ]

  // Effect for time range changes - show loading state
  useEffect(() => {
    fetchAnalyticsData(true) // true = show full-page loader
    
    // Auto-refresh analytics every 5 minutes
    const interval = setInterval(() => {
      console.log('[ANALYTICS] Auto-refreshing analytics data...')
      fetchAnalyticsData(true)
    }, 300000) // 5 minutes
    
    return () => {
      clearInterval(interval)
    }
  }, [timeRange]) // This ONLY runs on timeRange change

  // =================================================================
  // 1. THIS IS THE NEW CLICK HANDLER
  // =================================================================
  const handleTabClick = (tabId) => {
    if (tabId === activeTab) return // Don't re-fetch if tab is the same

    // Set BOTH states at once. This causes a re-render
    // where activeTab is new AND analyticsData is null.
    setActiveTab(tabId)
    setAnalyticsData(null)
  }

  // =================================================================
  // 2. THIS IS THE MODIFIED useEffect for [activeTab]
  // =================================================================
  // Separate effect for tab changes - fetch data without full loading state
  useEffect(() => {
    // We only fetch data. `setAnalyticsData(null)` was moved to the click handler.
    // This will run *after* the re-render from handleTabClick,
    // which correctly showed the loading state.
    fetchAnalyticsData(false) // false = do not show full-page loader
  }, [activeTab]) // This ONLY runs on activeTab change

  // Helper function to safely access nested properties
  const safeGet = (obj, path, defaultValue = null) => {
    try {
      return path.split('.').reduce((current, key) => {
        return current && current[key] !== undefined ? current[key] : defaultValue
      }, obj)
    } catch (error) {
      console.warn(`Error accessing path ${path}:`, error)
      return defaultValue
    }
  }

  const fetchAnalyticsData = async (showLoadingSpinner = true) => {
    try {
      if (showLoadingSpinner) {
        setLoading(true) // Show full-page loader (for time range changes)
      }
      setError(null) // Always clear old errors on a new fetch

      let response
      // This switch statement is the same as you had
      switch (activeTab) {
        case 'overview':
          response = await axios.get(`/api/analytics/overview?timeRange=${timeRange}`)
          break
        case 'notifications':
          response = await axios.get(`/api/analytics/notifications?timeRange=${timeRange}`)
          break
        case 'operators':
          response = await axios.get(`/api/analytics/operators?timeRange=${timeRange}`)
          break
        case 'alerts':
          response = await axios.get(`/api/analytics/alert-trends?timeRange=${timeRange}`)
          break
        case 'response':
          response = await axios.get(`/api/analytics/response-times?timeRange=${timeRange}`)
          break
        case 'escalations':
          response = await axios.get(`/api/analytics/escalations?timeRange=${timeRange}`)
          break
        default:
          response = await axios.get(`/api/analytics/overview?timeRange=${timeRange}`)
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
        // Add safe defaults for common missing properties
        const safeData = {
          ...data,
          notification_breakdown: data.notification_breakdown || [],
          trends: data.trends || [],
          response_times: data.response_times || [],
          escalation_trends: data.escalation_trends || [],
          alert_breakdown: data.alert_breakdown || [],
          sla_targets: data.sla_targets || [],
          escalation_reasons: data.escalation_reasons || [],
          trend_analysis: data.trend_analysis || { most_common_type: 'N/A', week_over_week_change: 0 },
          peak_hours: data.peak_hours || { peak_hour: 'N/A', peak_count: 0 },
          severity_distribution: data.severity_distribution || [],
          failure_reasons: data.failure_reasons || [],
          supervisor_response: data.supervisor_response || { avg_supervisor_response_time: 'N/A', supervisor_resolution_rate: 0 },
          escalation_timing: data.escalation_timing || { fastest_escalation: 'N/A' },
          overall_avg_response_time: data.overall_avg_response_time || 'N/A',
          sla_compliance_rate: data.sla_compliance_rate || 0,
          total_escalations: data.total_escalations || 0,
          auto_escalation_percentage: data.auto_escalation_percentage || 0,
          escalation_rate: data.escalation_rate || 0
        }
        setAnalyticsData(safeData)
      } else {
        setAnalyticsData({})
      }
      setLastUpdated(new Date())
    } catch (err) {
      // Set an error regardless of loading type
      if (err.response) {
        setError(`Failed to load ${activeTab} data: ${err.response.status} ${err.response.statusText}`)
      } else if (err.request) {
        setError(`Network error: Unable to connect to server for ${activeTab} data`)
      } else {
        setError(`Failed to load ${activeTab} data: ${err.message}`)
      }
      // Set empty data structure to prevent crashes
      setAnalyticsData({})
    } finally {
      // Always clear loading state, but only show full-page loader when requested
      setLoading(false)
    }
  }


  const exportData = async (format = 'json') => {
    try {
      const response = await axios.post('/api/analytics/export', {
        timeRange: timeRange,
        format: format
      })
      
      if (format === 'json') {
        const dataStr = JSON.stringify(response.data.data, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.json`
        link.click()
        URL.revokeObjectURL(url)
      }
      
      alert(`Analytics data exported successfully!`)
    } catch (error) {
      console.error('Export error:', error)
      alert('Failed to export data')
    }
  }

  const renderMetricCard = (title, value, subtitle, icon, trend) => (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
      {trend !== undefined && (
        <div className={`metric-trend ${trend >= 0 ? 'positive' : 'negative'}`}>
          {trend >= 0 ? '↗️' : '↘️'} {Math.abs(trend)}%
        </div>
      )}
    </div>
  )

  // Skeleton Components
  const OverviewSkeleton = () => (
    <div className="analytics-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
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

  const NotificationsSkeleton = () => (
    <div className="analytics-tab-skeleton">
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

  const OperatorsSkeleton = () => (
    <div className="analytics-tab-skeleton">
      <div className="skeleton-team-metrics"></div>
      <div className="skeleton-leaderboard"></div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const AlertsSkeleton = () => (
    <div className="analytics-tab-skeleton">
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
      <div className="skeleton-severity"></div>
    </div>
  )

  const ResponseTimesSkeleton = () => (
    <div className="analytics-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-sla-grid"></div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const EscalationsSkeleton = () => (
    <div className="analytics-tab-skeleton">
      <div className="skeleton-metric-grid">
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
        <div className="skeleton-card"></div>
      </div>
      <div className="skeleton-reasons-grid"></div>
      <div className="skeleton-chart-grid">
        <div className="skeleton-chart"></div>
        <div className="skeleton-chart"></div>
      </div>
    </div>
  )

  const renderOverviewTab = () => {
    if (!analyticsData) return <OverviewSkeleton />

    // Handle different possible data structures
    const data = analyticsData.data || analyticsData
    const summary_metrics = data.summary_metrics || data

    return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Total Alerts', summary_metrics.total_alerts_processed || 0, 'Processed', '🎯')}
          {renderMetricCard('Avg Response Time', summary_metrics.avg_response_time || '0ms', 'Target: &lt; 10m', '⚡')}
          {renderMetricCard('Resolution Rate', `${summary_metrics.resolution_rate || 0}%`, 'Successfully resolved', '✅')}
          {renderMetricCard('Notification Success', `${summary_metrics.notification_delivery_rate || 0}%`, 'Delivery rate', '📧')}
          {renderMetricCard('SLA Compliance', `${summary_metrics.sla_compliance || 0}%`, 'Within targets', '🎯')}
          {renderMetricCard('Escalation Rate', `${summary_metrics.escalation_rate || 0}%`, 'Auto-escalated', '⬆️')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Alert Processing Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.alert_trends?.time_series || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="self_harm_detection" stroke="#dc2626" name="Critical Alerts" />
                <Line type="monotone" dataKey="pii_exposure" stroke="#f97316" name="PII Alerts" />
                <Line type="monotone" dataKey="toxicity_filter" stroke="#fbbf24" name="Other Alerts" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Performance Summary</h3>
            <div className="summary-stats">
              <div className="stat-item">
                <span className="stat-label">System Uptime</span>
                <span className="stat-value">{summary_metrics.system_uptime}%</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Operator Utilization</span>
                <span className="stat-value">{summary_metrics.operator_utilization}%</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Peak Response Time</span>
                <span className="stat-value">&lt; 5 minutes</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderNotificationsTab = () => {
    // 1. Check for null data FIRST
    if (!analyticsData) return <NotificationsSkeleton />

    // 2. Wrap the rest in try...catch for unexpected render errors
    try {
      const data = analyticsData.data || analyticsData
      if (!data || typeof data !== 'object') {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderNotificationsTab:", data)
        return <div className="analytics-loading">Processing notifications data...</div>
      }

    return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Delivery Rate', `${data.delivery_rate || 0}%`, 'Overall success', '📧')}
          {renderMetricCard('Total Sent', data.total_notifications_sent || 0, 'All channels', '📤')}
          {renderMetricCard('Email Rate', `${data.email_delivery_rate || 0}%`, 'Email delivery', '✉️')}
          {renderMetricCard('SMS Rate', `${data.sms_delivery_rate || 0}%`, 'SMS delivery', '📱')}
        </div>
        

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Notification Performance Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.time_series || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="emails_sent" stroke="#3b82f6" name="Emails Sent" />
                <Line type="monotone" dataKey="emails_delivered" stroke="#22c55e" name="Emails Delivered" />
                <Line type="monotone" dataKey="sms_sent" stroke="#f59e0b" name="SMS Sent" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Delivery Methods Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.notification_breakdown || []}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="delivered"
                  nameKey="method"
                  label={({method, rate}) => `${method}: ${rate}%`}
                >
                  {(analyticsData.notification_breakdown || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#22c55e', '#f59e0b'][index]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {analyticsData.failure_reasons && (
          <div className="failure-analysis">
            <h3>🔍 Delivery Failure Analysis</h3>
            <div className="failure-reasons">
              {(analyticsData.failure_reasons || []).map((reason, index) => (
                <div key={index} className="failure-item">
                  <span className="failure-reason">{reason.reason}</span>
                  <span className="failure-count">{reason.count} failures</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
    } catch (err) {
      console.error(`Error rendering ${activeTab} tab:`, err)
      return (
        <div className="analytics-error">
          <h3>Error displaying {activeTab} data</h3>
          <p>{err.message}</p>
        </div>
      )
    }
  }

  const renderOperatorsTab = () => {
    if (!analyticsData) return <OperatorsSkeleton />
    
    // Safe data access
    const data = getAnalyticsData()
    if (!data) return <div className="analytics-error">No operator data available</div>

    return (
      <div className="analytics-tab">
        <div className="team-metrics">
          <div className="team-summary">
            <h3>👥 Team Performance Summary</h3>
            <div className="team-stats">
              <div className="team-stat">
                <span className="stat-label">Active Operators</span>
                <span className="stat-value">{data.team_metrics?.active_operators || 0}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Total Alerts Handled</span>
                <span className="stat-value">{data.team_metrics?.total_alerts_handled || 0}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Team Avg Response</span>
                <span className="stat-value">{data.team_metrics?.average_response_time || '0ms'}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Top Performer</span>
                <span className="stat-value">{data.team_metrics?.top_performer || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="operator-leaderboard">
          <h3>🏆 Operator Performance Rankings</h3>
          <div className="leaderboard">
            {(data.operator_rankings || []).map((operator, index) => (
              <div key={index} className={`operator-card ${index < 3 ? 'top-performer' : ''}`}>
                <div className="operator-rank">#{index + 1}</div>
                <div className="operator-info">
                  <div className="operator-name">{operator.operator_name}</div>
                  <div className="operator-stats">
                    <span>Alerts: {operator.alerts_handled}</span>
                    <span>Response: {operator.avg_response_time_formatted}</span>
                    <span>Resolution: {operator.resolution_rate}%</span>
                  </div>
                </div>
                <div className="operator-score">{operator.performance_score}/10</div>
              </div>
            ))}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Workload Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.workload_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="operator" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="workload_percent" fill="#3b82f6" name="Workload %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Performance Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.performance_trends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="avg_response_time" stroke="#ef4444" name="Avg Response Time (s)" />
                <Line type="monotone" dataKey="resolution_rate" stroke="#22c55e" name="Resolution Rate %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    )
  }

  const renderAlertsTab = () => {
    // 1. Check for null data FIRST
    if (!analyticsData) return <AlertsSkeleton />

    // 2. Wrap the rest in try...catch for unexpected render errors
    try {
      const data = analyticsData.data || analyticsData
      if (!data || typeof data !== 'object') {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderAlertsTab:", data)
        return <div className="analytics-loading">Processing alert trends data...</div>
      }

      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Total Alerts', analyticsData.total_alerts, 'This period', '🚨')}
          {renderMetricCard('Most Common', safeGet(analyticsData, 'trend_analysis.most_common_type', 'N/A'), 'Alert type', '📊')}
          {renderMetricCard('Peak Hour', safeGet(analyticsData, 'peak_hours.peak_hour', 'N/A'), `${safeGet(analyticsData, 'peak_hours.peak_count', 0)} alerts`, '⏰')}
          {renderMetricCard('Weekly Change', `${safeGet(analyticsData, 'trend_analysis.week_over_week_change', 0)}%`, 'vs last week', '📈')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Alert Trends Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.time_series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="self_harm_detection" stroke="#dc2626" name="Self-Harm" />
                <Line type="monotone" dataKey="pii_exposure" stroke="#f97316" name="PII Exposure" />
                <Line type="monotone" dataKey="medical_misinformation" stroke="#fbbf24" name="Medical Info" />
                <Line type="monotone" dataKey="toxicity_filter" stroke="#3b82f6" name="Toxicity" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Alert Type Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.alert_breakdown || []}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="count"
                  nameKey="type"
                  label={({type, percentage}) => `${type}: ${percentage}%`}
                >
                  {(analyticsData.alert_breakdown || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#dc2626', '#f97316', '#fbbf24', '#3b82f6', '#22c55e'][index]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="severity-analysis">
          <h3>Severity Distribution</h3>
          <div className="severity-bars">
            {(analyticsData.severity_distribution || []).map((severity, index) => (
              <div key={index} className="severity-bar">
                <div className="severity-label" style={{ color: severity.color }}>
                  {severity.severity}
                </div>
                <div className="severity-progress">
                  <div
                    className="severity-fill"
                    style={{
                      width: `${(severity.count / Math.max(...(analyticsData.severity_distribution || []).map(s => s.count))) * 100}%`,
                      backgroundColor: severity.color
                    }}
                  ></div>
                </div>
                <div className="severity-count">{severity.count}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
    } catch (err) {
      console.error(`Error rendering ${activeTab} tab:`, err)
      return (
        <div className="analytics-error">
          <h3>Error displaying {activeTab} data</h3>
          <p>{err.message}</p>
        </div>
      )
    }
  }

  const renderResponseTimesTab = () => {
    // 1. Check for null data FIRST
    if (!analyticsData) return <ResponseTimesSkeleton />

    // 2. Wrap the rest in try...catch for unexpected render errors
    try {
      const responseData = analyticsData.data || analyticsData
      if (!responseData || typeof responseData !== 'object') {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderResponseTimesTab:", responseData)
        return <div className="analytics-loading">Processing response times data...</div>
      }

      // Format fastest response time
      const formatResponseTime = (minutes) => {
        if (!minutes && minutes !== 0) return 'N/A'
        if (minutes < 1) {
          const seconds = Math.round(minutes * 60)
          return `${seconds}s`
        } else if (minutes < 60) {
          const mins = Math.floor(minutes)
          const secs = Math.round((minutes - mins) * 60)
          return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`
        } else {
          const hours = Math.floor(minutes / 60)
          const mins = Math.round(minutes % 60)
          return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
        }
      }
      
      // Get data from summary or top level
      const summary = responseData.summary || {}
      const fastestTime = summary.fastest_response_time_minutes
      const improvement = summary.improvement_percentage
      const overallAvg = summary.average_response_time || analyticsData.overall_avg_response_time

      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Overall Avg', formatResponseTime(overallAvg), 'Response time', '⏱️')}
          {renderMetricCard('SLA Compliance', `${analyticsData.sla_compliance_rate || 0}%`, 'Within targets', '🎯')}
          {renderMetricCard('Fastest Response', formatResponseTime(fastestTime), 'Best time', '🚀')}
          {renderMetricCard('Improvement', improvement !== null && improvement !== undefined ? `${improvement >= 0 ? '+' : ''}${improvement}%` : 'N/A', 'vs last period', '📈')}
        </div>

        <div className="sla-targets">
          <h3>🎯 SLA Performance by Severity</h3>
          <div className="sla-grid">
            {(analyticsData.sla_targets || []).map((sla, index) => (
              <div key={index} className={`sla-card ${sla.status}`}>
                <div className="sla-severity">{sla.severity}</div>
                <div className="sla-times">
                  <div className="sla-target">Target: {sla.target_formatted}</div>
                  <div className="sla-actual">Actual: {sla.avg_response_formatted}</div>
                </div>
                <div className="sla-compliance">{sla.compliance_rate}%</div>
                <div className={`sla-status-indicator ${sla.status}`}></div>
              </div>
            ))}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Response Times Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.time_series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="avg_response_time" stroke="#3b82f6" name="Avg Response (s)" />
                <Line type="monotone" dataKey="critical_response_time" stroke="#dc2626" name="Critical Response (s)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Response Time Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.response_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#22c55e" name="Alert Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    )
    } catch (err) {
      console.error(`Error rendering ${activeTab} tab:`, err)
      return (
        <div className="analytics-error">
          <h3>Error displaying {activeTab} data</h3>
          <p>{err.message}</p>
        </div>
      )
    }
  }

  const renderEscalationsTab = () => {
    // 1. Check for null data FIRST
    if (!analyticsData) return <EscalationsSkeleton />

    // 2. Wrap the rest in try...catch for unexpected render errors
    try {
      const data = analyticsData.data || analyticsData
      if (!data || typeof data !== 'object') {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderEscalationsTab:", data)
        return <div className="analytics-loading">Processing escalations data...</div>
      }

      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Total Escalations', analyticsData.total_escalations || 0, 'This period', '⬆️')}
          {renderMetricCard('Auto-Escalation', `${analyticsData.auto_escalation_percentage || 0}%`, 'Automated', '⚙️')}
          {renderMetricCard('Escalation Rate', `${analyticsData.escalation_rate || 0}%`, 'Of all alerts', '📊')}
          {renderMetricCard('Avg Time', safeGet(analyticsData, 'avg_time_to_escalation', 'N/A'), 'To escalate', '⏱️')}
        </div>

        <div className="escalation-reasons">
          <h3>📋 Escalation Reasons</h3>
          <div className="reasons-grid">
            {(analyticsData.escalation_reasons || []).map((reason, index) => (
              <div key={index} className="reason-card">
                <div className="reason-name">{reason.reason}</div>
                <div className="reason-stats">
                  <span className="reason-count">{reason.count}</span>
                  <span className="reason-percentage">{reason.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Escalation Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.time_series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="total_escalations" stroke="#f97316" name="Total Escalations" />
                <Line type="monotone" dataKey="auto_escalations" stroke="#3b82f6" name="Auto Escalations" />
                <Line type="monotone" dataKey="manual_escalations" stroke="#22c55e" name="Manual Escalations" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Supervisor Response Performance</h3>
            <div className="supervisor-metrics">
              <div className="supervisor-metric">
                <span className="metric-label">Avg Response Time</span>
                <span className="metric-value">{analyticsData.supervisor_response?.avg_supervisor_response_time || 'N/A'}</span>
              </div>
              <div className="supervisor-metric">
                <span className="metric-label">Resolution Rate</span>
                <span className="metric-value">{analyticsData.supervisor_response?.supervisor_resolution_rate || 0}%</span>
              </div>
              <div className="supervisor-metric">
                <span className="metric-label">Fastest Escalation</span>
                <span className="metric-value">{analyticsData.escalation_timing?.fastest_escalation || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
    } catch (err) {
      console.error(`Error rendering ${activeTab} tab:`, err)
      return (
        <div className="analytics-error">
          <h3>Error displaying {activeTab} data</h3>
          <p>{err.message}</p>
        </div>
      )
    }
  }

  if (loading) {
    return <div className="analytics-loading">Loading analytics dashboard...</div>
  }

  if (error) {
    return <div className="analytics-error">{error}</div>
  }


  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div className="header-left">
          <h1>📊 Analytics Dashboard</h1>
          <p className="header-subtitle">
            Comprehensive insights into alert management performance • Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        
        <div className="header-controls">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="time-range-select"
          >
            {timeRanges.map(range => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
          
          
          <button
            onClick={() => exportData('json')}
            className="export-btn"
          >
            📤 Export
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="analytics-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => handleTabClick(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="analytics-content">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'notifications' && renderNotificationsTab()}
        {activeTab === 'operators' && renderOperatorsTab()}
        {activeTab === 'alerts' && renderAlertsTab()}
        {activeTab === 'response' && renderResponseTimesTab()}
        {activeTab === 'escalations' && renderEscalationsTab()}
      </div>
    </div>
  )
}

export default Analytics
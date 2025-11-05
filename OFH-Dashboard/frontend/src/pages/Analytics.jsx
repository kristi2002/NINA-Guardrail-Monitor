import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import TimeAgo from '../components/TimeAgo'
import './Analytics.css'

function Analytics() {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [timeRange, setTimeRange] = useState('7d')
  const [lastUpdated, setLastUpdated] = useState(new Date())
  
  // ✅ Refs to track the *previous* state
  const prevTimeRange = useRef(timeRange)
  const prevActiveTab = useRef(activeTab)
  const isInitialMount = useRef(true)
  const abortControllerRef = useRef(null)
  const requestIdRef = useRef(0)


  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'notifications', label: 'Notifications', icon: '📧' },
    { id: 'operators', label: 'Users', icon: '👥' },
    { id: 'alerts', label: 'Alert Trends', icon: '📈' },
    { id: 'response', label: 'Response Times', icon: '⏱️' },
    { id: 'escalations', label: 'Escalations', icon: '⬆️' }
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
    // Generate a unique request ID for this effect run
    const currentRequestId = ++requestIdRef.current
    const isInitial = isInitialMount.current
    
    console.log(`[ANALYTICS] Effect running - Request ID: ${currentRequestId}, Tab: ${activeTab}, TimeRange: ${timeRange}, IsInitial: ${isInitial}`)
    
    // 1. Check what changed BEFORE creating a new controller
    const timeRangeChanged = prevTimeRange.current !== timeRange
    const tabChanged = prevActiveTab.current !== activeTab
    
    // 2. In React StrictMode, the second run happens immediately after the first
    // We should NOT abort the first request if we're still in the initial mount phase
    // Only abort if it's a real dependency change (timeRange or activeTab actually changed)
    const shouldAbortPrevious = !isInitial && (timeRangeChanged || tabChanged)
    
    if (abortControllerRef.current && shouldAbortPrevious) {
      console.log('[ANALYTICS] Aborting previous request due to dependency change')
      abortControllerRef.current.abort()
    } else if (abortControllerRef.current) {
      // Don't abort if it's initial mount OR if there are no changes (StrictMode double-run)
      console.log('[ANALYTICS] Skipping abort - initial mount or no changes (React StrictMode protection)')
    }

    // 3. Create a new AbortController for this request
    const controller = new AbortController()
    abortControllerRef.current = controller
    const signal = controller.signal

    console.log(`[ANALYTICS] Changes - Initial: ${isInitial}, TimeRangeChanged: ${timeRangeChanged}, TabChanged: ${tabChanged}`)

    // 4. Update refs BEFORE making the request to prevent re-triggers
    prevTimeRange.current = timeRange
    prevActiveTab.current = activeTab

    // 5. Decide on loading state and fetch
    // ALWAYS fetch on initial mount, or when something actually changed
    if (isInitial) {
      // This is the initial mount - always fetch with full loader
      console.log('[ANALYTICS] Initial mount - fetching with loader')
      isInitialMount.current = false
      fetchAnalyticsData(true, signal)
    } else if (timeRangeChanged || tabChanged) {
      // Something actually changed - fetch with appropriate loader
      if (timeRangeChanged) {
        console.log('[ANALYTICS] Time range changed - fetching with loader')
        fetchAnalyticsData(true, signal)
      } else {
        console.log('[ANALYTICS] Tab changed - fetching with skeleton')
        setAnalyticsData(null)
        fetchAnalyticsData(false, signal)
      }
    } else {
      // No changes detected - this is likely React StrictMode double-run
      // BUT if we already aborted the previous request, we need to fetch again
      // Check if we have data - if not, we need to fetch (the previous one was aborted)
      if (!analyticsData) {
        console.log('[ANALYTICS] No changes but no data - fetching (previous request was likely aborted)')
        fetchAnalyticsData(true, signal)
      } else {
        console.log('[ANALYTICS] No changes detected - skipping fetch (likely React StrictMode double-run, data already exists)')
      }
    }

    // 6. Set up the interval
    const interval = setInterval(() => {
      console.log('[ANALYTICS] Auto-refreshing analytics data...')
      // Auto-refresh is always silent, no signal or loader needed
      fetchAnalyticsData(false)
    }, 300000) // 5 minutes

    // 7. Return cleanup function
    return () => {
      console.log('🧹 Cleaning up Analytics: checking if abort needed...')
      // In React StrictMode, effects run twice on mount
      // The first cleanup should NOT abort - let the second request complete
      // Only abort if:
      // 1. This is still the current controller/request
      // 2. It's NOT the initial mount (to handle StrictMode double-run)
      const isStillCurrent = abortControllerRef.current === controller && requestIdRef.current === currentRequestId
      
      // For initial mount, never abort (React StrictMode protection)
      if (isInitial) {
        console.log('[ANALYTICS] Skipping abort on initial mount cleanup (React StrictMode protection)')
      } else if (isStillCurrent) {
        // Only abort if it's a real dependency change, not initial mount
        console.log('[ANALYTICS] Aborting request due to dependency change')
        controller.abort()
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null
        }
      }
      clearInterval(interval)
    }
  }, [timeRange, activeTab]) // ✅ DEPENDS ON BOTH

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

  const fetchAnalyticsData = async (showLoadingSpinner = true, signal = null) => {
    console.log(`[ANALYTICS] fetchAnalyticsData called - showLoading: ${showLoadingSpinner}, tab: ${activeTab}, timeRange: ${timeRange}`)
    
    // Check if request was already aborted before starting
    if (signal && signal.aborted) {
      console.log('[ANALYTICS] Request already aborted, skipping fetch')
      return
    }
    
    try {
      if (showLoadingSpinner) {
        console.log('[ANALYTICS] Setting loading to true')
        setLoading(true) // Show full-page loader (for time range changes)
      }
      setError(null) // Always clear old errors on a new fetch

      // Build the request config with abort signal
      const config = signal ? { signal } : {}

      let response
      const endpoint = `/api/analytics/${activeTab === 'overview' ? 'overview' : activeTab === 'operators' ? 'operators' : activeTab === 'notifications' ? 'notifications' : activeTab === 'alerts' ? 'alert-trends' : activeTab === 'response' ? 'response-times' : 'escalations'}?timeRange=${timeRange}`
      console.log(`[ANALYTICS] Making request to: ${endpoint}`)
      
      // This switch statement is the same as you had
      switch (activeTab) {
        case 'overview':
          response = await axios.get(`/api/analytics/overview?timeRange=${timeRange}`, config)
          break
        case 'notifications':
          response = await axios.get(`/api/analytics/notifications?timeRange=${timeRange}`, config)
          break
        case 'operators':
          response = await axios.get(`/api/analytics/operators?timeRange=${timeRange}`, config)
          break
        case 'alerts':
          response = await axios.get(`/api/analytics/alert-trends?timeRange=${timeRange}`, config)
          break
        case 'response':
          response = await axios.get(`/api/analytics/response-times?timeRange=${timeRange}`, config)
          break
        case 'escalations':
          response = await axios.get(`/api/analytics/escalations?timeRange=${timeRange}`, config)
          break
        default:
          response = await axios.get(`/api/analytics/overview?timeRange=${timeRange}`, config)
      }

      // Handle both direct data and wrapped responses with safe fallbacks
      let data = null
      if (response.data.success && response.data.data) {
        data = response.data.data
      } else if (response.data) {
        data = response.data
      }

      // Ensure data has required structure with safe defaults
      // Even if data is empty {}, we still create safeData with defaults
      const safeData = {
        ...(data || {}),
        // Defaults for Overview tab
        alerts: (data && data.alerts) || {},
        conversations: (data && data.conversations) || {},
        users: (data && data.users) || {},
        system_health: (data && data.system_health) || {},
        // Defaults for other tabs
        notification_breakdown: (data && data.notification_breakdown) || [],
        trends: (data && data.trends) || [],
        response_times: (data && data.response_times) || [],
        escalation_trends: (data && data.escalation_trends) || [],
        alert_breakdown: (data && data.alert_breakdown) || [],
        sla_targets: (data && data.sla_targets) || [],
        escalation_reasons: (data && data.escalation_reasons) || [],
        trend_analysis: (data && data.trend_analysis) || { most_common_type: 'N/A', week_over_week_change: 0 },
        peak_hours: (data && data.peak_hours) || { peak_hour: 'N/A', peak_count: 0 },
        severity_distribution: (data && data.severity_distribution) || [],
        failure_reasons: (data && data.failure_reasons) || [],
        supervisor_response: (data && data.supervisor_response) || { avg_supervisor_response_time: 'N/A', supervisor_resolution_rate: 0 },
        escalation_timing: (data && data.escalation_timing) || { fastest_escalation: 'N/A' },
        overall_avg_response_time: (data && data.overall_avg_response_time) || 'N/A',
        sla_compliance_rate: (data && data.sla_compliance_rate) || 0,
        total_escalations: (data && data.total_escalations) || 0,
        auto_escalation_percentage: (data && data.auto_escalation_percentage) || 0,
        escalation_rate: (data && data.escalation_rate) || 0
      }
      console.log('[ANALYTICS] Data fetched successfully, setting analyticsData')
      setAnalyticsData(safeData)
      setLastUpdated(new Date())
    } catch (err) {
      console.log(`[ANALYTICS] Error in fetchAnalyticsData:`, err)
      // Don't set error if request was intentionally cancelled
      if (err.name === 'CanceledError' || axios.isCancel(err)) {
        console.log('[ANALYTICS] Request was cancelled - ignoring')
        // Don't update any state if request was cancelled
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
      // Set empty data structure to prevent crashes
      setAnalyticsData({})
    } finally {
      // Only clear loading state if request wasn't cancelled
      // Check if signal was aborted before updating state
      if (signal && !signal.aborted) {
        setLoading(false)
      } else if (!signal) {
        // No signal means it's an auto-refresh, always clear loading
        setLoading(false)
      }
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
    // 1. Check for null data FIRST (this means "we are fetching")
    // Only show skeleton if loading is false (means it's a tab switch, not initial load)
    if (!analyticsData && !loading) return <OverviewSkeleton />
    
    // 2. If data is null but loading is true, return null (full-page loader will show)
    if (!analyticsData && loading) return null
    
    // 3. Even if data is empty, still render the structure with defaults so layout is preserved
    // Don't show "No data" message - let the components render with default values

    // 4. Wrap the rest in a try...catch
    try {
      // Backend returns: {alerts: {...}, conversations: {...}, users: {...}, system_health: {...}}
      const data = analyticsData.data || analyticsData
      const alerts = data.alerts || {}
      const conversations = data.conversations || {}
      const users = data.users || {}
      const systemHealth = data.system_health || {}

      // Calculate metrics from backend data
      const totalAlerts = alerts.total || 0
      const avgResponseTime = systemHealth.alert_response_time || 0
      const avgResponseTimeFormatted = avgResponseTime < 1 ? `${Math.round(avgResponseTime * 60)}s` : `${Math.round(avgResponseTime)}m`
      const activeConversations = conversations.active || 0
      const totalConversations = conversations.total || 0
      const resolutionRate = totalConversations > 0 ? Math.round(((totalConversations - activeConversations) / totalConversations) * 100) : 0
      const escalationRate = systemHealth.conversation_escalation_rate || 0

      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Total Alerts', totalAlerts, 'Processed', '🎯')}
          {renderMetricCard('Avg Response Time', avgResponseTimeFormatted, 'Target: < 10m', '⚡')}
          {renderMetricCard('Resolution Rate', `${resolutionRate}%`, 'Successfully resolved', '✅')}
          {renderMetricCard('Active Conversations', activeConversations, 'Currently active', '💬')}
          {renderMetricCard('High Risk Conversations', conversations.high_risk || 0, 'Requiring attention', '🚨')}
          {renderMetricCard('Escalation Rate', `${Math.round(escalationRate * 100)}%`, 'Auto-escalated', '⬆️')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Alert Distribution by Severity</h3>
            {Object.keys(alerts.severity_distribution || {}).length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(alerts.severity_distribution || {}).map(([severity, count]) => ({ name: severity, value: count }))}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    nameKey="name"
                    label={({name, value}) => `${name}: ${value}`}
                  >
                    {Object.entries(alerts.severity_distribution || {}).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['#dc2626', '#f97316', '#fbbf24', '#3b82f6'][index % 4]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-placeholder">No severity distribution data available</div>
            )}
          </div>

          <div className="chart-container">
            <h3>Performance Summary</h3>
            <div className="summary-stats">
              <div className="stat-item">
                <span className="stat-label">Total Conversations</span>
                <span className="stat-value">{totalConversations}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Active Users</span>
                <span className="stat-value">{users.active || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Average Duration</span>
                <span className="stat-value">{Math.round(conversations.average_duration || 0)}m</span>
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

  const renderNotificationsTab = () => {
    // 1. Check for null data FIRST (this means "we are fetching")
    if (!analyticsData) return <NotificationsSkeleton />
    
    // 2. Check for empty data SECOND (this means "fetch finished, nothing found")
    if (Object.keys(analyticsData).length === 0) {
      return <div className="analytics-loading">No notifications data available. Try refreshing.</div>
    }

    // 3. Wrap the rest in a try...catch
    try {
      const data = analyticsData.data || analyticsData
      if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderNotificationsTab:", data)
        return <div className="analytics-loading">Processing notifications data...</div>
      }

    // Backend returns: {total_notifications, by_type, by_status, notification_breakdown, trends}
    const totalNotifications = data.total_notifications || 0
    const byStatus = data.by_status || {}
    const sentCount = byStatus.sent || 0
    const pendingCount = byStatus.pending || 0
    const deliveryRate = totalNotifications > 0 ? Math.round((sentCount / totalNotifications) * 100) : 0

    return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Delivery Rate', `${deliveryRate}%`, 'Overall success', '📧')}
          {renderMetricCard('Total Sent', sentCount, 'All channels', '📤')}
          {renderMetricCard('Pending', pendingCount, 'Awaiting delivery', '⏳')}
          {renderMetricCard('Total Notifications', totalNotifications, 'This period', '📊')}
        </div>
        

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Notification Trends Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.trends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" name="Notifications" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Delivery Methods Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.notification_breakdown || []}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="delivered"
                  nameKey="method"
                  label={({method, rate}) => `${method}: ${rate}%`}
                >
                  {(data.notification_breakdown || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#22c55e', '#f59e0b'][index % 3]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="status-breakdown">
          <h3>📊 Status Breakdown</h3>
          <div className="status-grid">
            {Object.entries(byStatus).map(([status, count]) => {
              const statusLower = status.toLowerCase()
              return (
                <div key={status} className={`status-card status-${statusLower}`}>
                  <div className="status-name">{status}</div>
                  <div className="status-count">{count}</div>
                </div>
              )
            })}
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

  const renderOperatorsTab = () => {
    // 1. Check for null data FIRST (this means "we are fetching")
    if (!analyticsData) return <OperatorsSkeleton />
    
    // 2. Check for empty data SECOND (this means "fetch finished, nothing found")
    if (Object.keys(analyticsData).length === 0) {
      return <div className="analytics-loading">No users data available. Try refreshing.</div>
    }

    // 3. Wrap the rest in a try...catch
    try {
      // Backend returns: {summary: {...}, distributions: {...}, performance_metrics: {...}, recent_activity: [...]}
      const data = analyticsData.data || analyticsData
      const summary = data.summary || {}
      const distributions = data.distributions || {}
      const performanceMetrics = data.performance_metrics || {}
      const roleDistribution = distributions.by_role || {}

      return (
      <div className="analytics-tab">
        <div className="team-metrics">
          <div className="team-summary">
            <h3>👥 Team Performance Summary</h3>
            <div className="team-stats">
              <div className="team-stat">
                <span className="stat-label">Total Users</span>
                <span className="stat-value">{summary.total_users || 0}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Active Users</span>
                <span className="stat-value">{summary.active_users || 0}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Recent Logins</span>
                <span className="stat-value">{summary.recent_logins || 0}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Avg Session Duration</span>
                <span className="stat-value">{Math.round(performanceMetrics.average_session_duration || 0)}m</span>
              </div>
            </div>
          </div>
        </div>

        <div className="role-distribution">
          <h3>📊 Role Distribution</h3>
          <div className="role-grid">
            {Object.entries(roleDistribution).map(([role, count]) => (
              <div key={role} className="role-card">
                <div className="role-name">{role}</div>
                <div className="role-count">{count}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>User Activity Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.recent_activity || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="active_users" stroke="#3b82f6" name="Active Users" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Role Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(roleDistribution).map(([role, count]) => ({ name: role, value: count }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  nameKey="name"
                  label={({name, value}) => `${name}: ${value}`}
                >
                  {Object.entries(roleDistribution).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#22c55e', '#f59e0b', '#dc2626'][index % 4]} />
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
      console.error(`Error rendering ${activeTab} tab:`, err)
      return (
        <div className="analytics-error">
          <h3>Error displaying {activeTab} data</h3>
          <p>{err.message}</p>
        </div>
      )
    }
  }

  const renderAlertsTab = () => {
    // 1. Check for null data FIRST (this means "we are fetching")
    if (!analyticsData) return <AlertsSkeleton />
    
    // 2. Check for empty data SECOND (this means "fetch finished, nothing found")
    if (Object.keys(analyticsData).length === 0) {
      return <div className="analytics-loading">No alert trends data available. Try refreshing.</div>
    }

    // 3. Wrap the rest in a try...catch
    try {
      const data = analyticsData.data || analyticsData
      if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderAlertsTab:", data)
        return <div className="analytics-loading">Processing alert trends data...</div>
      }

      // Get data from the correct structure
      const summary = data.summary || {}
      const distributions = data.distributions || {}
      const performanceMetrics = data.performance_metrics || {}
      
      // Calculate most common event type from distributions
      const eventTypes = distributions.by_event_type || {}
      const mostCommonType = Object.keys(eventTypes).reduce((a, b) => eventTypes[a] > eventTypes[b] ? a : b, 'N/A') || 'N/A'
      
      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Total Alerts', summary.total_alerts || 0, 'This period', '🚨')}
          {renderMetricCard('Critical Alerts', summary.critical_alerts || 0, 'High priority', '⚠️')}
          {renderMetricCard('Active Alerts', summary.active_alerts || 0, 'Currently open', '📊')}
          {renderMetricCard('Most Common Type', mostCommonType, 'Event type', '📈')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Alert Trends Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceMetrics.resolution_time_trends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="average_resolution_time_minutes" stroke="#dc2626" name="Avg Resolution (min)" />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" name="Alert Count" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Alert Type Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(eventTypes).map(([type, count]) => ({ type, count }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="count"
                  nameKey="type"
                  label={({type, count}) => `${type}: ${count}`}
                >
                  {Object.entries(eventTypes).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#dc2626', '#f97316', '#fbbf24', '#3b82f6', '#22c55e'][index % 5]} />
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
            {Object.entries(distributions.by_severity || {}).map(([severity, count], index) => {
              const colors = { 'CRITICAL': '#dc2626', 'critical': '#dc2626', 'HIGH': '#f97316', 'high': '#f97316', 'MEDIUM': '#fbbf24', 'medium': '#fbbf24', 'LOW': '#22c55e', 'low': '#22c55e' }
              const maxCount = Math.max(...Object.values(distributions.by_severity || {}))
              return (
                <div key={index} className="severity-bar">
                  <div className="severity-label" style={{ color: colors[severity] || '#64748b' }}>
                    {severity}
                  </div>
                  <div className="severity-progress">
                    <div
                      className="severity-fill"
                      style={{
                        width: `${maxCount > 0 ? (count / maxCount) * 100 : 0}%`,
                        backgroundColor: colors[severity] || '#64748b'
                      }}
                    ></div>
                  </div>
                  <div className="severity-count">{count}</div>
                </div>
              )
            })}
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
    // 1. Check for null data FIRST (this means "we are fetching")
    if (!analyticsData) return <ResponseTimesSkeleton />
    
    // 2. Check for empty data SECOND (this means "fetch finished, nothing found")
    if (Object.keys(analyticsData).length === 0) {
      return <div className="analytics-loading">No response times data available. Try refreshing.</div>
    }

    // 3. Wrap the rest in a try...catch
    try {
      const responseData = analyticsData.data || analyticsData
      if (!responseData || typeof responseData !== 'object' || Object.keys(responseData).length === 0) {
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
      const performanceMetrics = responseData.performance_metrics || {}
      const fastestTime = summary.fastest_response_time_minutes
      const improvement = summary.improvement_percentage
      const overallAvg = summary.average_response_time || 0
      const avgResolution = summary.average_resolution_time || 0
      const responseTimeBySeverity = performanceMetrics.response_time_by_severity || {}
      const resolutionTrends = performanceMetrics.resolution_time_trends || []

      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('Overall Avg', formatResponseTime(overallAvg), 'Response time', '⏱️')}
          {renderMetricCard('Avg Resolution', formatResponseTime(avgResolution), 'Resolution time', '✅')}
          {renderMetricCard('Fastest Response', formatResponseTime(fastestTime), 'Best time', '🚀')}
          {renderMetricCard('Improvement', improvement !== null && improvement !== undefined ? `${improvement >= 0 ? '+' : ''}${improvement}%` : 'N/A', 'vs last period', '📈')}
        </div>

        <div className="sla-targets">
          <h3>🎯 Response Time by Severity</h3>
          <div className="sla-grid">
            {Object.entries(responseTimeBySeverity).map(([severity, timeMinutes], index) => (
              <div key={index} className="sla-card">
                <div className="sla-severity">{severity}</div>
                <div className="sla-times">
                  <div className="sla-actual">Avg: {formatResponseTime(timeMinutes)}</div>
                </div>
              </div>
            ))}
            {Object.keys(responseTimeBySeverity).length === 0 && (
              <div className="sla-card">No response time data available</div>
            )}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Response Times Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={resolutionTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="average_resolution_time_minutes" stroke="#3b82f6" name="Avg Resolution (min)" />
                <Line type="monotone" dataKey="count" stroke="#dc2626" name="Alert Count" />
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
    // 1. Check for null data FIRST (this means "we are fetching")
    if (!analyticsData) return <EscalationsSkeleton />
    
    // 2. Check for empty data SECOND (this means "fetch finished, nothing found")
    if (Object.keys(analyticsData).length === 0) {
      return <div className="analytics-loading">No escalations data available. Try refreshing.</div>
    }

    // 3. Wrap the rest in a try...catch
    try {
      // Backend returns: {summary: {...}, distributions: {...}, quality_metrics: {...}, recent_conversations: [...]}
      const data = analyticsData.data || analyticsData
      if (!data || typeof data !== 'object') {
        // Handle unexpected data structure
        console.warn("Unexpected data structure in renderEscalationsTab:", data)
        return <div className="analytics-loading">Processing escalations data...</div>
      }

      const summary = data.summary || {}
      const escalationRate = summary.escalation_rate || 0
      const highRiskConversations = summary.high_risk_conversations || 0
      const totalConversations = summary.total_conversations || 0

      return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('High Risk Conversations', highRiskConversations, 'Requiring escalation', '🚨')}
          {renderMetricCard('Escalation Rate', `${Math.round(escalationRate * 100)}%`, 'Of all conversations', '📊')}
          {renderMetricCard('Total Conversations', totalConversations, 'This period', '💬')}
          {renderMetricCard('Active Conversations', summary.active_conversations || 0, 'Currently active', '⚡')}
        </div>

        <div className="risk-distribution">
          <h3>📊 Risk Level Distribution</h3>
          <div className="risk-grid">
            {Object.entries(data.distributions?.by_risk_level || {}).map(([risk, count]) => {
              const riskLower = risk.toLowerCase()
              return (
                <div key={risk} className={`risk-card risk-${riskLower}`}>
                  <div className="risk-name">{risk}</div>
                  <div className="risk-count">{count}</div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Conversation Status Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(data.distributions?.by_status || {}).map(([status, count]) => ({ name: status, value: count }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  nameKey="name"
                  label={({name, value}) => `${name}: ${value}`}
                >
                  {Object.entries(data.distributions?.by_status || {}).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#3b82f6', '#22c55e', '#f59e0b', '#dc2626'][index % 4]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Recent Conversations</h3>
            <div className="recent-conversations">
              {(data.recent_conversations || []).slice(0, 10).map((conv, index) => {
                const riskLower = (conv.risk_level || '').toLowerCase()
                return (
                  <div key={index} className={`conversation-item conv-risk-${riskLower}`}>
                    <div className="conv-id">ID: {conv.id}</div>
                    <div className="conv-risk">Risk: {conv.risk_level || 'N/A'}</div>
                    <div className="conv-status">Status: {conv.status || 'N/A'}</div>
                  </div>
                )
              })}
              {(data.recent_conversations || []).length === 0 && (
                <div className="no-data">No recent conversations</div>
              )}
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

  // Only show full-page loading for initial load
  if (loading && !analyticsData) {
    return <div className="analytics-loading">Loading analytics dashboard...</div>
  }


  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div className="header-left">
          <h1>📊 Analytics Dashboard</h1>
          <p className="header-subtitle">
            Comprehensive insights into alert management performance • Last updated: <TimeAgo timestamp={lastUpdated} />
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
        {error && (
          <div className="analytics-error-banner" style={{ padding: '1rem', background: '#fee', color: '#c33', marginBottom: '1rem', borderRadius: '4px' }}>
            ⚠️ {error}
            <button onClick={() => { setError(null); fetchAnalyticsData(); }} style={{ marginLeft: '1rem', padding: '0.25rem 0.5rem' }}>Retry</button>
          </div>
        )}
        {loading && analyticsData && (
          <div className="analytics-loading-indicator" style={{ padding: '1rem', textAlign: 'center' }}>Loading {activeTab} data...</div>
        )}
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
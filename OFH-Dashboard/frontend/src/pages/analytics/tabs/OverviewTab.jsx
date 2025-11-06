/**
 * Overview Tab Component
 */
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import MetricCard from './MetricCard'

export default function OverviewTab({ data, loading, renderMetricCard }) {
  if (!data && !loading) {
    return (
      <div className="analytics-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }
  
  if (!data && loading) return null

  try {
    const alerts = data.alerts || {}
    const conversations = data.conversations || {}
    const users = data.users || {}
    const systemHealth = data.system_health || {}

    const totalAlerts = alerts.total || 0
    const avgResponseTime = systemHealth.alert_response_time || 0
    const avgResponseTimeFormatted = avgResponseTime < 1 
      ? `${Math.round(avgResponseTime * 60)}s` 
      : `${Math.round(avgResponseTime)}m`
    const activeConversations = conversations.active || 0
    const totalConversations = conversations.total || 0
    const resolutionRate = totalConversations > 0 
      ? Math.round(((totalConversations - activeConversations) / totalConversations) * 100) 
      : 0
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
    console.error(`Error rendering overview tab:`, err)
    return (
      <div className="analytics-error">
        <h3>Error displaying overview data</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


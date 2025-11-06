/**
 * Alert Trends Tab Component
 */
import { LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function AlertsTab({ data, loading, renderMetricCard }) {
  if (!data) {
    return (
      <div className="analytics-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
        <div className="skeleton-severity"></div>
      </div>
    )
  }

  if (Object.keys(data).length === 0) {
    return <div className="analytics-loading">No alert trends data available. Try refreshing.</div>
  }

  try {
    const data_processed = data.data || data
    const summary = data_processed.summary || {}
    const distributions = data_processed.distributions || {}
    const performanceMetrics = data_processed.performance_metrics || {}
    
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
    console.error(`Error rendering alerts tab:`, err)
    return (
      <div className="analytics-error">
        <h3>Error displaying alert trends data</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


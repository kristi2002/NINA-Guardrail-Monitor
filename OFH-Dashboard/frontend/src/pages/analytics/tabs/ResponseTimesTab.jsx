/**
 * Response Times Tab Component
 */
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

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

export default function ResponseTimesTab({ data, loading, renderMetricCard }) {
  if (!data) {
    return (
      <div className="analytics-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-sla-grid"></div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  if (Object.keys(data).length === 0) {
    return <div className="analytics-loading">No response times data available. Try refreshing.</div>
  }

  try {
    const responseData = data.data || data
    if (!responseData || typeof responseData !== 'object' || Object.keys(responseData).length === 0) {
      return <div className="analytics-loading">Processing response times data...</div>
    }

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
          <h3>SLA Compliance</h3>
          <div className="sla-grid">
            {Object.entries(responseData.sla_targets || {}).map(([severity, sla]) => {
              const compliance = sla.compliance_rate || 0
              const status = compliance >= 95 ? 'good' : compliance >= 80 ? 'warning' : 'critical'
              return (
                <div key={severity} className={`sla-card ${status}`}>
                  <div className="sla-severity">{severity}</div>
                  <div className="sla-times">
                    <span className="sla-target">Target: {sla.target_time || 'N/A'}</span>
                    <span className="sla-actual">Actual: {sla.actual_time || 'N/A'}</span>
                  </div>
                  <div className="sla-compliance">{compliance}%</div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Response Time Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={resolutionTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="response_time" stroke="#3b82f6" name="Response Time" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Response Time by Severity</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.entries(responseTimeBySeverity).map(([severity, time]) => ({ severity, time }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="time" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering response times tab:`, err)
    return (
      <div className="analytics-error">
        <h3>Error displaying response times data</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


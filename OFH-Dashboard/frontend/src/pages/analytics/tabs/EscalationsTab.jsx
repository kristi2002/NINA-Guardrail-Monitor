/**
 * Escalations Tab Component
 */
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function EscalationsTab({ data, loading, renderMetricCard }) {
  if (!data) {
    return (
      <div className="analytics-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-reasons-grid"></div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  if (Object.keys(data).length === 0) {
    return <div className="analytics-loading">No escalations data available. Try refreshing.</div>
  }

  try {
    const data_processed = data.data || data
    if (!data_processed || typeof data_processed !== 'object' || Object.keys(data_processed).length === 0) {
      return <div className="analytics-loading">Processing escalations data...</div>
    }

    const summary = data_processed.summary || {}
    const highRiskConversations = summary.high_risk_conversations || 0
    const totalConversations = summary.total_conversations || 0
    const escalationRate = totalConversations > 0 
      ? (highRiskConversations / totalConversations) 
      : 0

    return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {renderMetricCard('High Risk Conversations', highRiskConversations, 'Requiring escalation', '🚨')}
          {renderMetricCard('Escalation Rate', `${Math.round(escalationRate * 100)}%`, 'Of all conversations', '📊')}
          {renderMetricCard('Total Conversations', totalConversations, 'This period', '💬')}
          {renderMetricCard('Active Conversations', summary.active_conversations || 0, 'Currently active', '⚡')}
        </div>

        <div className="escalation-reasons">
          <h3>Escalation Reasons</h3>
          <div className="reasons-grid">
            {(data_processed.escalation_reasons || []).map((reason, index) => (
              <div key={index} className="reason-card">
                <div className="reason-name">{reason.reason || 'Unknown'}</div>
                <div className="reason-stats">
                  <span className="reason-count">{reason.count || 0}</span>
                  <span className="reason-percentage">
                    {totalConversations > 0 
                      ? `${Math.round((reason.count / totalConversations) * 100)}%`
                      : '0%'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Escalation Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data_processed.escalation_trends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#ef4444" name="Escalations" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Escalation Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={(data_processed.escalation_reasons || []).map(r => ({ name: r.reason, value: r.count }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  nameKey="name"
                  label={({name, value}) => `${name}: ${value}`}
                >
                  {(data_processed.escalation_reasons || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#dc2626', '#f97316', '#fbbf24', '#3b82f6'][index % 4]} />
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
    console.error(`Error rendering escalations tab:`, err)
    return (
      <div className="analytics-error">
        <h3>Error displaying escalations data</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


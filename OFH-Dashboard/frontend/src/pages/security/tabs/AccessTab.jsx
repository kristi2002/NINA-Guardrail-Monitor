/**
 * Security Access Control Tab Component
 */
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function AccessTab({ data, loading, renderMetricCard, securityDataRaw }) {
  const hasValidData = securityDataRaw && Object.keys(securityDataRaw).length > 0
  if (!data || !hasValidData) {
    return (
      <div className="security-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  try {
    const { access_data, access_summary, user_patterns } = data

    return (
      <div className="security-tab">
        <div className="metrics-grid metrics-grid--wrap">
          {renderMetricCard('Success Rate', `${access_summary.success_rate}%`, 'Authentication success', '✅')}
          {renderMetricCard('Failed Attempts', access_summary.failed_attempts, 'Failed logins', '❌')}
          {renderMetricCard('MFA Adoption', `${access_summary.mfa_adoption_rate}%`, 'Multi-factor auth', '🔐')}
          {renderMetricCard('Suspicious Activity', access_summary.suspicious_activities, 'Detected activities', '👁️')}
          {renderMetricCard('Admin Activity', access_summary.admin_activity_recent || 0, 'Admin logins this period', '👩‍💼')}
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
                <Area type="monotone" dataKey="admin_activity" stackId="2" stroke="#6366f1" fill="#6366f1" fillOpacity={0.35} name="Admin Activity" />
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
    console.error(`Error rendering access tab:`, err)
    return (
      <div className="security-error">
        <h3>Error rendering access tab</h3>
        <p>Error: {err.message}</p>
      </div>
    )
  }
}


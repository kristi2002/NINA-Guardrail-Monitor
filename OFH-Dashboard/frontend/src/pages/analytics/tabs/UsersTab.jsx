/**
 * Users (Admin Performance) Tab Component
 */
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function UsersTab({ data, loading, renderMetricCard }) {
  if (!data) {
    return (
      <div className="analytics-tab-skeleton">
        <div className="skeleton-team-metrics"></div>
        <div className="skeleton-leaderboard"></div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  if (Object.keys(data).length === 0) {
    return <div className="analytics-loading">No admin performance data available. Try refreshing.</div>
  }

  try {
    const data_processed = data.data || data
    const summary = data_processed.summary || {}
    const distributions = data_processed.distributions || {}
    const performanceMetrics = data_processed.performance_metrics || {}
    const roleDistribution = distributions.by_role || {}

    return (
      <div className="analytics-tab">
        <div className="team-metrics">
          <div className="team-summary">
            <h3>👥 Admin Performance Summary</h3>
            <div className="team-stats">
              <div className="team-stat">
                <span className="stat-label">Total Admins</span>
                <span className="stat-value">{summary.total_users || 0}</span>
              </div>
              <div className="team-stat">
                <span className="stat-label">Active Admins</span>
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

        {Object.keys(roleDistribution).length > 0 && (
          <div className="role-distribution">
            <h3>📊 Admin Role Distribution</h3>
            <div className="role-grid">
              {Object.entries(roleDistribution).map(([role, count]) => (
                <div key={role} className="role-card">
                  <div className="role-name">{role.charAt(0).toUpperCase() + role.slice(1)}</div>
                  <div className="role-count">{count}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Admin Activity Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data_processed.recent_activity || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="active_users" stroke="#3b82f6" name="Active Admins" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {Object.keys(roleDistribution).length > 0 ? (
            <div className="chart-container">
              <h3>Admin Role Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(roleDistribution).map(([role, count]) => ({ name: role.charAt(0).toUpperCase() + role.slice(1), value: count }))}
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
          ) : (
            <div className="chart-container">
              <h3>Admin Login Frequency</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data_processed.recent_activity || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="login_frequency" stroke="#22c55e" name="Login Frequency" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering users tab:`, err)
    return (
      <div className="analytics-error">
        <h3>Error displaying admin performance data</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


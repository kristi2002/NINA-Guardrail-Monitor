/**
 * Notifications Tab Component
 */
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import MetricCard from './MetricCard'

export default function NotificationsTab({ data, loading, renderMetricCard }) {
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
      </div>
    )
  }

  if (Object.keys(data).length === 0) {
    return <div className="analytics-loading">No notifications data available. Try refreshing.</div>
  }

  try {
    const totalNotifications = data.total_notifications || 0
    const byStatus = data.by_status || {}
    const sentCount = byStatus.sent || 0
    const pendingCount = byStatus.pending || 0
    const deliveryRate = totalNotifications > 0 
      ? Math.round((sentCount / totalNotifications) * 100) 
      : 0

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
            <h3>Notification Breakdown by Type</h3>
            <div className="recent-conversations">
              {(data.notification_breakdown || []).slice(0, 10).map((item, index) => (
                <div key={index} className="conversation-item">
                  <div className="conv-id">{item.type || 'Unknown'}</div>
                  <div className="conv-risk">Count: {item.count || 0}</div>
                  <div className="conv-status">Status: {item.status || 'N/A'}</div>
                </div>
              ))}
              {(!data.notification_breakdown || data.notification_breakdown.length === 0) && (
                <div className="no-data">No notification breakdown data available</div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering notifications tab:`, err)
    return (
      <div className="analytics-error">
        <h3>Error displaying notifications data</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


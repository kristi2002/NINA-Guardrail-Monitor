/**
 * Notifications Tab Component
 */
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useTranslation } from 'react-i18next'
import MetricCard from './MetricCard'

export default function NotificationsTab({ data, loading, renderMetricCard }) {
  const { t } = useTranslation()

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
    return <div className="analytics-loading">{t('analytics.tabs.notifications.messages.noData')}</div>
  }

  try {
    const totalNotifications = data.total_notifications || 0
    const byStatus = data.by_status || {}
    const sentCount = byStatus.sent || 0
    const pendingCount = byStatus.pending || 0
    const deliveryRate = totalNotifications > 0 
      ? Math.round((sentCount / totalNotifications) * 100) 
      : 0

    const metrics = [
      {
        title: t('analytics.tabs.notifications.metrics.deliveryRate.title'),
        subtitle: t('analytics.tabs.notifications.metrics.deliveryRate.subtitle'),
        value: `${deliveryRate}%`,
        icon: '📧'
      },
      {
        title: t('analytics.tabs.notifications.metrics.totalSent.title'),
        subtitle: t('analytics.tabs.notifications.metrics.totalSent.subtitle'),
        value: sentCount,
        icon: '📤'
      },
      {
        title: t('analytics.tabs.notifications.metrics.pending.title'),
        subtitle: t('analytics.tabs.notifications.metrics.pending.subtitle'),
        value: pendingCount,
        icon: '⏳'
      },
      {
        title: t('analytics.tabs.notifications.metrics.totalNotifications.title'),
        subtitle: t('analytics.tabs.notifications.metrics.totalNotifications.subtitle'),
        value: totalNotifications,
        icon: '📊'
      }
    ]

    return (
      <div className="analytics-tab">
        <div className="metrics-grid">
          {metrics.map(metric =>
            renderMetricCard(metric.title, metric.value, metric.subtitle, metric.icon)
          )}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>{t('analytics.tabs.notifications.charts.trends.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.trends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  name={t('analytics.tabs.notifications.charts.trends.series.notifications')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>{t('analytics.tabs.notifications.charts.breakdown.title')}</h3>
            <div className="recent-conversations">
              {(data.notification_breakdown || []).slice(0, 10).map((item, index) => (
                <div key={index} className="conversation-item">
                  <div className="conv-id">{item.type || t('analytics.tabs.notifications.labels.unknown')}</div>
                  <div className="conv-risk">
                    {t('analytics.tabs.notifications.labels.count', { count: item.count || 0 })}
                  </div>
                  <div className="conv-status">
                    {t('analytics.tabs.notifications.labels.status', {
                      status: item.status || t('analytics.tabs.notifications.labels.na')
                    })}
                  </div>
                </div>
              ))}
              {(!data.notification_breakdown || data.notification_breakdown.length === 0) && (
                <div className="no-data">
                  {t('analytics.tabs.notifications.charts.breakdown.noData')}
                </div>
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
        <h3>{t('analytics.tabs.notifications.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


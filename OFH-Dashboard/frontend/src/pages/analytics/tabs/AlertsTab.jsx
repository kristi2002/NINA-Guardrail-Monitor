/**
 * Alert Trends Tab Component
 */
import { LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useTranslation } from 'react-i18next'

export default function AlertsTab({ data, loading, renderMetricCard }) {
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
        <div className="skeleton-severity"></div>
      </div>
    )
  }

  if (Object.keys(data).length === 0) {
    return <div className="analytics-loading">{t('analytics.tabs.alerts.messages.noData')}</div>
  }

  try {
    const data_processed = data.data || data
    const summary = data_processed.summary || {}
    const distributions = data_processed.distributions || {}
    const performanceMetrics = data_processed.performance_metrics || {}
    
    // Calculate most common event type from distributions
    const eventTypes = distributions.by_event_type || {}
    const mostCommonType = Object.keys(eventTypes).reduce((a, b) => eventTypes[a] > eventTypes[b] ? a : b, 'N/A') || 'N/A'

    const metrics = [
      {
        title: t('analytics.tabs.alerts.metrics.total.title'),
        subtitle: t('analytics.tabs.alerts.metrics.total.subtitle'),
        value: summary.total_alerts || 0,
        icon: '🚨'
      },
      {
        title: t('analytics.tabs.alerts.metrics.critical.title'),
        subtitle: t('analytics.tabs.alerts.metrics.critical.subtitle'),
        value: summary.critical_alerts || 0,
        icon: '⚠️'
      },
      {
        title: t('analytics.tabs.alerts.metrics.active.title'),
        subtitle: t('analytics.tabs.alerts.metrics.active.subtitle'),
        value: summary.active_alerts || 0,
        icon: '📊'
      },
      {
        title: t('analytics.tabs.alerts.metrics.commonType.title'),
        subtitle: t('analytics.tabs.alerts.metrics.commonType.subtitle'),
        value: mostCommonType,
        icon: '📈'
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
            <h3>{t('analytics.tabs.alerts.charts.trends.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceMetrics.resolution_time_trends || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="average_resolution_time_minutes"
                  stroke="#dc2626"
                  name={t('analytics.tabs.alerts.charts.trends.series.avgResolution')}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  name={t('analytics.tabs.alerts.charts.trends.series.count')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>{t('analytics.tabs.alerts.charts.typeDistribution.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(eventTypes).map(([type, count]) => ({
                    type: t(`analytics.tabs.alerts.eventTypes.${type.toLowerCase?.() || String(type).toLowerCase()}`, {
                      defaultValue: type
                    }),
                    count
                  }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="count"
                  nameKey="type"
                  label={({type, count}) => t('analytics.tabs.alerts.charts.typeDistribution.label', { type, count })}
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
          <h3>{t('analytics.tabs.alerts.severity.title')}</h3>
          <div className="severity-bars">
            {Object.entries(distributions.by_severity || {}).map(([severity, count], index) => {
              const colors = { 'CRITICAL': '#dc2626', 'critical': '#dc2626', 'HIGH': '#f97316', 'high': '#f97316', 'MEDIUM': '#fbbf24', 'medium': '#fbbf24', 'LOW': '#22c55e', 'low': '#22c55e' }
              const maxCount = Math.max(...Object.values(distributions.by_severity || {}))
              const severityKey = typeof severity === 'string' ? severity.toLowerCase() : String(severity).toLowerCase()
              return (
                <div key={index} className="severity-bar">
                  <div className="severity-label" style={{ color: colors[severity] || colors[severityKey] || '#64748b' }}>
                    {t(`analytics.tabs.alerts.severity.labels.${severityKey}`, { defaultValue: severity })}
                  </div>
                  <div className="severity-progress">
                    <div
                      className="severity-fill"
                      style={{
                        width: `${maxCount > 0 ? (count / maxCount) * 100 : 0}%`,
                        backgroundColor: colors[severity] || colors[severityKey] || '#64748b'
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
        <h3>{t('analytics.tabs.alerts.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


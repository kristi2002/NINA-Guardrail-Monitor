/**
 * Overview Tab Component
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import MetricCard from './MetricCard'

function PerformanceCard({ icon, iconClass, label, value, trend }) {
  return (
    <div className="summary-card">
      <div className={`summary-icon ${iconClass}`}>{icon}</div>
      <div className="summary-body">
        <span className="summary-label">{label}</span>
        <span className="summary-value">{value}</span>
        {trend?.label && (
          <span className={`summary-trend ${trend.type || 'neutral'}`}>
            {trend.label}
          </span>
        )}
      </div>
    </div>
  )
}

export default function OverviewTab({ data, loading, renderMetricCard, timeRange = '7d' }) {
  const { t } = useTranslation()
  const timeRangeLabel = useMemo(() => t(`analytics.tabs.overview.timeRange.${timeRange}`), [t, timeRange])
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

    const metrics = [
      {
        title: t('analytics.tabs.overview.metrics.totalAlerts.title'),
        subtitle: t('analytics.tabs.overview.metrics.totalAlerts.subtitle'),
        value: totalAlerts,
        icon: '🎯'
      },
      {
        title: t('analytics.tabs.overview.metrics.avgResponseTime.title'),
        subtitle: t('analytics.tabs.overview.metrics.avgResponseTime.subtitle'),
        value: avgResponseTimeFormatted,
        icon: '⚡'
      },
      {
        title: t('analytics.tabs.overview.metrics.resolutionRate.title'),
        subtitle: t('analytics.tabs.overview.metrics.resolutionRate.subtitle'),
        value: `${resolutionRate}%`,
        icon: '✅'
      },
      {
        title: t('analytics.tabs.overview.metrics.activeConversations.title'),
        subtitle: t('analytics.tabs.overview.metrics.activeConversations.subtitle'),
        value: activeConversations,
        icon: '💬'
      },
      {
        title: t('analytics.tabs.overview.metrics.highRisk.title'),
        subtitle: t('analytics.tabs.overview.metrics.highRisk.subtitle'),
        value: conversations.high_risk || 0,
        icon: '🚨'
      },
      {
        title: t('analytics.tabs.overview.metrics.escalationRate.title'),
        subtitle: t('analytics.tabs.overview.metrics.escalationRate.subtitle'),
        value: `${Math.round(escalationRate * 100)}%`,
        icon: '⬆️'
      }
    ]

    const performanceCards = [
      {
        icon: '💬',
        iconClass: 'total',
        label: t('analytics.tabs.overview.performance.cards.totalConversations.label'),
        value: totalConversations,
        trend: { type: 'positive', label: t('analytics.tabs.overview.performance.cards.totalConversations.trend') }
      },
      {
        icon: '🧑‍💻',
        iconClass: 'users',
        label: t('analytics.tabs.overview.performance.cards.activeUsers.label'),
        value: users.active || 0,
        trend: { type: 'neutral', label: t('analytics.tabs.overview.performance.cards.activeUsers.trend') }
      },
      {
        icon: '⏱️',
        iconClass: 'duration',
        label: t('analytics.tabs.overview.performance.cards.averageDuration.label'),
        value: `${Math.round(conversations.average_duration || 0)}m`,
        trend: { type: 'negative', label: t('analytics.tabs.overview.performance.cards.averageDuration.trend') }
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
          <div className="alert-summary">
            <h3>{t('analytics.tabs.overview.charts.alertDistribution.title')}</h3>
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
              <div className="chart-placeholder">
                {t('analytics.tabs.overview.charts.alertDistribution.noData')}
              </div>
            )}
          </div>

          <div className="performance-summary">
            <div className="summary-header">
              <div>
                <h3>{t('analytics.tabs.overview.performance.title')}</h3>
                <p className="summary-subtitle">
                  {t('analytics.tabs.overview.performance.subtitle', { timeRange: timeRangeLabel })}
                </p>
              </div>
              <div className="summary-badge">
                <span className="trend-icon">↗</span>
                <span>{t('analytics.tabs.overview.performance.badge')}</span>
              </div>
            </div>
            <div className="summary-grid">
              {performanceCards.map(card => (
                <PerformanceCard key={card.label} {...card} />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering overview tab:`, err)
    return (
      <div className="analytics-error">
        <h3>{t('analytics.tabs.overview.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


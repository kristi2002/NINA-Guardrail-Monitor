/**
 * Dashboard Metrics Section Component
 */
import { MetricCard, MetricCardSkeleton } from '../../../components/analytics'
import { calculateTrend } from '../../../utils/trendCalculator'
import { useTranslation } from 'react-i18next'


export default function DashboardMetrics({ metrics, previousMetrics }) {
  const { t } = useTranslation()
  const activeConversations = metrics?.conversation_metrics?.active_sessions || 0
  const criticalAlerts = metrics?.alert_metrics?.critical_alerts || 0
  const totalConversations = metrics?.conversation_metrics?.total_sessions || 0
  const averageDuration = metrics?.conversation_metrics?.average_session_duration || 0
  const durationLabel = averageDuration
    ? t('dashboard.metrics.durationValue', { minutes: Math.round(averageDuration) })
    : t('dashboard.metrics.noData')

  if (!metrics) {
    return (
      <div className="metrics-grid">
        <MetricCardSkeleton />
        <MetricCardSkeleton />
        <MetricCardSkeleton />
        <MetricCardSkeleton />
      </div>
    )
  }

  return (
    <div className="metrics-grid">
      <MetricCard 
        title={t('dashboard.metrics.activeConversations')}
        value={activeConversations}
        icon="💬"
        trend={previousMetrics ? calculateTrend(
          activeConversations,
          previousMetrics.conversation_metrics?.active_sessions || 0
        ) : undefined}
      />
      <MetricCard 
        title={t('dashboard.metrics.criticalAlerts')}
        value={criticalAlerts}
        icon="🚨"
        trend={previousMetrics ? calculateTrend(
          criticalAlerts,
          previousMetrics.alert_metrics?.critical_alerts || 0
        ) : undefined}
        isAlert={true}
      />
      <MetricCard 
        title={t('dashboard.metrics.totalConversations')}
        value={totalConversations}
        icon="📅"
        trend={previousMetrics ? calculateTrend(
          totalConversations,
          previousMetrics.conversation_metrics?.total_sessions || 0
        ) : undefined}
      />
      <MetricCard 
        title={t('dashboard.metrics.averageDuration')}
        value={durationLabel}
        icon="⏱️"
        trend={previousMetrics ? calculateTrend(
          averageDuration,
          previousMetrics.conversation_metrics?.average_session_duration || 0
        ) : undefined}
      />
    </div>
  )
}


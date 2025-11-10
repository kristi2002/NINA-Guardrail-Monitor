/**
 * Security Access Control Tab Component
 */
import { useTranslation } from 'react-i18next'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function AccessTab({ data, loading, renderMetricCard, securityDataRaw }) {
  const { t } = useTranslation()
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
          {renderMetricCard(
            t('security.tabs.access.metrics.successRate.title'),
            `${access_summary.success_rate}%`,
            t('security.tabs.access.metrics.successRate.subtitle'),
            '✅'
          )}
          {renderMetricCard(
            t('security.tabs.access.metrics.failedAttempts.title'),
            access_summary.failed_attempts,
            t('security.tabs.access.metrics.failedAttempts.subtitle'),
            '❌'
          )}
          {renderMetricCard(
            t('security.tabs.access.metrics.mfaAdoption.title'),
            `${access_summary.mfa_adoption_rate}%`,
            t('security.tabs.access.metrics.mfaAdoption.subtitle'),
            '🔐'
          )}
          {renderMetricCard(
            t('security.tabs.access.metrics.suspiciousActivity.title'),
            access_summary.suspicious_activities,
            t('security.tabs.access.metrics.suspiciousActivity.subtitle'),
            '👁️'
          )}
          {renderMetricCard(
            t('security.tabs.access.metrics.adminActivity.title'),
            access_summary.admin_activity_recent || 0,
            t('security.tabs.access.metrics.adminActivity.subtitle'),
            '👩‍💼'
          )}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>{t('security.tabs.access.charts.authTrends.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={access_data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="successful_logins"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  name={t('security.tabs.access.charts.authTrends.series.successful')}
                />
                <Area
                  type="monotone"
                  dataKey="failed_logins"
                  stackId="1"
                  stroke="#ef4444"
                  fill="#ef4444"
                  name={t('security.tabs.access.charts.authTrends.series.failed')}
                />
                <Area
                  type="monotone"
                  dataKey="admin_activity"
                  stackId="2"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.35}
                  name={t('security.tabs.access.charts.authTrends.series.admin')}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>{t('security.tabs.access.charts.userPatterns.title')}</h3>
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
        <h3>{t('security.tabs.access.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


/**
 * Security Threats Tab Component
 */
import { useTranslation } from 'react-i18next'
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function ThreatsTab({ data, loading, renderMetricCard, securityDataRaw }) {
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
    const { threat_data, threat_summary, threat_analysis } = data

    return (
      <div className="security-tab">
        <div className="metrics-grid">
          {renderMetricCard(
            t('security.tabs.threats.metrics.total.title'),
            threat_summary.total_threats,
            t('security.tabs.threats.metrics.total.subtitle'),
            '⚠️'
          )}
          {renderMetricCard(
            t('security.tabs.threats.metrics.blocked.title'),
            threat_summary.threats_blocked,
            t('security.tabs.threats.metrics.blocked.subtitle'),
            '🛡️'
          )}
          {renderMetricCard(
            t('security.tabs.threats.metrics.resolutionRate.title'),
            `${Math.round((threat_summary.threats_resolved / Math.max(threat_summary.total_threats, 1)) * 100)}%`,
            t('security.tabs.threats.metrics.resolutionRate.subtitle'),
            '✅'
          )}
          {renderMetricCard(
            t('security.tabs.threats.metrics.avgResponse.title'),
            threat_summary.average_response_time,
            t('security.tabs.threats.metrics.avgResponse.subtitle'),
            '⏱️'
          )}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>{t('security.tabs.threats.charts.trends.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={threat_data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="total_threats"
                  stroke="#ef4444"
                  name={t('security.tabs.threats.charts.trends.series.total')}
                />
                <Line
                  type="monotone"
                  dataKey="malware_detected"
                  stroke="#f59e0b"
                  name={t('security.tabs.threats.charts.trends.series.malware')}
                />
                <Line
                  type="monotone"
                  dataKey="phishing_attempts"
                  stroke="#8b5cf6"
                  name={t('security.tabs.threats.charts.trends.series.phishing')}
                />
                <Line
                  type="monotone"
                  dataKey="brute_force_attempts"
                  stroke="#06b6d4"
                  name={t('security.tabs.threats.charts.trends.series.bruteForce')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>{t('security.tabs.threats.charts.distribution.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={threat_analysis.top_threats}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="count"
                  nameKey="type"
                  label={({type, count}) =>
                    t('security.tabs.threats.charts.distribution.label', { type, count })
                  }
                >
                  {threat_analysis.top_threats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#ef4444', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'][index % 5]} />
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
    console.error(`Error rendering threats tab:`, err)
    return (
      <div className="security-error">
        <h3>{t('security.tabs.threats.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


/**
 * Security Incidents Tab Component
 */
import { useTranslation } from 'react-i18next'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function IncidentsTab({ data, loading, renderMetricCard, securityDataRaw }) {
  const { t } = useTranslation()
  const hasValidData = securityDataRaw && Object.keys(securityDataRaw).length > 0
  if (!data || !hasValidData) {
    return (
      <div className="security-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-incidents-list"></div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  try {
    const { incident_data, incident_summary, recent_incidents } = data

    return (
      <div className="security-tab">
        <div className="metrics-grid">
          {renderMetricCard(
            t('security.tabs.incidents.metrics.total.title'),
            incident_summary.total_incidents,
            t('security.tabs.incidents.metrics.total.subtitle'),
            '🚨'
          )}
          {renderMetricCard(
            t('security.tabs.incidents.metrics.resolved.title'),
            incident_summary.resolved_incidents,
            t('security.tabs.incidents.metrics.resolved.subtitle'),
            '✅'
          )}
          {renderMetricCard(
            t('security.tabs.incidents.metrics.resolutionRate.title'),
            `${incident_summary.resolution_rate}%`,
            t('security.tabs.incidents.metrics.resolutionRate.subtitle'),
            '📊'
          )}
          {renderMetricCard(
            t('security.tabs.incidents.metrics.avgResponse.title'),
            incident_summary.average_response_time,
            t('security.tabs.incidents.metrics.avgResponse.subtitle'),
            '⏱️'
          )}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>{t('security.tabs.incidents.charts.trends.title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={incident_data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="incidents_detected"
                  stroke="#ef4444"
                  name={t('security.tabs.incidents.charts.trends.series.detected')}
                />
                <Line
                  type="monotone"
                  dataKey="incidents_resolved"
                  stroke="#10b981"
                  name={t('security.tabs.incidents.charts.trends.series.resolved')}
                />
                <Line
                  type="monotone"
                  dataKey="incidents_escalated"
                  stroke="#f59e0b"
                  name={t('security.tabs.incidents.charts.trends.series.escalated')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>{t('security.tabs.incidents.charts.recent.title')}</h3>
            <div className="incidents-list">
              {recent_incidents.slice(0, 8).map((incident) => (
                <div key={incident.id} className={`incident-item ${incident.severity.toLowerCase()}`}>
                  <div className="incident-header">
                    <span className="incident-type">{incident.type}</span>
                    <span className={`incident-severity ${incident.severity.toLowerCase()}`}>
                      {incident.severity}
                    </span>
                    <span className={`incident-status ${incident.status.toLowerCase()}`}>
                      {incident.status}
                    </span>
                  </div>
                  <div className="incident-description">{incident.description}</div>
                  <div className="incident-meta">
                    <span>
                      {t('security.tabs.incidents.charts.recent.labels.assigned', {
                        assigned: incident.assigned_to
                      })}
                    </span>
                    {incident.resolution_time && (
                      <span>
                        {t('security.tabs.incidents.charts.recent.labels.resolvedIn', {
                          time: incident.resolution_time
                        })}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering incidents tab:`, err)
    return (
      <div className="security-error">
        <h3>{t('security.tabs.incidents.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


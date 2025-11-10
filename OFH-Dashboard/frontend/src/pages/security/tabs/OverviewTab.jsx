/**
 * Security Overview Tab Component
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function OverviewTab({ data, loading, renderMetricCard, securityDataRaw }) {
  const { t } = useTranslation()

  const hasValidData = !!data && securityDataRaw && Object.keys(securityDataRaw).length > 0

  const metrics = useMemo(() => {
    if (!hasValidData || !data) {
      return []
    }
    const { summary, access_control } = data
    return [
      {
        title: t('security.tabs.overview.metrics.securityScore.title'),
        value: `${summary.security_score}%`,
        subtitle: t('security.tabs.overview.metrics.securityScore.subtitle'),
        icon: '🛡️'
      },
      {
        title: t('security.tabs.overview.metrics.totalThreats.title'),
        value: summary.total_threats,
        subtitle: t('security.tabs.overview.metrics.totalThreats.subtitle'),
        icon: '🚫'
      },
      {
        title: t('security.tabs.overview.metrics.activeSessions.title'),
        value: access_control.active_sessions,
        subtitle: t('security.tabs.overview.metrics.activeSessions.subtitle'),
        icon: '👁️'
      },
      {
        title: t('security.tabs.overview.metrics.resolvedThreats.title'),
        value: summary.resolved_threats,
        subtitle: t('security.tabs.overview.metrics.resolvedThreats.subtitle'),
        icon: '✅'
      }
    ]
  }, [data, hasValidData, t])

  // Show skeleton if no data yet or if data is empty/null
  if (!data || !hasValidData) {
    return (
      <div className="security-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-events-section"></div>
        <div className="skeleton-status-grid"></div>
      </div>
    )
  }

  try {
    const { summary, recent_incidents, threat_distribution, access_control, compliance } = data

    return (
      <div className="security-tab">
        <div className="metrics-grid">
          {metrics.map(metric =>
            renderMetricCard(metric.title, metric.value, metric.subtitle, metric.icon)
          )}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>{t('security.tabs.overview.charts.incidents.title')}</h3>
            {recent_incidents && recent_incidents.length > 0 ? (
              <div className="events-list">
                {recent_incidents.slice(0, 5).map((incident, index) => (
                  <div key={incident.id || index} className={`event-item ${(incident.severity || 'unknown').toLowerCase()}`}>
                    <div className="event-header">
                      <span className="event-type">{incident.type || t('security.tabs.overview.events.unknownType')}</span>
                      <span className={`event-severity ${(incident.severity || 'unknown').toLowerCase()}`}>
                        {incident.severity || t('security.tabs.overview.events.unknownSeverity')}
                      </span>
                    </div>
                    <div className="event-description">
                      {incident.description || t('security.tabs.overview.events.noDescription')}
                    </div>
                    <div className="event-meta">
                      <span>
                        {t('security.tabs.overview.events.time')}:{' '}
                        {incident.timestamp ? new Date(incident.timestamp).toLocaleString() : t('conversationDetail.patient.notAvailable')}
                      </span>
                      <span>
                        {t('security.tabs.overview.events.status')}: {incident.status || t('security.tabs.overview.events.unknownSeverity')}
                      </span>
                      <span>
                        {t('security.tabs.overview.events.id')}: {incident.id || t('conversationDetail.patient.notAvailable')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="chart-placeholder">
                {t('security.tabs.overview.charts.incidents.placeholder')}
              </div>
            )}
          </div>

          <div className="chart-container">
            <h3>{t('security.tabs.overview.charts.distribution.title')}</h3>
            {Object.keys(threat_distribution).length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.entries(threat_distribution).map(([type, count]) => ({ type, count }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-placeholder">
                {t('security.tabs.overview.charts.distribution.placeholder')}
              </div>
            )}
          </div>
        </div>

        <div className="security-status">
          <h3>{t('security.tabs.overview.compliance.title')}</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">{t('security.tabs.overview.compliance.labels.gdpr')}</span>
              <span className={`status-value ${compliance.gdpr_compliance >= 90 ? 'good' : compliance.gdpr_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.gdpr_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">{t('security.tabs.overview.compliance.labels.hipaa')}</span>
              <span className={`status-value ${compliance.hipaa_compliance >= 90 ? 'good' : compliance.hipaa_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.hipaa_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">{t('security.tabs.overview.compliance.labels.pci')}</span>
              <span className={`status-value ${compliance.pci_compliance >= 90 ? 'good' : compliance.pci_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.pci_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">{t('security.tabs.overview.compliance.labels.activeThreats')}</span>
              <span className={`status-value ${summary.active_threats === 0 ? 'good' : summary.active_threats <= 2 ? 'warning' : 'critical'}`}>
                {summary.active_threats}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering overview tab:`, err)
    return (
      <div className="security-error">
        <h3>{t('security.tabs.overview.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


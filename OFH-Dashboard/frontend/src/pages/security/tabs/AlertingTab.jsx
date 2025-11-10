import { useTranslation } from 'react-i18next'

export default function AlertingTab({ data, loading }) {
  const { t } = useTranslation()
  const alertingData = data?.alerting || {}
  const alerts = alertingData.alerts || []
  const warning = alertingData.warning
  const retrievedAt = alertingData.retrieved_at

  if (loading) {
    return <div className="security-loading-indicator">{t('security.tabs.alerting.loading')}</div>
  }

  return (
    <div className="alerting-tab">
      <div className="alerting-summary">
        <span>{t('security.tabs.alerting.summary.latest', { count: alerts.length })}</span>
        {retrievedAt && (
          <span>
            {t('security.tabs.alerting.summary.updated', {
              time: new Date(retrievedAt).toLocaleString()
            })}
          </span>
        )}
      </div>

      {warning && (
        <div className="alerting-warning">
          <strong>{t('security.tabs.alerting.warning.title')}</strong> &mdash; {warning}
        </div>
      )}

      {alerts.length === 0 ? (
        <div className="alerting-empty">
          <h3>{t('security.tabs.alerting.empty.title')}</h3>
          <p>{t('security.tabs.alerting.empty.description')}</p>
        </div>
      ) : (
        <div className="alerting-list">
          {alerts.map((alert) => (
            <div key={alert.id || alert.event_id} className="alerting-card">
              <div className="alerting-header">
                <span className={`severity severity-${alert.severity || 'info'}`}>
                  {(alert.severity || 'info').toUpperCase()}
                </span>
                <span className="alerting-type">{alert.event_type}</span>
              </div>
              <div className="alerting-body">
                <h4>{alert.title || t('security.tabs.alerting.card.fallbackTitle')}</h4>
                <p>{alert.message || t('security.tabs.alerting.card.fallbackMessage')}</p>
              </div>
              <div className="alerting-meta">
                <span>
                  {t('security.tabs.alerting.card.conversation', { id: alert.conversation_id })}
                </span>
                {alert.ingested_at && (
                  <span>{new Date(alert.ingested_at).toLocaleString()}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}



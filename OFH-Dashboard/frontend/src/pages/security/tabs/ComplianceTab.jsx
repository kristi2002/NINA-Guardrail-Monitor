/**
 * Security Compliance Tab Component
 */
import { useTranslation } from 'react-i18next'

export default function ComplianceTab({ data, loading, renderMetricCard, securityDataRaw }) {
  const { t } = useTranslation()
  const hasValidData = securityDataRaw && Object.keys(securityDataRaw).length > 0
  if (!data || !hasValidData) {
    return (
      <div className="security-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-frameworks-grid"></div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  try {
    const { frameworks, security_controls, overall_compliance_score } = data

    return (
      <div className="security-tab">
        <div className="metrics-grid">
          {renderMetricCard(
            t('security.tabs.compliance.metrics.overall.title'),
            `${overall_compliance_score}%`,
            t('security.tabs.compliance.metrics.overall.subtitle'),
            '📊'
          )}
          {renderMetricCard(
            t('security.tabs.compliance.metrics.gdpr.title'),
            `${frameworks.GDPR.score}%`,
            t('security.tabs.compliance.metrics.gdpr.subtitle'),
            '🇪🇺'
          )}
          {renderMetricCard(
            t('security.tabs.compliance.metrics.hipaa.title'),
            `${frameworks.HIPAA.score}%`,
            t('security.tabs.compliance.metrics.hipaa.subtitle'),
            '🏥'
          )}
          {renderMetricCard(
            t('security.tabs.compliance.metrics.soc2.title'),
            `${frameworks.SOC2.score}%`,
            t('security.tabs.compliance.metrics.soc2.subtitle'),
            '🔒'
          )}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>{t('security.tabs.compliance.charts.frameworks.title')}</h3>
            <div className="compliance-frameworks">
              {Object.entries(frameworks).map(([framework, frameworkData]) => (
                <div key={framework} className="framework-card">
                  <div className="framework-header">
                    <h4>{framework}</h4>
                    <span className={`framework-status ${frameworkData.status.toLowerCase()}`}>{frameworkData.status}</span>
                  </div>
                  <div className="framework-score">{frameworkData.score}%</div>
                  <div className="framework-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${frameworkData.score}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="framework-details">
                    <span>
                      {t('security.tabs.compliance.charts.frameworks.requirements', {
                        met: frameworkData.requirements_met,
                        total: frameworkData.total_requirements
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-container">
            <h3>{t('security.tabs.compliance.charts.controls.title')}</h3>
            <div className="controls-grid">
              {Object.entries(security_controls).map(([control, controlData]) => (
                <div key={control} className="control-item">
                  <div className="control-header">
                    <span className="control-name">{control.replace('_', ' ').toUpperCase()}</span>
                    <span className={`control-status ${controlData.status.toLowerCase()}`}>{controlData.status}</span>
                  </div>
                  <div className="control-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${(controlData.implemented / controlData.total) * 100}%` }}
                      ></div>
                    </div>
                    <span className="control-count">
                      {t('security.tabs.compliance.charts.controls.count', {
                        implemented: controlData.implemented,
                        total: controlData.total
                      })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  } catch (err) {
    console.error(`Error rendering compliance tab:`, err)
    return (
      <div className="security-error">
        <h3>{t('security.tabs.compliance.messages.errorTitle')}</h3>
        <p>{err.message}</p>
      </div>
    )
  }
}


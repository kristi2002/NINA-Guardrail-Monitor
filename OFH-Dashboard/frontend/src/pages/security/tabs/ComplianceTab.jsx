/**
 * Security Compliance Tab Component
 */
export default function ComplianceTab({ data, loading, renderMetricCard, securityDataRaw }) {
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
          {renderMetricCard('Overall Score', `${overall_compliance_score}%`, 'Compliance rating', '📊')}
          {renderMetricCard('GDPR Score', `${frameworks.GDPR.score}%`, 'GDPR compliance', '🇪🇺')}
          {renderMetricCard('HIPAA Score', `${frameworks.HIPAA.score}%`, 'HIPAA compliance', '🏥')}
          {renderMetricCard('SOC2 Score', `${frameworks.SOC2.score}%`, 'SOC2 compliance', '🔒')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Compliance Frameworks</h3>
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
                    <span>{frameworkData.requirements_met}/{frameworkData.total_requirements} requirements met</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-container">
            <h3>Security Controls</h3>
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
                    <span className="control-count">{controlData.implemented}/{controlData.total}</span>
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
        <h3>Error rendering compliance tab</h3>
        <p>Error: {err.message}</p>
      </div>
    )
  }
}


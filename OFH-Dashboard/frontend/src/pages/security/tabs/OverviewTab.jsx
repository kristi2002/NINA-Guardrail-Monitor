/**
 * Security Overview Tab Component
 */
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function OverviewTab({ data, loading, renderMetricCard, securityDataRaw }) {
  // Show skeleton if no data yet or if data is empty/null
  const hasValidData = securityDataRaw && Object.keys(securityDataRaw).length > 0
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
          {renderMetricCard('Security Score', `${summary.security_score}%`, 'Overall security rating', '🛡️')}
          {renderMetricCard('Total Threats', summary.total_threats, 'This period', '🚫')}
          {renderMetricCard('Active Sessions', access_control.active_sessions, 'Being monitored', '👁️')}
          {renderMetricCard('Resolved Threats', summary.resolved_threats, 'Successfully resolved', '✅')}
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Recent Security Incidents</h3>
            {recent_incidents && recent_incidents.length > 0 ? (
              <div className="events-list">
                {recent_incidents.slice(0, 5).map((incident, index) => (
                  <div key={incident.id || index} className={`event-item ${(incident.severity || 'unknown').toLowerCase()}`}>
                    <div className="event-header">
                      <span className="event-type">{incident.type || 'Unknown Incident'}</span>
                      <span className={`event-severity ${(incident.severity || 'unknown').toLowerCase()}`}>{incident.severity || 'Unknown'}</span>
                    </div>
                    <div className="event-description">{incident.description || 'No description available'}</div>
                    <div className="event-meta">
                      <span>Time: {incident.timestamp ? new Date(incident.timestamp).toLocaleString() : 'N/A'}</span>
                      <span>Status: {incident.status || 'Unknown'}</span>
                      <span>ID: {incident.id || 'N/A'}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="chart-placeholder">No recent security incidents</div>
            )}
          </div>

          <div className="chart-container">
            <h3>Threat Distribution</h3>
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
              <div className="chart-placeholder">No threat distribution data available</div>
            )}
          </div>
        </div>

        <div className="security-status">
          <h3>Compliance Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">GDPR Compliance</span>
              <span className={`status-value ${compliance.gdpr_compliance >= 90 ? 'good' : compliance.gdpr_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.gdpr_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">HIPAA Compliance</span>
              <span className={`status-value ${compliance.hipaa_compliance >= 90 ? 'good' : compliance.hipaa_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.hipaa_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">PCI Compliance</span>
              <span className={`status-value ${compliance.pci_compliance >= 90 ? 'good' : compliance.pci_compliance >= 70 ? 'warning' : 'critical'}`}>
                {compliance.pci_compliance}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Active Threats</span>
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
        <h3>Error rendering overview tab</h3>
        <p>Error: {err.message}</p>
      </div>
    )
  }
}


/**
 * Simple Metric Card Component for Analytics Tabs
 */
export default function MetricCard({ title, value, subtitle, icon, trend }) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
      {trend !== undefined && (
        <div className={`metric-trend ${trend >= 0 ? 'positive' : 'negative'}`}>
          {trend >= 0 ? '↗️' : '↘️'} {Math.abs(trend)}%
        </div>
      )}
    </div>
  )
}


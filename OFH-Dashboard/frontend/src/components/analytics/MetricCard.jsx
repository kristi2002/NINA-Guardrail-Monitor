import './MetricCard.css'

function resolveTrend(trend) {
  if (trend === undefined || trend === null) {
    return null
  }

  if (typeof trend === 'number') {
    return {
      className: trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral',
      icon: trend > 0 ? '↗' : trend < 0 ? '↘' : '→',
      value: `${Math.abs(trend)}%`,
    }
  }

  if (typeof trend === 'string') {
    return {
      className: 'neutral',
      icon: '→',
      value: trend,
    }
  }

  if (typeof trend === 'object') {
    return {
      className: trend.type || 'neutral',
      icon: trend.icon || (trend.type === 'positive' ? '↗' : trend.type === 'negative' ? '↘' : '→'),
      value: trend.value ?? '',
    }
  }

  return null
}

function MetricCard({ title, value, subtitle, icon, trend, isAlert = false }) {
  const trendData = resolveTrend(trend)

  return (
    <div className={`metric-card ${isAlert ? 'alert' : ''}`}>
      <div className="card-background"></div>
      <div className="card-content">
        <div className="metric-header">
          <div className="header-left">
            <div className="icon-container">
              <span className="metric-icon">{icon}</span>
            </div>
            <h3 className="metric-title">{title}</h3>
          </div>
        </div>
        {isAlert && (
          <div className="alert-indicator">
            <span className="pulse-dot"></span>
            <span className="alert-label">Requires Attention</span>
          </div>
        )}
        
        <div className="metric-value-container">
          <div className="metric-value-group">
            <span className="metric-value">{value}</span>
            {subtitle && <span className="metric-subtitle">{subtitle}</span>}
          </div>
          {trendData && trendData.value && (
            <div className={`metric-trend ${trendData.className}`}>
              <span className="trend-icon">{trendData.icon}</span>
              <span className="trend-value">{trendData.value}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MetricCard


import './MetricCard.css'

function MetricCard({ title, value, icon, trend, isAlert = false }) {
  const trendClass = trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral'
  const trendIcon = trend > 0 ? '↗' : trend < 0 ? '↘' : '→'
  
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
          {isAlert && (
            <div className="alert-indicator">
              <span className="pulse-dot"></span>
              <span>Requires Attention</span>
            </div>
          )}
        </div>
        
        <div className="metric-value-container">
          <span className="metric-value">{value}</span>
          {trend !== undefined && (
            <div className={`metric-trend ${trendClass}`}>
              <span className="trend-icon">{trendIcon}</span>
              <span className="trend-value">{Math.abs(trend)}%</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MetricCard

